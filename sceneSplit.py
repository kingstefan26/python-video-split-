from scenedetect import detect, ContentDetector
import os, sys, subprocess, json, shutil
from tqdm import tqdm
import atexit


DebugMode = True


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

currnetPath = ""

finishedMerge = False


def deleteCUrrentlyencoded():
    if not finishedMerge:
        print('App quiting, deleting currently encoded scene. to resume just rerun the script with the same settings')
        if os.path.exists(currnetPath):
            os.remove(currnetPath)


atexit.register(deleteCUrrentlyencoded)


def mergeVideoFiles(listOfFilePaths, outputfile):
    with open('temp.txt', 'w') as f:
        for name in listOfFilePaths:
            f.write("file '" + name + "'\n")

    vec = ['ffmpeg']
    vec += ['-v', 'error']
    vec += ['-stats']
    vec += ['-f', 'concat']
    vec += ['-i', 'temp.txt']
    vec += ['-safe', '0']
    vec += ['-vsync', 'drop']
    vec += ['-c', 'copy']
    vec += [outputfile]

    subprocess.run(vec)

    if not DebugMode:
        os.remove('temp.txt')


def extractLosslessChunk(start, end, inputpath, outpath):

    command_vec = ['ffmpeg']

    if DebugMode:
        command_vec += ['-v', 'error']
        command_vec.append('-stats')
        command_vec.append('-y')
    else:
        command_vec.append('-n')


    command_vec += ['-i', inputpath]

    command_vec += ['-vf', 'trim=start_frame=' + str(start) + ':end_frame=' + str(end)]

    command_vec += ['-c:v', 'ffv1']

    command_vec += ['-threads', '12']

    command_vec += ['-an', '-sn']

    command_vec += ['-copyts', '-avoid_negative_ts', '1']

    offsetFromStart = (start - 1) / get_video_frame_rate(inputfile)

    command_vec += ['-ss', str(offsetFromStart)]

    command_vec += ['-map_metadata', '-1']

    command_vec += [outpath]

    global currnetPath

    currnetPath = outpath

    if DebugMode:
        subprocess.run(command_vec)
    else:
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


def genformat(format_canon_name):
    outcommandvec = []
    match format_canon_name:
        case '360p':
            outcommandvec += ['-vf', 'scale=-2:360']
            outcommandvec += ['-b:v', '100k']
            outcommandvec += ['-maxrate', '200k']
            outcommandvec += ['-bufsize', '400k']
        case '480p':
            outcommandvec += ['-vf', 'scale=-2:468']
            outcommandvec += ['-b:v', '200k']
            outcommandvec += ['-maxrate', '400k']
            outcommandvec += ['-bufsize', '800k']
        case '720p':
            outcommandvec += ['-vf', 'scale=-2:720']
            outcommandvec += ['-b:v', '250k']
            outcommandvec += ['-maxrate', '1000k']
            outcommandvec += ['-bufsize', '2000k']
        case '1080p':
            outcommandvec += ['-vf', 'scale=-2:1080']
            outcommandvec += ['-b:v', '500k']
            outcommandvec += ['-maxrate', '2000k']
            outcommandvec += ['-bufsize', '4000k']
        case '1080p_crf':
            outcommandvec += ['-vf', 'scale=-2:1080']
            outcommandvec += ['-maxrate', '4000k']
            outcommandvec += ['-crf', '25']
        case 'sourse':
            outcommandvec += ['-maxrate', '6500k']
            outcommandvec += ['-crf', '20']

    return outcommandvec


def encodeVideo(inputpath, outputfilepath, format='1080p', chanellmapping=[],
                ffmpegpath='/home/kokoniara/ffmpeg_sources/ffmpeg/ffmpeg', preset='4'):
    command_vec = [ffmpegpath]

    if DebugMode:
        command_vec += ['-v', 'error']
        command_vec.append('-stats')

    command_vec += ['-i', inputpath]

    command_vec += ['-c:v', 'libsvtav1']

    command_vec += ['-preset', preset]

    command_vec += genformat(format)

    command_vec += ['-vsync', '0']

    command_vec += ['-svtav1-params',
                        'tune=0:enable-overlays=1:scd=0:rc=0:film-grain=14:chroma-u-dc-qindex-offset=-2:chroma-u-ac-qindex-offset=-2:chroma-v-dc-qindex-offset=-2:chroma-v-ac-qindex-offset=-2']

    command_vec += ['-g', '-1']

    command_vec += ['-pix_fmt', 'yuv420p10le']



    if len(chanellmapping) > 0:
        command_vec += chanellmapping

    if os.path.exists(outputfilepath):
        tqdm.write(outputfilepath + ' already exists skipping')
    else:
        command_vec.append(outputfilepath)

        global currnetPath
        currnetPath = outputfilepath

        if DebugMode:
            subprocess.run(command_vec)
        else:
            subprocess.run(command_vec, stdout=open(os.devnull, 'wb'))

        currnetPath = ''


if __name__ == "__main__":
    inputfile = '../Arcane.S01E09.The.Monster.You.Created.1080p.NF.WEB-DL.DDP5.1.H.264-EniaHD.mkv'
    tempfolder = 'temp/'
    sceneCacheFileName = tempfolder + 'sceneCache.json'
    output = 'e09.mkv'

    if os.path.exists(output):
        print('Output %s already exists' % (output))
        exit()

    if not os.path.exists(tempfolder):
        os.mkdir(tempfolder)

    fragments = getVideoSceneList(inputfile, sceneCacheFileName)



    encodedScenes = []

    for i, frag in enumerate(tqdm(fragments, total=len(fragments), desc='Encoding Scenes', unit='scene')):
        sceneStartTimestamp = frag[0]
        sceneEndTimestamp = frag[1]

        encodedScenePath = tempfolder + str(i) + '.mkv'
        if not os.path.exists(encodedScenePath):

            losslessscenepath = tempfolder + 'losslesschnk' + str(i) + '.mkv'
            if not os.path.exists(losslessscenepath):
                extractLosslessChunk(sceneStartTimestamp, sceneEndTimestamp, inputfile, losslessscenepath)

            encodeVideo(inputpath=losslessscenepath, outputfilepath=encodedScenePath, format='360p')
            # if not DebugMode:
            os.remove(losslessscenepath)

            encodedScenes.append(encodedScenePath)

        else:

            encodedScenes.append(encodedScenePath)
            tqdm.write('File ' + encodedScenePath + ' already exists skipping')
            continue

    print('Encoding finished, merging Scenes')

    mergeVideoFiles(encodedScenes, output)

    if not os.path.exists(output):
        print('Failed merge, file %s does not exist try again' % output)
        exit()

    finishedMerge = True

    if not DebugMode:
        shutil.rmtree(tempfolder)
