import glob
import subprocess
import sys

# Split tracks downloaded from https://mega.nz/folder/v1QQ0Z4R#sLF_ushOsddbL0PAFS2kuA

def get_tracks(txt, num):
    """
LoQDubious 1:
1. Sneaker Pimps - Half Life
2. Folk & Røvere - Cowboy & Indianer- 4:46
3. Smith & Mighty - Rescue Me PT.II(Feat. L.D.) – 9:22
4. DJ Shadow - Midnight In A Perfect World – 14:04
5. Portishead - Cowboys – 18:49
6. Angelo Badalamenti - The Pink Room – 23:24
7. P.J. Harvey - The Wind – 27:17
8. April Nine - This Nite – 30:57
9. Hooverphonic - Inhaler – 35:24
10. Baxter - Love Again – 40:31
11. Tricky - Overcome – 44:11
12. Esthero with Danny Saber - Song For Holly – 48:38
13. Gary Numan - Dark – 52:43
14. Death In Vegas - Dirge – 57:07
15. VNV Nation - Darkangel - 1:02:43
Bonus 1: DJ Food - Turtle Soup *Removed Due To Copyright Issues*
Bonus 2: Massive Attack - Teardrop (Mad Professor remix) *Removed Due To Copyright Issues*

LoQDubious 2:
1. PJ Harvey - Rebecca
2. Akotcha - So Far So good - 3:00
3. Tricky - Hell Is Round The Corner - 9:05
    """
    ok = False
    tracks = []
    for line in open(txt).readlines():
        if line.strip() == "LoQDubious %d:" % num:
            ok = True
        elif ok:
            if line.strip() == "":
                break
            if "copyright" in line.lower():
                continue
            line = line.strip()
            line = line.replace("–", "-").replace("\u200b", " ")
            #typos.
            if "Here With Me" in line or "David McCallum - The Edge" in line or "Swab - This Sad World" in line:
                continue # not in order. just ignore, too lazy to fix

            try:
                ii, line = line.split(". ", 1)
            except:
                ii, line = line.split(" ", 1)

            if not tracks:
                track = line.strip()
                time = "0:00"
            else:
                track = line
                track, time = track.rsplit("-", 1)
                track = track.strip()
                time = time.strip()
            track = track.replace("/", "_")
            tracks.append((time, track + " (LoQD%d)" % num))

    return tracks

def handle_mp3(f, txt, outdir):
    num = int(f.split(".mp3")[0].split()[1])
    tracks = get_tracks(txt, num)
    for i, (time, track) in enumerate(tracks):
        print(i, track)
        to = []
        if i != len(tracks) - 1:
            to = ["-to", tracks[i+1][0]]
        outfile = outdir + "/" + track + ".mp3"
        try:
            open(outfile)
            print("Already exists.")
        except:
            subprocess.check_output(["ffmpeg", "-i", f, "-vn", "-acodec", "copy",
                "-ss", time] + to + [outfile])


def split_tracks():
    mp3dir = sys.argv[1]
    track_txt = sys.argv[2]
    splitdir = sys.argv[3]
    files = sorted(glob.glob(mp3dir + "/*.mp3"))
    for i, f in enumerate(files):
        print(i, "/", len(files), "-", f)
        handle_mp3(f, track_txt, splitdir)

if __name__ == "__main__":
    split_tracks()

