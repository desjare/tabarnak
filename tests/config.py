"""
test configuration
"""
import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

TEST_MEDIA_DIR = os.path.join(TEST_DIR, "media")

TEST_BAT_DIR = os.path.join(TEST_MEDIA_DIR, "BAT")
TEST_BAT_H264_DIR = os.path.join(TEST_BAT_DIR, "h264")
TEST_BAT_VP8_DIR = os.path.join(TEST_BAT_DIR, "vp8")
TEST_BAT_INVALID_DIR = os.path.join(TEST_BAT_DIR, "invalid")

TEST_H264_FILE_2_SECONDS = "H.264-720x480-1-audio-tracks-mono-vorbis-eng-2-seconds.mkv"
TEST_H264_PATH_2_SECONDS = os.path.join(TEST_BAT_H264_DIR,TEST_H264_FILE_2_SECONDS)
