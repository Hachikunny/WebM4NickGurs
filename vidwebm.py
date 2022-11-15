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
parser.add_argument("-s", "--start", metavar="START", help="Start point", default=0.0)
parser.add_argument("-e", "--end", metavar="END", help="End point", default=-1.0)
parser.add_argument("-f", "--frame-accurate", help="Enable frame-accurate seeking (slower)", action='store_true')
parser.add_argument("-r", "--framerate", help="Change the output framerate", type=int)
parser.add_argument("-1", "--single-pass", help="Use single-pass instead of two-pass", action='store_true')
parser.add_argument("-9", "--vp9", help="Use VP9 instead of VP8 (slower)", action='store_true')
parser.add_argument("-10", "--high-depth", help="Use 10-bit depth (slower)", action='store_true')
parser.add_argument("-t", "--threads", metavar="THREADS", help="Specify number of threads to use (default 1)", default=1, type=int)
parser.add_argument("-j", "--subtitles", metavar="SUBTITLES", help="Encode with embedded subtitles at the specified track", type=int, nargs="?", default=argparse.SUPPRESS)
parser.add_argument("-x", "--board", metavar="BOARD", help="Automatically select a filesize limit based on a board name", type=str)
parser.add_argument("-v", "--verbose", help="Enable verbose command-line output", action='store_true')

args = parser.parse_args()

if not shutil.which("mkvextract") and "subtitles" in args:
    print("You are missing some dependencies (mkvtoolnix).", file=sys.stderr)
    sys.exit()

if not os.path.isfile(args.input):
    print("Invalid file.", file=sys.stderr)
    sys.exit()

def timeParse(s):
    time = 0.0
    mult = 1
    while len(s) > 0:
        if s.rfind(":") != -1:
            time += float(s[s.rfind(":") + 1:]) * mult
            s = s[0:s.rfind(":")]
            mult *= 60
        else:
            time += float(s) * mult
            s = ""
    return time

board_sizes = {"3":3, "a":3, "aco":3, "adv":3, "an":3, "b":2, "bant":2, "biz":3, "c":3, "cgl":3, "ck":3, "cm":3, "co":3, "d":3, "diy":3, "e":3, "f":3, "fa":3, "fit":3, "g":3, "gd":3, "gif":4, "h":3, "hc":3, "his":3, "hm":3, "hr":3, "i":3, "ic":3, "int":3, "jp":3, "k":3, "lgbt":3, "lit":3, "m":3, "mlp":3, "mu":3, "n":3, "news":3, "o":3, "out":3, "p":3, "po":3, "pol":3, "pw":3, "qa":3, "qst":3, "r":3, "r9k":3, "s":3, "s4s":3, "sci":3, "soc":3, "sp":3, "t":3, "tg":3, "toy":3, "trash":3, "trv":3, "tv":3, "u":3, "v":3, "vg":3, "vip":3, "vm":3, "vmg":3, "vp":3, "vr":3, "vrpg":3, "vst":3, "vt":3, "w":3, "wg":3, "wsg":6, "wsr":3, "x":3, "xs":3, "y":3}

avid = av.open(args.input)
duration = avid.duration // 1_000_000
avid.close()
size = args.limit * 1024 * 8
if args.board:
    size = board_sizes[args.board.lower()] * 1024 * 8

command = ["ffmpeg", "-y"]

start = timeParse(str(args.start))
if args.end != -1.0:
    end = timeParse(args.end)

if args.frame_accurate:
    command.append("-i")
    command.append(args.input)
    command.append("-ss")
    command.append(str(start))
    if args.end != -1.0:
        command.append("-to")
        command.append(str(end))
else:
    command.append("-ss")
    command.append(str(start))
    command.append("-i")
    command.append(args.input)
    if args.end != -1.0:
        command.append("-to")
        command.append(str((end - start)))
if args.framerate:
    command += (f"-r {str(args.framerate)}".split())

command += ("-map_metadata -1 -map_chapters -1".split())

vf = ""
ext = ""

if "subtitles" in args:
    if args.verbose:
        print(*["mkvinfo", args.input], sep=" ")
        p = subprocess.run(["mkvinfo", args.input], capture_output=True)
        print(p.stdout.decode())
    else:
        p = subprocess.run(["mkvinfo", args.input], capture_output=True)
    t = p.stdout.decode()
    no = args.subtitles
    codec = None
    while len(t) > 0:
        tstart = t.find("| + Track")
        tend = t[tstart+1:].find("| + Track")
        if tend == -1:
            sub = t[tstart:]
            t = ""
        else:
            sub = t[tstart:tstart+1+tend]
            t = t[tstart+1+tend:]
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
            if args.verbose:
                print(*["mkvextract", args.input, "tracks", f"{no}:temporary-script.{ext}"], sep=" ")
                subprocess.run(["mkvextract", args.input, "tracks", f"{no}:temporary-script.{ext}"])
            else:
                subprocess.run(["mkvextract", args.input, "tracks", f"{no}:temporary-script.{ext}"], capture_output=True)
            if args.verbose:
                print(*["mkvmerge", "-i", args.input], sep=" ")
                p = subprocess.run(["mkvmerge", "-i", args.input], capture_output=True)
                print(p.stdout.decode())
            else:
                p = subprocess.run(["mkvmerge", "-i", args.input], capture_output=True)
            mx = 0
            if p.stdout.decode().rfind("Attachment ID ") != -1:
                mx = int(re.search("Attachment ID (\\d+)", p.stdout.decode()[p.stdout.decode().rfind("Attachment ID"):]).group(1))
                if not os.path.isdir("temporary-fonts"):
                    os.mkdir("temporary-fonts")
                tlist = []
                for x in range(mx):
                    tlist.append(str(x+1))
                if args.verbose:
                    print(*(["mkvextract", "attachments", args.input] + tlist), sep=" ")
                    subprocess.run(["mkvextract", "attachments", args.input] + tlist, cwd="temporary-fonts")
                else:
                    subprocess.run(["mkvextract", "attachments", args.input] + tlist, cwd="temporary-fonts", capture_output=True)
            seek = f"ffmpeg -y -i temporary-script.{ext} -ss {str(start)} "
            if args.end != -1:
                seek += f"-to {str(end)} "
            seek += f"temporary-script-seek.{ext}"
            if args.verbose:
                print(seek, sep=" ")
                subprocess.run(seek.split())
            else:
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

command += ("-map 0:v:0".split())

if args.end != -1:
    if args.audio:
        size -= args.bitrate * (end - start)
    bitrate = size / (end - start)
else:
    if args.audio:
        size -= args.bitrate * (duration - start)
    bitrate = size / (duration - start)
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
        if args.output[-5:] == ".webm":
            command.append(args.output)
        else:
            command.append(args.output + ".webm")
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
        if args.output[-5:] == ".webm":
            command.append(args.output)
        else:
            command.append(args.output + ".webm")
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
        if args.output[-5:] == ".webm":
            command.append(args.output)
        else:
            command.append(args.output + ".webm")
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
        if args.output[-5:] == ".webm":
            command.append(args.output)
        else:
            command.append(args.output + ".webm")
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
    
