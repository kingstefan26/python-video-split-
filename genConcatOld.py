import sys
import os

with open("mhmconcat", 'w') as f:
    for i in range(int(sys.argv[1])):
        f.write("file 'temp/" + str(i) + ".webm'\n")

print("ffmpeg -v error -f concat -safe 0 -i mhmconcat -c copy coralineTest.mp4")
