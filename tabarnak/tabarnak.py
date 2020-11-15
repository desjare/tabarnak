#!/usr/bin/python3
"""
tabarnak - transcode all basically accessible resolutely not all Klingon transcode utility tool
"""
# pylint: disable=line-too-long
# pylint: disable=import-outside-toplevel
# pylint: disable=too-many-locals
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-lines

import argparse
import datetime
import json
import logging
import math
import os
import signal
import sys
import subprocess
import shutil
import yaml

# python 3.7 required due to subprocess
if sys.version_info < (3,7):
    raise Exception("Must be using Python 3.7") # pragma: no cover

#
# ffmpeg & ffprobe commands
#

# ffprobe && ffmpeg
ffprobe_path = shutil.which("ffprobe")
ffmpeg_path = shutil.which("ffmpeg")

# checks
if ffmpeg_path is None:
    raise RuntimeError("ffmpeg not found in path") # pragma: no cover

if ffmpeg_path is None:
    raise RuntimeError("ffmpeg not found path") # pragma: no cover

# probe command
probe_cmd = [ffprobe_path, "-v", "error"]
probe_of = ["-of" , "default=noprint_wrappers=1:nokey=1"]
probe_vstream = ["-select_streams",  "v:0"]

# fetch codec name command
probe_codec_cmd = probe_cmd + probe_vstream + ["-show_entries", "stream=codec_name"] + probe_of

# fetch duration in frames
probe_duration_cmd = probe_cmd + ["-show_entries", "format=duration"] + probe_of

#
# videc & audio codec constants
#

# codec & configurations
VIDEO_CODECS = ["hevc", "h264", "dvvideo", "mpeg4", "msmpeg4v3", "dnxhd", "vp8", "vp9"]


# extensions to ignore
skip_ext = [".srt", ".jpg", ".txt", ".py", ".pyc"]

#
# stats classes
#
class TranscoderFileStats:
    """
    transcoder file stats class
    """

    YAMLTag = u"!TranscoderFileStats"

    def __init__(self, input_file_size:int, output_file_size:int):
        self.input_file_size = input_file_size
        self.output_file_size = output_file_size

    def as_dict(self):
        """
        return object as a dict
        """
        return dict(input_file_size=self.input_file_size,
                    output_file_size=self.output_file_size,
                    save_in_bytes=self.get_save_in_bytes(),
                    save_in_percent=self.get_save_in_percent())

    def get_input_file_size(self) -> int:
        """
        return the input file size in bytes
        """
        return self.input_file_size

    def get_output_file_size(self) -> int:
        """
        return the output file size in bytes
        """
        return self.output_file_size

    def get_save_in_bytes(self) -> float:
        """
        return the saved in bytes
        """
        return self.input_file_size - self.output_file_size

    def get_save_in_percent(self) -> float:
        """
        return the saved space in percent
        """
        return (1. - float(self.output_file_size) / float(self.input_file_size)) * 100.

    @staticmethod
    def to_yaml(dumper, data):
        """
        dump the file to yaml
        """
        return dumper.represent_mapping(data.YAMLTag, data.as_dict())

yaml.add_representer(TranscoderFileStats, TranscoderFileStats.to_yaml, Dumper=yaml.SafeDumper)

class TranscoderStats:
    """
    transcoder Stats class
    """

    YAMLTag = u"!TranscoderStats"

    def __init__(self):
        # define collected stats
        self.total_saved = 0.0

    def increment_total_saved(self, value):
        """
        increment total saved value in bytes
        """
        self.total_saved += value

    def get_total_saved(self):
        """
        fetch total saved bytes
        """
        return self.total_saved

    def as_dict(self):
        """
        return object as a dict
        """
        return dict(total_saved=self.total_saved)

    @staticmethod
    def to_yaml(dumper, data):
        """
        dump the file to yaml
        """
        return dumper.represent_mapping(data.YAMLTag, data.as_dict())

yaml.add_representer(TranscoderStats, TranscoderStats.to_yaml, Dumper=yaml.SafeDumper)

#
# result classes
#
class TrancodeFileResult:
    """
    transcoder file result containing information about outcome
    of transcoding
    """
    YAMLTag = u"!TrancodeFileResult"

    def __init__(self, path):
        self.path = path
        self.transcoder_file_stats : TranscoderFileStats = None
        self.infos: [str]= []
        self.errors: [str] = []
        self.warnings: [str] = []
        self.exceptions: [str] = []
        self.fails_on_tolerance: [str] = []

    def as_dict(self):
        """
        return object as a dict
        """
        return dict(path=self.path,
                    stats=self.transcoder_file_stats,
                    infos=self.infos,
                    warnings=self.warnings,
                    errors=self.errors,
                    exception=self.exceptions,
                    fails_on_tolerance=self.fails_on_tolerance)

    def set_file_stats(self,transcoder_file_stats: TranscoderFileStats):
        """
        set stats for file transcoding
        """
        self.transcoder_file_stats = transcoder_file_stats

    def status(self) -> bool:
        """
        return True if the trancode has been successful
        """
        return len(self.exceptions) == 0 and len(self.fails_on_tolerance) ==0

    def info(self,message:str):
        """
        add an information message
        """
        self.infos.append(message)

    def warning(self, message:str):
        """
        add a warning message
        """
        self.warnings.append(message)

    def error(self, message:str):
        """
        add a warning message
        """
        self.warnings.append(message)

    def exception(self, message:str):
        """
        add a exception message
        """
        self.exceptions.append(message)

    def fail_on_tolerance(self, message:str):
        """
        add a fail on tolerance error
        """
        self.fails_on_tolerance.append(message)

    @staticmethod
    def to_yaml(dumper, data):
        """
        dump the file to yaml
        """
        return dumper.represent_mapping(data.YAMLTag, data.as_dict())

yaml.add_representer(TrancodeFileResult, TrancodeFileResult.to_yaml, Dumper=yaml.SafeDumper)

class TranscoderResults:
    """
    transcoder results class containing informatin about job results
    """
    YAMLTag = u"!TranscoderResults"

    def __init__(self):
        self.infos = []
        self.errors = []
        self.warnings = []
        self.exceptions = []
        self.file_result : TrancodeFileResult = None
        self.file_results :[TrancodeFileResult] = []
        self.stats = TranscoderStats()
        self.start_time = datetime.datetime.now()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, _):
        if exc_type:
            logging.debug("TranscoderResults __exit__ %s:%s", exc_type, exc_value)
            if self.file_result is not None:
                self.file_result.exception("%s:%s" % (exc_type, exc_value))
            else:
                self.exception("%s:%s" % (exc_type, exc_value))
        # do not propagate exception
        return True

    def set_file_result(self, file_result: TrancodeFileResult):
        """
        set current file result
        """
        self.file_result = file_result
        self.file_results.append(file_result)

    def get_transcoder_stats(self) -> TranscoderStats:
        """
        return global transcoder stats
        """
        return self.stats

    def as_dict(self):
        """
        return object as a dict
        """
        return dict(infos=self.infos,
                    warnings=self.warnings,
                    errors=self.errors,
                    exceptions=self.exceptions,
                    file_results=self.file_results,
                    stats=self.stats,
                    status=self.status(),
                    start_time=self.start_time,
                    end_time=datetime.datetime.now(),
                    elapsed_time = str(datetime.datetime.now() - self.start_time))

    def status(self) -> bool:
        """
        return true if there were no problems with jobs
        """
        if len(self.exceptions) > 0:
            return False

        for file_result in self.file_results:
            if file_result.status() is False:
                return False
        return True

    def reset(self):
        """
        reset results to initial state
        """
        self.infos = []
        self.errors = []
        self.warnings = []
        self.exceptions = []
        self.file_result : TrancodeFileResult = None
        self.file_results :[TrancodeFileResult] = []

    def info(self,message:str):
        """
        add an information message in context
        """
        if self.file_result:
            self.file_result.info(message)
        else:
            self.infos.append(message)

    def warning(self, message:str):
        """
        add a warning message in context
        """
        if self.file_result:
            self.file_result.warning(message)
        else:
            self.warnings.append(message)

    def error(self, message:str):
        """
        add a error message in context
        """
        if self.file_result:
            self.file_result.error(message)
        else:
            self.errors.append(message)

    def exception(self, message:str):
        """
        add a exception message
        """
        self.exceptions.append(message)

    def fail_on_tolerance(self, message:str):
        """
        add fail on tolerance error on file result
        """
        if self.file_result:
            self.file_result.fail_on_tolerance(message)

    @staticmethod
    def to_yaml(dumper, data):
        """
        dump the file to yaml
        """
        return dumper.represent_mapping(data.YAMLTag, data.as_dict())

    def print_summary(self, transcoder_args=None):
        """
        print a summary of transcoder operations including infos, warnings and errors
        """
        stdout = sys.stdout
        if transcoder_args:
            stdout = transcoder_args.stdout
        summary = yaml.safe_dump(self)
        print(summary, file=stdout)

yaml.add_representer(TranscoderResults, TranscoderResults.to_yaml, Dumper=yaml.SafeDumper)

# transcoder results
transcoder_results = TranscoderResults()

#
# configuration class
#
DEFAULT_H264_VIDEO_CONFIG = {
    "default_ext": ".mkv",
    "encoder_args" : {
        "-c:v": "libx264",
        "-crf": "30"
    }
}

DEFAULT_HEVC_VIDEO_CONFIG = {
    "default_ext": ".mkv",
    "encoder_args" : {
        "-c:v": "libx265",
        "-crf": "28",
        "-preset": "medium"
    }
}

DEFAULT_AV1_VIDEO_CONFIG = {
    "default_ext": ".mkv",
    "encoder_args" : {
        "-c:v": "libaom-av1",
        "-crf": "30",
        "-b:v": "2000k",
        "-strict": "experimental",
        "-row-mt": "1",
        "-tile-columns": "4",
        "-tile-rows": ""
    }
}

DEFAULT_VP9_VIDEO_CONFIG = {
    "default_ext": ".webm",
    "encoder_args" : {
        "-c:v": "libvpx-vp9",
        "-crf": "30",
        "-b:v": "2000k"
    }
}

class TranscoderConfiguration:
    """
    transcoder configuration
    """
    YAMLTag = "!TranscoderConfiguration"

    def __init__(self, video_configs:dict = None):
        # use default config if none specified
        if video_configs is None:
            self.video_configs = {
                "h264": DEFAULT_H264_VIDEO_CONFIG,
                "hevc" : DEFAULT_HEVC_VIDEO_CONFIG,
                "av1" : DEFAULT_AV1_VIDEO_CONFIG,
                "vp9" : DEFAULT_VP9_VIDEO_CONFIG
            }
        else:
            self.video_configs = video_configs

    def get_container_ext(self, config_name:str) -> str:
        """
        return container extension based on config name
        """
        return self.video_configs.get(config_name).get("default_ext")

    def get_encoder_args(self, config_name:str) -> str:
        """
        return encoder args based on config name
        """
        video_config_encoder_args = self.video_configs.get(config_name).get("encoder_args")
        encoder_args = ""
        for key, value in video_config_encoder_args.items():
            encoder_args += key + " " + value + " "
        return encoder_args

    def as_dict(self):
        """
        return object as a dict
        """
        return dict(video_configs=self.video_configs)

    def from_dict(self, config_dict:dict):
        """
        override config from dict
        """
        self.video_configs = config_dict["video_configs"]

    @staticmethod
    def to_yaml(dumper, data):
        """
        dump the file to yaml
        """
        return dumper.represent_mapping(data.YAMLTag, data.as_dict())

    @staticmethod
    def from_yaml(loader, node):
        """
        build a TranscoderConfiguration from a yml loader and node
        """
        node_map = loader.construct_mapping(node)
        return TranscoderConfiguration(video_configs=node_map["video_configs"])

yaml.add_representer(TranscoderConfiguration, TranscoderConfiguration.to_yaml, Dumper=yaml.SafeDumper)
yaml.add_constructor(TranscoderConfiguration.YAMLTag, TranscoderConfiguration.from_yaml, Loader=yaml.SafeLoader)

class TranscoderEncoderArgs:
    """
    transcoder encoder args
    """
    def __init__(self, args: dict, config: TranscoderConfiguration):
        self.encoder_args = ""
        self.output_video_codec = "hevc"

        if args.map_args is not None:
            self.encoder_args += args.map_args
        elif args.default_map is False:
            self.encoder_args += " -map 0 "

        if args.strip_metadata is True:
            self.encoder_args += " -map_metadata -1 "

        if args.video_config_name is not None:
            self.encoder_args += config.get_encoder_args(args.video_config_name)
            self.output_video_codec = args.video_config_name
        elif args.encoder_args is not None:
            self.encoder_args += args.encoder_args
        else:
            self.encoder_args += config.get_encoder_args(self.output_video_codec)

    def get_output_video_codec(self):
        """
        return output video code name
        """
        return self.output_video_codec

    def get_args(self):
        """
        return encoder ffmpeg encoder args
        """
        return self.encoder_args

class TranscoderInputOutputArgs:
    """
    transcoder configuration
    """
    def __init__(self, args):
        self.input_dir = args.input_dir
        self.output_dir = args.output_dir
        self.output_suffix = args.output_suffix
        self.keep_relative_path = args.keep_relative_path

    def get_input_dir(self) -> str:
        """
        return input directory
        """
        return self.input_dir

    def get_output_dir(self, input_dir:str, root_path:str) -> str:
        """
        return output directory
        """
        if self.keep_relative_path is True:
            rel_path = os.path.relpath(root_path, input_dir)
            output_dir = os.path.join(self.output_dir, rel_path)
            return output_dir
        return self.output_dir

    def get_output_suffix(self) -> str:
        """
        return output suffix
        """
        return self.output_suffix

class TranscoderArgs:
    """
    transcoder arguments and options
    """
    def __init__(self, args, config:TranscoderConfiguration, stdout=sys.stdout, stderr=sys.stderr):
        self.args = args

        self.input_output_args = TranscoderInputOutputArgs(args)
        self.config = config
        self.encoder_args = TranscoderEncoderArgs(args, self.config)

        self.stdout = stdout
        self.stderr = stderr

    def get_input_dir(self) -> str:
        """
        return transcoder input dir
        """
        return self.input_output_args.get_input_dir()

    def get_output_dir(self, input_dir:str, root_path:str) -> str:
        """
        return transcoder output dir
        """
        return self.input_output_args.get_output_dir(input_dir, root_path)

    def get_output_suffix(self) -> str:
        """
        return transcoder output suffix
        """
        return self.input_output_args.get_output_suffix()

    def get_output_video_codec(self):
        """
        return output video codec name from encoder args
        """
        return self.encoder_args.get_output_video_codec()

    def get_container_ext(self):
        """
        return container extension based on transcoder args
        """
        return self.config.get_container_ext(self.get_output_video_codec())

    def get_encoder_args(self):
        """
        fetch encoder arguments for ffmpeg
        """
        return self.encoder_args.get_args()

    def get_diff_tolerance_in_frames(self):
        """
        fetch diff tolerance in frames
        """
        return self.args.duration_diff_tolerance_in_frames

    def get_percent_tolerance(self):
        """
        fetch percent tolerance
        """
        return self.args.percent_tolerance



def setup_logging(args):
    """
    setup logging. Add file & console logging handlers.
    If we are using prometheus setup prometheus logging.
    """

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # setup prometheus if specified
    if args.use_prometheus is True:
        try:
            from prometheus_client import REGISTRY, Counter

            log_entries = Counter(
                'python_logging_messages_total',
                'Count of log entries by logger and level.',
                ['logger', 'level'], registry=REGISTRY)


            class ExportingLogHandler(logging.Handler):
                """A LogHandler that exports logging metrics for Prometheus.io."""
                def emit(self, record):
                    log_entries.labels(record.name, record.levelname).inc()


            def export_stats_on_root_logger():
                """Attaches an ExportingLogHandler to the root logger.
                This should be sufficient to get metrics about all logging in a
                Python application, unless a part of the application defines its
                own logger and sets this logger's `propagate` attribute to
                False. The `propagate` attribute is True by default, which means
                that by default all loggers propagate all their logged messages to
                the root logger.
                """
                logger.addHandler(ExportingLogHandler())


            export_stats_on_root_logger()

        except ImportError as error: # pragma: no cover
            print("Error setting prometheus logging: %s" % (error))
            sys.exit(1)

    # end prometheus

    # create file handler which logs even debug message
    file_handler = logging.FileHandler(args.log_path)
    file_handler.setLevel(logging.DEBUG)
    # set formatter
    file_handler.setFormatter(formatter)
    # add handlers
    logger.addHandler(file_handler)

    # create console handler with a higher log level
    if args.stdout_path is None and args.stderr_path is None:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        # set formatter
        console_handler.setFormatter(formatter)
        # set formatter
        logger.addHandler(console_handler)

def close_logging(args):
    """
    close logging. If prometheus is enabaled, dump the REGISTRY to file
    """
    if args.use_prometheus:
        from prometheus_client import REGISTRY, write_to_textfile
        write_to_textfile('transcode.prom', REGISTRY)

def signal_handler(signal_number, _):
    """
    signal handler for the transcoder
    """
    logging.error("Interupted %d", signal_number)
    transcoder_results.print_summary()

    # SIGUSR1 is used in tests
    if signal_number != signal.SIGUSR1:
        sys.exit(1)

def remove_file(output_file):
    """
    remove a file and ignore exception
    """
    transcoder_results.info("Removing %s" % (output_file))
    try:
        if os.path.exists(output_file):
            os.remove(output_file)
    except IsADirectoryError as error:
        logging.error("Cannot remove %s:%s", output_file, error)


def fetch_codec_name(path):
    """
    return codec name of a media file giving its path
    """
    _, ext = os.path.splitext(path)
    if ext in skip_ext:
        return ""

    check_output_cmd = probe_codec_cmd.copy()
    check_output_cmd += [path]

    results = subprocess.run(check_output_cmd, stdout=subprocess.PIPE, check=False)
    if results.returncode != 0:
        raise RuntimeError("Cannot run ffprobe on %s error: %d" % (path, results.returncode))
    codec = results.stdout.decode('utf-8').replace("\n","")

    if codec == "" or codec not in VIDEO_CODECS:
        transcoder_results.error("Invalid codec \"%s\" for %s" % (codec, path))
        logging.error("Invalid codec \"%s\" for %s", codec, path)
        return ""
    return codec

def fetch_duration_in_frames(path):
    """
    fetch duration in frames (int) of a media file giving its path
    """
    check_output_cmd = probe_duration_cmd.copy()
    check_output_cmd += [path]

    results = subprocess.run(check_output_cmd, stdout=subprocess.PIPE, check=False)
    if results.returncode != 0:
        transcoder_results.error("Cannot run ffprobe on %s error: %d" % (path, results.returncode))
        logging.error("Cannot run ffprobe on %s error: %d", path, results.returncode)
        return 0

    duration = results.stdout.decode('utf-8').replace("\n","")

    frame_duration = 0.0
    try:
        frame_duration = math.ceil(float(duration))
    except ValueError:
        pass

    if int(frame_duration) == 0:
        transcoder_results.error("ffprobe zero duuration for %s" % (path))
        logging.error("ffprobe zero duuration for %s", path)

    return int(frame_duration)

def format_size(num, suffix='B'):
    """
    format num bytes to a readable human format
    """
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix) # pragma: no cover

def format_input_output(transcoder_file_stats: TranscoderFileStats):
    """
    format input and output size and stats for logging
    """
    input_fmt = format_size(transcoder_file_stats.get_input_file_size())
    output_fmt = format_size(transcoder_file_stats.get_output_file_size())
    saved_fmt = format_size(transcoder_file_stats.get_save_in_bytes())
    total_saved_fmt = format_size(transcoder_results.get_transcoder_stats().get_total_saved())

    return "Input Size: %s Output Size: %s Saved: %s %2.2f percent Total %s" % (input_fmt, output_fmt, saved_fmt, transcoder_file_stats.get_save_in_percent(), total_saved_fmt)


def compare_input_output(input_file, output_file, input_codec_name, transcode_args):
    """
    compare an input media file to its output media file and returns a tuple of comparison stats
    """

    input_duration = fetch_duration_in_frames(input_file)
    output_duration = fetch_duration_in_frames(output_file)

    input_name = os.path.basename(input_file)
    output_name = os.path.basename(output_file)

    duration_diff = abs(input_duration - output_duration)
    if duration_diff > transcode_args.get_diff_tolerance_in_frames():
        delta_in_frames = output_duration - input_duration
        transcoder_results.fail_on_tolerance("compare_input_output duration differs input: %s:%d frames output %s:%d frames out duration - in duration:%d frames" % (input_name, input_duration, output_name, output_duration, delta_in_frames))
        logging.error("compare_input_output duration differs input: %s:%d frames output %s:%d frames out duration - in duration:%d frames",
                        input_name, input_duration, output_name, output_duration, delta_in_frames )

    input_file_size = 0
    try:
        input_file_size = os.path.getsize(input_file)
    except FileNotFoundError:
        pass

    output_file_size = 0
    try:
        output_file_size = os.path.getsize(output_file)
    except FileNotFoundError:
        pass

    transcoder_file_stats = TranscoderFileStats(input_file_size, output_file_size)
    transcoder_results.get_transcoder_stats().increment_total_saved(transcoder_file_stats.get_save_in_bytes())

    if transcoder_file_stats.get_save_in_percent() > transcode_args.get_percent_tolerance():
        transcoder_results.fail_on_tolerance("compare_input_output file size percent difference is too high: %2.2f for file %s  Input codec %s" % (transcoder_file_stats.get_save_in_percent(), os.path.basename(output_file), input_codec_name))
        logging.warning("compare_input_output file size percent difference is too high: %2.2f for file %s  Input codec %s",
                        transcoder_file_stats.get_save_in_percent(), os.path.basename(output_file), input_codec_name)

    return transcoder_file_stats

def transcode_file(source_filename, codec_name, transcode_args, output_file):
    """
    transcode a single media file
    """

    # set current file result to transcoder results
    transcoder_file_result = TrancodeFileResult(source_filename)
    transcoder_results.set_file_result(transcoder_file_result)

    with transcoder_results:
        encoder_args =  transcode_args.get_encoder_args().strip().split(" ")
        encoder_args = list(filter(lambda a: a != '', encoder_args))

        cmd = [ffmpeg_path, "-i", source_filename] + encoder_args + [output_file]
        transcoder_results.info("transcode_file running %s" % (cmd))
        logging.info("transcode_file running %s", cmd)

        results = subprocess.run(cmd, capture_output=True, encoding="utf-8", check=False)

        if results.stdout is not None:
            transcode_args.stdout.write(results.stdout)

        if results.stderr is not None:
            transcode_args.stderr.write(results.stderr)

        if results.returncode != 0:
            logging.error("transcode_file error running %s returncode: %d", cmd, results.returncode)
            remove_file(output_file)
            raise RuntimeError("transcode_file error running %s returncode: %d" % (cmd, results.returncode))

        if fetch_duration_in_frames(output_file) == 0:
            logging.error("transcode_file error running %s: zero duration for %s", cmd, output_file)
            remove_file(output_file)
            raise RuntimeError("transcode_file error running %s: zero duration for %s" % (cmd, output_file))

        transcoder_file_stats = compare_input_output(source_filename, output_file, codec_name, transcode_args)
        transcoder_file_result.set_file_stats(transcoder_file_stats)

        job_stats_string = format_input_output(transcoder_file_stats)

        transcoder_results.info("transcode_file job done: %s %s" % (output_file, job_stats_string))
        logging.info("transcode_file job done: %s %s", output_file, job_stats_string)


def transcode(transcode_args, copy_others):
    """
    walk into a directory and transcode all media file to specified parameters
    """
    input_dir = transcode_args.get_input_dir()
    for root, _, files in os.walk(input_dir, topdown=False):
        for name in files:
            # skip hidden files
            if name.startswith("."):
                continue

            source_filename = os.path.join(root,name).replace("./","")
            output_dir = transcode_args.get_output_dir(input_dir, root)

            os.makedirs(output_dir, exist_ok=True)

            codec_name = ""
            with transcoder_results:
                codec_name = fetch_codec_name(source_filename)

            if codec_name in transcode_args.get_output_video_codec():

                logging.debug("Skipping %s codec \"%s\"", name, codec_name)

                if copy_others is True:
                    dest_filename = os.path.join(output_dir, os.path.basename(source_filename))
                    if os.path.exists(dest_filename) is False:
                        logging.info("Copying %s", dest_filename)
                        shutil.copyfile(source_filename, dest_filename)

                continue

            output_filename, _ = os.path.splitext(source_filename)
            output_filename += transcode_args.get_output_suffix() + transcode_args.get_container_ext()

            output_file = os.path.join(output_dir, os.path.basename(output_filename))

            if os.path.exists(output_file) is True:

                transcoder_file_stats = compare_input_output(source_filename,output_file, codec_name, transcode_args)

                logging.info("Skipping %s exists. %s", output_file, format_input_output(transcoder_file_stats))
                continue

            transcode_file(source_filename, codec_name, transcode_args, output_file)


def parse_args(argv):
    """
    parse program arguments
    """
    parser = argparse.ArgumentParser(description="tabarnak.py: transcode utility script")

    # general options
    parser.add_argument("--copy", default=False, dest="copy_others", action="store_true", help="copy hevc source files and other files")

    # configuration
    config_group = parser.add_argument_group('configuration')
    config_group.add_argument("--output-yml-config", default=False, action="store_true", dest="output_yml_config", help="output yml default configuration")
    config_group.add_argument("--output-json-config", default=False, action="store_true", dest="output_json_config", help="output json default configuration")
    config_group.add_argument("--input-yml-config", type=str, default=None, dest="input_yml_config", help="input yml configuration from specified path")
    config_group.add_argument("--input-json-config", type=str, default=None, dest="input_json_config", help="input json configuration from specified path")


    # io
    io_group = parser.add_argument_group('input/output options')

    io_group.add_argument("--input-dir", type=str, default=".", dest="input_dir", help="directory where your media files are found")
    io_group.add_argument("--output-dir", type=str, default=".", dest="output_dir", help="directory where your media files are outputted")
    io_group.add_argument("--keep-relative-path", default=False, action="store_true", dest="keep_relative_path", help="keep relative directory structure")
    io_group.add_argument("--output-suffix", type=str, default="", dest="output_suffix", help="suffix to add to the output file")
    io_group.add_argument("--stdout-path", type=str, default=None, dest="stdout_path", help="redirect stdout to path")
    io_group.add_argument("--stderr-path", type=str, default=None, dest="stderr_path", help="redirect stderr to path")

    # logging
    log_group = parser.add_argument_group('logging options')
    log_group.add_argument("--log-path", type=str, default="tabarnak.log", dest="log_path", help="log path")
    log_group.add_argument("--prometheus-log-path", type=str, default="tabarnak.prom", dest="prometheus_log_path", help="prometheus log path")
    log_group.add_argument("--use-prometheus-logging", default=False, action="store_true", dest="use_prometheus", help="use prometheus for logging")


    stream_group = parser.add_argument_group('stream options')
    stream_group.add_argument("--default-map", default=False, action="store_true", dest="default_map", help="use ffmpeg default mapping instead of mapping all streams which might not be supported by mkv container")
    stream_group.add_argument("--map-args", type=str, default=None, dest="map_args", help="specify ffmpeg map arguments")
    stream_group.add_argument("--strip-metadata", default=False, action="store_true", dest="strip_metadata", help="remove most metadata from the file")

    # error
    error_group = parser.add_argument_group('error options')
    error_group.add_argument("--duration-tolerance", type=int, default=1, dest="duration_diff_tolerance_in_frames", help="duration difference in frames that is tolerated")
    error_group.add_argument("--percent-tolerance", type=int, default=95, dest="percent_tolerance", help="percent difference that is tolerated")

    # encoding
    endoding_group = parser.add_argument_group('encoding options')
    endoding_group.add_argument("--encoder-args", type=str, default=None, dest="encoder_args", help="override default encoder args")

    video_config_group = endoding_group.add_mutually_exclusive_group()
    video_config_group.add_argument("--h264", action="store_const", const="h264", dest="video_config_name", help="specify h264 codec")
    video_config_group.add_argument("--hevc", action="store_const", const="hevc", dest="video_config_name", help="specify hevc codec")
    video_config_group.add_argument("--av1", action="store_const", const="av1", dest="video_config_name", help="specify av1 codec")
    video_config_group.add_argument("--vp9", action="store_const", const="vp9", dest="video_config_name", help="specify vp9 codec")

    if argv is not None:
        def error(message):
            """
            error(message: string)

            Prints a usage message incorporating the message to stderr and
            raise an raise an exception.
            """
            raise ChildProcessError(message)

        # monkey patch parser when running unittests
        parser.error = error

    arguments = parser.parse_args(argv)

    return arguments

def execute(args, cmd_stdout, cmd_stderr):
    """
    execute command with io
    """

    # configuration
    config = TranscoderConfiguration()

    if args.input_json_config is not None:
        with open(args.input_json_config, "r") as json_file:
            config_json = json.loads(json_file.read())
            config.from_dict(config_json)

    if args.input_yml_config is not None:
        with open(args.input_yml_config, "r") as yml_file:
            config = yaml.safe_load(yml_file.read())

    if args.output_yml_config is True:
        yml_config = yaml.safe_dump(config)
        print(yml_config, file=cmd_stdout)
        return

    if args.output_json_config is True:
        json_config = json.dumps(config.as_dict(), sort_keys=True, indent=4)
        print(json_config, file=cmd_stdout)
        return

    # transcode
    transcoder_args = TranscoderArgs(args, config, stdout = cmd_stdout, stderr = cmd_stderr)
    transcode(transcoder_args, args.copy_others)

    transcoder_results.print_summary(transcoder_args)


def main(argv: list = None):
    """
    main function: argv is used for tests
    """
    args = parse_args(argv)

    # reset results
    transcoder_results.reset()

    setup_logging(args)

    # setup signal interupt handler
    signal.signal(signal.SIGINT, signal_handler)

    # create output directory
    if args.output_dir is not None:
        os.makedirs(args.output_dir, exist_ok=True)

    # execute the transcoding tasks
    if args.stdout_path is not None and args.stderr_path is not None:
        with open(args.stdout_path, "w+") as cmd_stdout, open(args.stderr_path, "w+") as cmd_stderr:
            execute(args, cmd_stdout, cmd_stderr)
    else:
        execute(args, sys.stdout, sys.stderr) # pragma: no cover

    logging.info("Finished")
    close_logging(args)

    # exit if we are not running tests
    if transcoder_results.status() is False and argv is None:
        sys.exit(1) # pragma: no cover

    return transcoder_results

if __name__ == "__main__":
    main() # pragma: no cover
