
# WebM4NickGurs

4chan is a picky piece of shit and does not support x264, the most common codec. This program is a small wrapper for ffmpeg and preset with common options neccessary for achieving the most quality out of the file size limit of 4chan.

## Requirements

You need to have ffmpeg installed on your system and resolvable via ```$PATH/%PATH%```. If you want to burn embedded subtitles into your video, you must also have MKVToolNix installed.

On Windows, this can be done via something like:

```setx path "%path%;C:\Program Files\MKVToolNix;C:\%FFMPEG-DIR%"``` (I don't know where you downloaded ffmpeg)

On Linux, just use a package manager. That should work without needing to fuck around with ```$PATH```.

All of the modules used in the program must also be installed on your system. If Python is in a good mood, the following should work to resolve any missing libraries:

```pip install av ```

## Usage

```
vidwebm.py -i INPUT -o OUTPUT [-l LIMIT] [-a] [-b BITRATE] [-s START] [-e END] [-w WIDTH] [-h HEIGHT] [-j [TRACK]] [-f] [-r FRAMERATE] [-t THREADS] [-1] [-9] [-10] [-v]
```

```
-i, --input			Input video
-o, --output			Output video
-l, --limit			Size limit (in MB, default 4MB)
-a, --audio			Enable audio in output video
-b, --bitrate			Output audio bitrate (in kbps, default 96kbps)
-s, --start			Start point (seconds)
-e, --end			End point (seconds)
-w, --width			Width of output video
-h, --height			Height of output video
-j, --subtitles			Encode with embedded subtitles at the (optionally) specified track
-f, --frame-accurate            Enable frame-accurate seeking (slower)
-r, --framerate			Change the output framerate
-t, --threads			Specify number of threads to use (default 1)
-1, --single-pass		Use single-pass instead of two-pass
-9, --vp9			Use VP9 instead of VP8 (slower)
-10, --high-depth		Use 10-bit depth (slower)
-x, --board,                    Automatically select a filesize limit based on a board name
-v, --verbose			Enable verbose command-line output
```
## Related

[Find 4chan boards' filesize limits](https://api.4chan.org/boards.json) (Sizes are given in bytes; divide by 2^20 to get MB)

