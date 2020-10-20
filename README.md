# tabarnak

# Description
This script is used to convert or media file to modern codec such as hevc, vp9 or av1 (experimental). It walks into a directory and probes media files for video that are not encoded with specified codec (default hevc). Than it transcodes them. The idea is to use a more modern codec that has a better quality/bitrate ratio. Resulting files are significantly smaller than original h264, mpeg2, mpeg4 or likely any other formats that they are currently encoded to.

tabarnak.py uses [crf](https://trac.ffmpeg.org/wiki/Encode/H.265) encoding. All channels are copied. The audio is converted by ffmpeg to ogg vorbis by default.

tabarnak.py won't delete or clean up your files. It will skipped files that are already done. Basic sanity check is performed after encoding and it will print a warning if the input and output size does not match.

If you plan to use your media files with a chromecast, be sure the buy **chromecast ultra** since the 3rd generation chromecast does not support hevc.

## Usage

For help:
python3 tabarnak.py -h

## Requirements
* [python3](https://www.python.org/) (tested with python 3.6.9)
* [ffmpeg](https://ffmpeg.org/) in your path

I prepared a tutorial video to learn how to do that on Windows 10:
https://gist.github.com/desjare/adc1514d46bcb38414a5e2a602f6d12d

