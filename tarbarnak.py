#!/usr/bin/python3

import argparse
import logging
import os
import signal
import sys
import subprocess
import shutil

if sys.version_info < (3,8):
	raise Exception("Must be using Python 3")

# ffprobe
ffprobe_path = shutil.which("ffprobe")

probe_codec_command = [ffprobe_path, "-v", "error", "-select_streams",  "v:0", "-show_entries", "stream=codec_name", "-of" , "default=noprint_wrappers=1:nokey=1"]
probe_duration_command = [ffprobe_path, "-v", "error", "-show_entries", "format=duration", "-of" , "default=noprint_wrappers=1:nokey=1"]

# codec & configurations
output_video_codec = "hevc"
video_codecs = ["hevc", "h264", "dvvideo", "mpeg4", "msmpeg4v3", "dnxhd"]

default_container_by_codec = {
	"hevc" : ".mkv",
	"av1" : ".mkv",
	"vp9" : ".webm"
}

default_video_encoder_args_by_codec = {
	"hevc" : " -c:v libx265 -crf 28 ",
	"av1" : " -c:v libaom-av1 -crf 30 -b:v 2000k -strict experimental -row-mt 1 -tile-columns 4 -tile-rows 4 -threads 12",
	"vp9" : " -c:v libvpx-vp9 -crf 30 -b:v 2000k "
}

# extensions to ignore
skip_ext = [".srt", ".jpg", ".txt", ".py", ".pyc"]

# stats
total_saved = 0.0

infos = []
errors = []
warnings = []

use_prometheus = False

def setup_logging(args):
	global use_prometheus

	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)

	# create formatter and add it to the handlers
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

	# setup prometheus if specified
	if args.use_prometheus is True:
		use_prometheus = True
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

		except Exception as error:
			print("Error setting prometheus logging: %s" % (error))
			sys.exit(1)

	# end prometheus 

	# create file handler which logs even debug message
	fh = logging.FileHandler(args.log_path)
	fh.setLevel(logging.DEBUG)

	# create console handler with a higher log level
	ch = logging.StreamHandler()
	ch.setLevel(logging.INFO)

	# set formatter
	fh.setFormatter(formatter)
	ch.setFormatter(formatter)

	logger.addHandler(ch)
	logger.addHandler(fh)

def close_logging():
	if use_prometheus:
		from prometheus_client import REGISTRY, write_to_textfile
		write_to_textfile('transcode.prom', REGISTRY)

def handle_info(info):
	infos.append(info)
	logging.info(info)

def handle_warning(warning):
	warnings.append(warning)
	logging.warning(warning)

def handle_error(error):
	errors.append(error)
	logging.error(error)

def run_command(cmd):
	status = os.system(cmd)
	if(status != 0):
		print("Error: running command: %s" % (cmd, ))
		print("Error: return status: %d" % (status))
		return False
	return True

def remove_file(output_file):
	handle_info("Removing %s" % (output_file))
	try:
		os.remove(output_file)
	except Exception as e:
		handle_error("Cannot remove %s:%s"  % (output_file, e))

def format_size(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)

def format_input_output(input_file_size, output_file_size, saved, saved_percent, total_saved):

	input_fmt = format_size(input_file_size)
	output_fmt = format_size(output_file_size)
	saved_fmt = format_size(saved)
	total_saved_fmt = format_size(total_saved)

	return "Input Size: %s Output Size: %s Saved: %s %2.2f percent Total %s" % (input_fmt, output_fmt, saved_fmt, saved_percent, total_saved_fmt)

def print_summary():
	print("Summary: ")

	print("\n".join(infos))
	print("")

	print("Warnings:")
	print("\n".join(warnings))
	print("")

	print("Errors:")
	print("\n".join(errors))
	print("")

def signal_handler(sig, frame):
	logging.error("Interupted")

	close_logging()
	print_summary()
	
	sys.exit(1)

def fetch_codec_name(path):
	_, ext = os.path.splitext(path)
	if ext in skip_ext:
		return ""

	check_output_command = probe_codec_command.copy()
	check_output_command += [path]

	results = subprocess.run(check_output_command, stdout=subprocess.PIPE)
	if results.returncode != 0:
		handle_error("Cannot run ffprobe on %s error: %d" % (path, results.returncode))
		return ""
	codec = results.stdout.decode('utf-8').replace("\n","")

	if codec == "" or codec not in video_codecs:
		handle_error("Invalid codec \"%s\" for %s" % (codec, path))
		return ""

	return codec

def fetch_duration_in_frames(path):
	_, ext = os.path.splitext(path)
	if ext in skip_ext:
		return ""

	check_output_command = probe_duration_command.copy()
	check_output_command += [path]

	results = subprocess.run(check_output_command, stdout=subprocess.PIPE)
	if results.returncode != 0:
		handle_error("Cannot run ffprobe on %s error: %d" % (path, results.returncode))
		return 0
	duration = results.stdout.decode('utf-8').replace("\n","")

	frame_duration = 0.0
	try:
		frame_duration = float(duration)
	except:
		pass

	if int(frame_duration) == 0:
		handle_error("Zero Duration for %s" % (path))

	return int(frame_duration)

def compare_input_output(input_file, output_file, input_codec_name, duration_diff_tolerance_in_frames, percent_tolerance):
	global errors
	global total_saved

	input_duration = fetch_duration_in_frames(input_file)
	output_duration = fetch_duration_in_frames(output_file)

	input_name = os.path.basename(input_file)
	output_name = os.path.basename(output_file)

	duration_diff = abs(input_duration - output_duration)
	if duration_diff > duration_diff_tolerance_in_frames:
		delta_in_frames = output_duration - input_duration
		handle_error("Duration differs input: %s:%d frames output %s:%d frames out duration - in duration:%d frames" % (input_name, input_duration, output_name, output_duration, delta_in_frames))

	input_file_size = os.path.getsize(input_file)
	output_file_size= os.path.getsize(output_file)
	saved = input_file_size - output_file_size
	saved_percent = (1. - float(output_file_size) / float(input_file_size)) * 100. 
	total_saved += saved

	if saved_percent > percent_tolerance:
		handle_warning("File size percent difference is too high: %2.2f for file %s  Input codec %s" % (saved_percent, os.path.basename(output_file), input_codec_name))

	return (input_file_size, output_file_size, saved, saved_percent, total_saved)

def transcode(input_dir, output_dir, encoder_args, duration_diff_tolerance_in_frames, percent_tolerance, copy_others, verbose):
	global total_saved

	for root, _, files in os.walk(input_dir, topdown=False):
		for name in files:
			source_filename = os.path.join(root,name).replace("./","")

			codec_name = fetch_codec_name(source_filename)
			if codec_name == "" or codec_name == output_video_codec:
				if verbose is True:
					handle_info("Skipping %s codec \"%s\"" % (name, codec_name))

				if copy_others is True:
					dest_filename = os.path.join(output_dir, os.path.basename(source_filename))
					if os.path.exists(dest_filename) is False:
						handle_info("Copying %s" % (dest_filename))
						shutil.copyfile(source_filename, dest_filename)

				continue

			output_filename, ext = os.path.splitext(source_filename)
			output_filename += default_container_by_codec.get(output_video_codec)

			if ext.lower() in skip_ext:
				continue

			output_file = os.path.join(output_dir, os.path.basename(output_filename))

			if os.path.exists(output_file) is True:

				input_file_size, output_file_size, saved, saved_percent, total_saved = compare_input_output(source_filename,output_file, codec_name, duration_diff_tolerance_in_frames, percent_tolerance)

				if verbose is True:
					handle_info("Skipping %s exists. %s" % (output_file, format_input_output(input_file_size, output_file_size, saved, saved_percent, total_saved)))

				continue

			cmd = "ffmpeg -i \"%s\" %s \"%s\"" % (source_filename, encoder_args, output_file)
			handle_info("Running: %s" % (cmd))
			outcome = run_command(cmd)
			if outcome is False:

				handle_error("Error running %s" % (cmd))
				remove_file(output_file)

				continue

			input_file_size, output_file_size, saved, saved_percent, total_saved = compare_input_output(source_filename, output_file, codec_name, duration_diff_tolerance_in_frames, percent_tolerance)

			handle_info("Job Done: %s %s" % (output_file, format_input_output(input_file_size, output_file_size, saved, saved_percent, total_saved)))

parser = argparse.ArgumentParser(description="tabarnak.py: transcode utility script")
parser.add_argument("--input-dir", type=str, default=".", dest="input_dir", help="directory where your media files are found")
parser.add_argument("--output-dir", type=str, default=".", dest="output_dir", help="directory where your media files are outputted")

parser.add_argument("--verbose", default=False, action="store_true", dest="verbose", help="verbose")

# logging
parser.add_argument("--log-path", type=str, default="tabarnak.log", dest="log_path", help="log path")
parser.add_argument("--use-prometheus-logging", default=True, action="store_true", dest="use_prometheus", help="use prometheus for logging")



parser.add_argument("--copy", default=False, dest="copy_others", action="store_true", help="copy hevc source files and other files")
parser.add_argument("--default-map", default=False, action="store_true", dest="default_map", help="use ffmpeg default mapping instead of mapping all streams which might not be supported by mkv container")
parser.add_argument("--map-args", type=str, default=None, dest="map_args", help="specify ffmpeg map arguments")
parser.add_argument("--strip-metadata", default=False, action="store_true", dest="strip_metadata", help="remove most metadata from the file")
parser.add_argument("--duration-tolerance", type=int, default=30, dest="duration_diff_tolerance_in_frames", help="duration difference in frames that is tolerated")
parser.add_argument("--percent-tolerance", type=int, default=95, dest="percent_tolerance", help="percent difference that is tolerated")
parser.add_argument("--encoder-args", type=str, default=None, dest="encoder_args", help="override default encoder args")
parser.add_argument("--hevc", action="store_const", const="hevc", dest="video_codec_name", help="specify hevc codec")
parser.add_argument("--av1", action="store_const", const="av1", dest="video_codec_name", help="specify av1 codec")
parser.add_argument("--vp9", action="store_const", const="vp9", dest="video_codec_name", help="specify vp9 codec")


args = parser.parse_args()

setup_logging(args)

# setup signal interupt handler
signal.signal(signal.SIGINT, signal_handler)

encoder_args = ""

if args.map_args is not None:
	encoder_args += args.map_args
elif args.default_map is False:
	encoder_args += " -map 0 "

if args.strip_metadata is True:
	encoder_args += " -map_metadata -1 "

if args.video_codec_name is not None:
	encoder_args += default_video_encoder_args_by_codec.get(args.video_codec_name)
	output_video_codec = args.video_codec_name
elif args.encoder_args is not None:
	encoder_args += args.encoder_args
else:
	encoder_args += default_video_encoder_args_by_codec.get(output_video_codec)

if args.output_dir is not None:
	os.makedirs(args.output_dir, exist_ok=True)

transcode(args.input_dir, args.output_dir, encoder_args, args.duration_diff_tolerance_in_frames, args.percent_tolerance, args.copy_others, args.verbose)

print_summary()

logging.info("Finished")

close_logging()




