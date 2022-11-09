#!/usr/bin/python3
# You need to pip install all the shit on the following line if you do not already have it.
import argparse, os.path, os, av, subprocess, re, shutil, sys

# You also need ffmpeg (and also mkvtoolnix if you want to burn subtitles), and it has to be accessible via your $PATH/%PATH%. 
if not shutil.which("ffmpeg"):
    print("You are missing some dependencies (ffmpeg).", file=sys.stderr)
    sys.exit()

parser = argparse.ArgumentParser(description='Convert videos to 4chan compliant webms.', conflict_handler="resolve")
parser.add_argument("-w", "--width", metavar="WIDTH", help="Width of output video", type=int, default=-1)
parser.add_argument("-h", "--height", metavar="HEIGHT", help="Height of output video", type=int, default=-1)
parser.add_argument("-i", "--input", metavar="INPUT", help="Input video.", required=True)
parser.add_argument("-o", "--output", metavar="OUTPUT", help="Output video", required=True)
parser.add_argument("-l", "--limit", metavar="SIZE_LIMIT", help="Size limit (in MB, default 4MB)", default=4.0, type=float)
parser.add_argument("-a", "--audio", help="Enable audio in output video", action='store_true')
parser.add_argument("-b", "--bitrate", metavar="BITRATE", help="Output audio bitrate (in kbps, default 96kbps)", default=96, type=int)
parser.add_argument("-s", "--start", metavar="START", help="Start point", default=0.0, type=float)
parser.add_argument("-e", "--end", metavar="END", help="End point", default=-1.0, type=float)
parser.add_argument("-f", "--frame-accurate", help="Enable frame-accurate seeking (slower)", action='store_true')
parser.add_argument("-r", "--framerate", help="Change the output framerate", type=int)
parser.add_argument("-1", "--single-pass", help="Use single-pass instead of two-pass", action='store_true')
parser.add_argument("-9", "--vp9", help="Use VP9 instead of VP8 (slower)", action='store_true')
parser.add_argument("-10", "--high-depth", help="Use 10-bit depth (slower)", action='store_true')
parser.add_argument("-t", "--threads", metavar="THREADS", help="Specify number of threads to use (default 1)", default=1, type=int)
parser.add_argument("-j", "--subtitles", metavar="SUBTITLES", help="Encode with embedded subtitles at the specified track", type=int, nargs="?", default=argparse.SUPPRESS)
parser.add_argument("-v", "--verbose", help="Enable verbose command-line output", action='store_true')

args = parser.parse_args()

if not shutil.which("mkvextract") and "subtitles" in args:
    print("You are missing some dependencies (mkvtoolnix).", file=sys.stderr)
    sys.exit()

if not os.path.isfile(args.input):
    print("Invalid file.", file=sys.stderr)
    sys.exit()
avid = av.open(args.input)
duration = avid.duration // 1_000_000
avid.close()
size = args.limit * 1024 * 8

command = ["ffmpeg", "-y"]

if args.frame_accurate:
    command.append("-i")
    command.append(args.input)
    command.append("-ss")
    command.append(str(args.start))
    if args.end != -1.0:
        command.append("-to")
        command.append(str(args.end))
else:
    command.append("-ss")
    command.append(str(args.start))
    command.append("-i")
    command.append(args.input)
    if args.end != -1.0:
        command.append("-to")
        command.append(str((args.end - args.start)))
if args.framerate:
    command += (f"-r {str(args.framerate)}".split())

command += ("-map_metadata -1 -map_chapters -1".split())

vf = ""
ext = ""

if "subtitles" in args:
    p = subprocess.run(["mkvinfo", args.input], capture_output=True)
    t = p.stdout.decode()
    no = args.subtitles
    codec = None
    while len(t) > 0:
        start = t.find("| + Track")
        end = t[start+1:].find("| + Track")
        if end == -1:
            sub = t[start:]
            t = ""
        else:
            sub = t[start:start+1+end]
            t = t[start+1+end:]
        if no and int(re.search("track ID for mkvmerge & mkvextract: (\\d+)", sub).group(1)) == no:
            codec = re.search("Codec ID: ([A-Za-z0-9_/]*)", sub).group(1)
            break
        elif sub.find("Track type: subtitles") != -1 and sub.find('"Default track" flag: 0') == -1:
            no = int(re.search("track ID for mkvmerge & mkvextract: (\\d+)", sub).group(1))
            codec = re.search("Codec ID: ([A-Za-z0-9_/]*)", sub).group(1)
            break
        
    if no:
        if codec == "S_HDMV/PGS":
            ext = "sup"
        elif codec == "S_TEXT/ASS":
            ext = "ass"
        elif codec == "S_TEXT/UTF8":
            ext = "srt"
        if len(ext) > 0:
            subprocess.run(["mkvextract", args.input, "tracks", f"{no}:temporary-script.{ext}"], capture_output=True)
            p = subprocess.run(["mkvmerge", "-i", args.input], capture_output=True)
            mx = 0
            if p.stdout.decode().rfind("Attachment ID ") != -1:
                mx = int(re.search("Attachment ID (\\d+)", p.stdout.decode()[p.stdout.decode().rfind("Attachment ID"):]).group(1))
                if not os.path.isdir("temporary-fonts"):
                    os.mkdir("temporary-fonts")
                tlist = []
                for x in range(mx):
                    tlist.append(str(x+1))
                subprocess.run(["mkvextract", "attachments", args.input] + tlist, cwd="temporary-fonts", capture_output=True)
            seek = f"ffmpeg -y -i temporary-script.{ext} -ss {str(args.start)} "
            if args.end != -1:
                seek += f"-to {str(args.end)} "
            seek += f"temporary-script-seek.{ext}"
            subprocess.run(seek.split(), capture_output=True)
            vf += f"{ext}=temporary-script-seek.{ext}:fontsdir=./temporary-fonts/"
        else:
            print("Failed to find embedded subtitles", file=sys.stderr)
    else:
        print("Failed to find embedded subtitles", file=sys.stderr)
        
if args.width != -1 or args.height != -1:
    if len(vf) != 0:
        vf += ","
    vf += (f"scale={str(args.width)}:{str(args.height)}")
    
if len(vf) > 0:
    command.append("-vf")
    command.append(vf)

command.append("-map")
command.append("0:v:0")

if args.end != -1:
    if args.audio:
        size -= args.bitrate * (args.end - args.start)
    bitrate = size / (args.end - args.start)
else:
    if args.audio:
        size -= args.bitrate * (duration - args.start)
    bitrate = size / (duration - args.start)
command += ("-map 0:a:0".split())
command.append("-pix_fmt")
if args.high_depth:
    command.append("yuv420p10le")
else:
    command.append("yuv420p")

if args.vp9:
    command += (f"-c:v libvpx-vp9 -b:v {bitrate}k -lag-in-frames 25 -auto-alt-ref 1 -row-mt 1 -tile-rows 2 -threads {str(args.threads)} -speed 3".split())
    if not args.single_pass:
        command1 = command.copy()
        command1 += (("-pass 1 -an -f null " + "NUL" if os.name == "nt" else "/dev/null").split())
        if args.verbose:
            print(*command1, sep=" ")
            subprocess.run(command1)
        else:
            subprocess.run(command1, capture_output=True)
        command += ("-pass 2".split())
        if args.audio:
            command += (f"-c:a libopus -b:a {args.bitrate}k".split())
        else:
            command.append("-an")
        command.append(args.output)
        if args.verbose:
            print(*command, sep=" ")
            subprocess.run(command)
        else:
            subprocess.run(command, capture_output=True)
    else:
        if args.audio:
            command += (f"-c:a libopus -b:a {args.bitrate}k".split())
        else:
            command.append("-an")
        command.append(args.output)
        if args.verbose:
            print(*command, sep=" ")
            subprocess.run(command)
        else:
            subprocess.run(command, capture_output=True)
    
else:
    command += (f"-c:v libvpx -b:v {bitrate}k -lag-in-frames 25 -auto-alt-ref 1 -threads {str(args.threads)}".split())
    if not args.single_pass:
        command1 = command.copy()
        command1 += (("-pass 1 -an -f null " + "NUL" if os.name == "nt" else "/dev/null").split())
        if args.verbose:
            print(*command1, sep=" ")
            subprocess.run(command1)
        else:
            subprocess.run(command1, capture_output=True)
        command += ("-pass 2".split())
        if args.audio:
            command += (f"-c:a libvorbis -b:a {args.bitrate}k".split())
        else:
            command.append("-an")
        command.append(args.output)
        if args.verbose:
            print(*command, sep=" ")
            subprocess.run(command)
        else:
            subprocess.run(command, capture_output=True)
    else:
        if args.audio:
            command += (f"-c:a libvorbis -b:a {args.bitrate}k".split())
        else:
            command.append("-an")
        command.append(args.output)
        if args.verbose:
            print(*command, sep=" ")
            subprocess.run(command)
        else:
            subprocess.run(command, capture_output=True)
        
if os.path.isdir("temporary-fonts"):
    shutil.rmtree("temporary-fonts", ignore_errors=True)
if os.path.isfile(f"temporary-script.{ext}"):
    os.remove(f"temporary-script.{ext}")
if os.path.isfile(f"temporary-script-seek.{ext}"):
    os.remove(f"temporary-script-seek.{ext}")
if os.path.isfile("ffmpeg2pass-0.log"):
    os.remove("ffmpeg2pass-0.log")
    
