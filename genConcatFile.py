import os
import sys

toEncode = []
for root, dirs, files in os.walk('temp/', topdown=False):
    for name in files:
        if name.find("losslesschnk") != -1:
            toEncode.append(name)

with open("mhmconcat", 'w') as f:
    for i in toEncode:
        f.write(f"file 'temp/{i}'\n")

os.system("ffmpeg -v error -stats -f concat -safe 0 -i mhmconcat -c copy anime.mkv")
