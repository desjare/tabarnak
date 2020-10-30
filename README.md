# tabarnak - transcoder [FFmpeg](https://ffmpeg.org/) based utility tool
![Port au Persil](https://github.com/desjare/tabarnak/blob/main/.www/tabarnak.png?raw=true)

![Build Status](https://travis-ci.com/desjare/tabarnak.svg?branch=main)
![Pylint](https://github.com/desjare/tabarnak/workflows/Pylint/badge.svg)
[![codecov](https://codecov.io/gh/desjare/tabarnak/branch/main/graph/badge.svg?token=OTM2MYLPOM)](undefined)
[![HitCount](http://hits.dwyl.com/desjare/desjare/tabarnak.svg)](http://hits.dwyl.com/desjare/desjare/tabarnak)

# Description
In the Province of Québec tabarnak is a swear derived from the tabernacle but it is an acronym for:

**T**ranscoder **A**ll **B**asically **A**ccessible **R**esolutely **N**ot **A**ll **K**lingon

This script is used to convert video or video/audio media files to modern codecs such as HEVC, VP9 or AV1 (experimental). It walks into a directory and probes media files for video that are not encoded with specified codec (default HEVC). Then it transcodes them. The idea is to use a more modern codec that has a better quality/bitrate ratio. Resulting files are significantly smaller than original h264, mpeg2, mpeg4 or likely any other formats that they are currently encoded to.

tabarnak uses [crf](https://trac.ffmpeg.org/wiki/Encode/H.265) encoding. All channels are copied. The audio is converted by ffmpeg to ogg vorbis by default.

tabarnak won’t delete or clean up your files. It will skip files that are already done. Basic sanity check is performed after encoding and it will print a warning if the input and output size do not match.

If you plan to use your media files with a chrome cast, be sure the buy **chromecast ultra** since the 3rd generation chromecast does not support HEVC.

## Usage

### Install
pip3 install tabarnak-desjare

### Getting help
For help:
tabarnak -h

### Example usage

#### transcode all media files recursively using h264 codec and output them output directory 
tabarnak --input-dir . --output-dir output --h264

## Requirements
* [python3](https://www.python.org/) (tested with python 3.7 and 3.8)
* [ffmpeg](https://ffmpeg.org/) in your path

I prepared a tutorial video to learn how to do that on Windows 10:
https://gist.github.com/desjare/adc1514d46bcb38414a5e2a602f6d12d

