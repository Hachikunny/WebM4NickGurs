
# WebM4NickGurs

4chan is a picky piece of shit and does not support x264, the most common codec. This program is a small wrapper for ffmpeg and common options neccessary for achieving the most quality out of the file size limit of 4chan.

## Requiements

You need to have ffmpeg installed on your system and resolvable via ```$PATH/%PATH%```. If you want to burn embedded subtitles into your video, you must also have MKVToolNix installed.

## Usage

```
vidwebm.py -i INPUT -o OUTPUT [-l LIMIT] [-a] [-b BITRATE] [-s START] [-e END] [-w WIDTH] [-h HEIGHT] [-j [TRACK]] [-f] [-r FRAMERATE] [-t THREADS] [-1] [-9] [-10] [-v]
```

```
-i, --input			Input video.
-o, --output			Output video
-l, --limit			Size limit (in MB, default 4MB)
-a, --audio			Enable audio in output video
-b, --bitrate			Output audio bitrate (in kbps, default 96kbps)
-s, --start			Start point
-e, --end			End point
-w, --width			Width of output video
-h, --height			Height of output video
-j, --subtitles			Encode with embedded subtitles at the (optionally) specified track
-f, --frame-accurate            Enable frame-accurate seeking (slower)
-r, --framerate			Change the output framerate
-t, --threads			Specify number of threads to use (default 1)
-1, --single-pass		Use single-pass instead of two-pass
-9, --vp9			Use VP9 instead of VP8 (slower)
-10, --high-depth		Use 10-bit depth (slower)
-v, --verbose			Enable verbose command-line output
```
## Related

[Find 4chan boards' filesize limits](https://api.4chan.org/boards.json)

