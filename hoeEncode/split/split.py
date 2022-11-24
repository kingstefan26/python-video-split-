from scenedetect import detect, ContentDetector
import os, sys, subprocess, json, shutil
from tqdm import tqdm
import atexit

def get_video_frame_rate(filename):
    result = subprocess.run([
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        "-show_entries",
        "stream=r_frame_rate",
        filename,
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result_string = result.stdout.decode('utf-8').split()[0].split('/')
    fps = float(result_string[0]) / float(result_string[1])
    return fps

def mergeVideoFiles(listOfFilePaths, outputfile):
    with open('oldtemp.txt', 'w') as f:
        for name in listOfFilePaths:
            f.write("file '" + name + "'\n")
    vec = ['ffmpeg']
    vec += ['-v', 'error']
    vec += ['-stats']
    vec += ['-f', 'concat']
    vec += ['-i', 'oldtemp.txt']
    vec += ['-safe', '0']
    vec += ['-vsync', 'drop']
    vec += ['-c', 'copy']
    vec += [outputfile]
    subprocess.run(vec)
    os.remove('oldtemp.txt')

def extractLosslessChunk(start, end, inputpath, outpath):

    command_vec = ['ffmpeg']

    command_vec.append('-n')

    command_vec += ['-i', inputpath]

    command_vec += ['-vf', 'trim=start_frame=' + str(start) + ':end_frame=' + str(end)]

    command_vec += ['-c:v', 'ffv1']

    command_vec += ['-threads', '12']

    command_vec += ['-an', '-sn']

    command_vec += ['-copyts', '-avoid_negative_ts', '1']

    offsetFromStart = (start - 1) / get_video_frame_rate(inputpath)

    command_vec += ['-ss', str(offsetFromStart)]

    command_vec += ['-map_metadata', '-1']

    command_vec += [outpath]

    global currnetPath

    currnetPath = outpath

    subprocess.run(command_vec, stdout=open(os.devnull, 'wb'))

    currnetPath = ''

    return outpath

def getVideoSceneList(filePath, sceneCacheFileName):
    fragemts = []

    if os.path.exists(sceneCacheFileName):
        print('Scene cache exists skipping')
        file = open(sceneCacheFileName, )
        fragemts = json.load(file)
    else:
        print('Creating SceneCache')
        scene_list = detect(filePath, ContentDetector())
        for i, scene in enumerate(scene_list):
            print('Scene %2d: Start %s / Frame %d, End %s / Frame %d' % (
                i + 1,
                scene[0].get_timecode(), scene[0].get_frames(),
                scene[1].get_timecode(), scene[1].get_frames(),))

            fragemts.append([scene[0].get_frames(), scene[1].get_frames()])
            with open(sceneCacheFileName, 'w') as file:
                file.write(json.dumps(fragemts))

    return fragemts