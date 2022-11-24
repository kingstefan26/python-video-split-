import atexit
import json
import os
import shutil
import subprocess

from scenedetect import detect, ContentDetector
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map

DoubleEncode = True
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
currentlyProcessingPaths = []

finishedMerge = False


def deleteCUrrentlyencoded():
    if not finishedMerge:
        print('App quiting, deleting currently encoded scene. to resume just rerun the script with the same settings')

        for path in currentlyProcessingPaths:
            if os.path.exists(path):
                os.remove(path)


atexit.register(deleteCUrrentlyencoded)


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

    if not DebugMode:
        os.remove('oldtemp.txt')


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

        global currentlyProcessingPaths
        currentlyProcessingPaths.append(outputfilepath)

        if DebugMode:
            subprocess.run(command_vec)
        else:
            subprocess.run(command_vec, stdout=open(os.devnull, 'wb'))

        currentlyProcessingPaths.remove(outputfilepath)


def syscmd(cmd, encoding=''):
    """
    Runs a command on the system, waits for the command to finish, and then
    returns the text output of the command. If the command produces no text
    output, the command's return code will be returned instead.
    """
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         close_fds=True)
    p.wait()
    output = p.stdout.read()
    if len(output) > 1:
        if encoding:
            return output.decode(encoding)
        else:
            return output
    return p.returncode


def extractLosslessChunk(start, end, inputpath, outpath):
    command_vec = ['ffmpeg']

    if DebugMode:
        command_vec += ['-v', 'error']
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

    global currentlyProcessingPaths

    currentlyProcessingPaths.append(outpath)

    if DebugMode:
        subprocess.run(command_vec)
    else:
        subprocess.run(command_vec, stdout=open(os.devnull, 'wb'))

    currentlyProcessingPaths.remove(outpath)

    return outpath


isAnimation = True
isHighMotion = True
encodeForMobile = True


def encodeAomEnc(inpath="", outpath=""):
    # ffmpeg -i "2022-10-09 04-19-30.mkv" -sn -an -vsync 0 -f yuv4mpegpipe - | ~/dev/aom-av1-lavish/aom_build/aomenc - -p 1 --webm -o test7.webm --bit-depth=10 --cpu-used=3 --cq-level=30 --disable-kf --kf-min-dist=12 --kf-max-dist=240 --enable-dnl-denoising=0 --denoise-noise-level=4 --color-primaries=bt709 --transfer-characteristics=bt709 --matrix-coefficients=bt709 --threads=64 --tile-rows=0 --tile-columns=1 --enable-keyframe-filtering=1 --aq-mode=0 --tune-content=psy --tune=omni --enable-qm=1 --lag-in-frames=64 --quant-sharpness=3 --sharpness=3 --luma-bias=1 --deltaq-mode=2 --arnr-maxframes=3 --arnr-strength=1  --quant-b-adapt=1 --loopfilter-sharpness=5
    global currentlyProcessingPaths
    currentlyProcessingPaths.append(outpath)

    # one pass
    # yes = 'ffmpeg -v error -i "' + inpath + '" -strict -1 -f yuv4mpegpipe - | ~/dev/aom-av1-lavish/aom_build/aomenc - -p 1 --ivf -o "' + outpath + '" --bit-depth=10 --cpu-used=3 --cq-level=26 --disable-kf --kf-min-dist=12 --kf-max-dist=240 --enable-dnl-denoising=0 --denoise-noise-level=6 --color-primaries=bt709 --transfer-characteristics=bt709 --matrix-coefficients=bt709 --threads=8 --tile-rows=1 --tile-columns=2 --enable-keyframe-filtering=1 --aq-mode=0 --tune-content=psy --tune=omni --enable-qm=1 --lag-in-frames=64 --quant-sharpness=3 --sharpness=3 --luma-bias=1 --deltaq-mode=2 --arnr-maxframes=3 --arnr-strength=1  --quant-b-adapt=1 --loopfilter-sharpness=5  --enable-fwd-kf=1 --enable-chroma-deltaq=1  --mv-cost-upd-freq=2'
    # syscmd(yes)

    indeeddotcom = 'ffmpeg -v error -i "' + inpath + '" -strict -1 -f yuv4mpegpipe - | ~/dev/aom-av1-lavish/aom_build/aomenc - --ivf -o "' + outpath + '" --cpu-used=4 --passes=2 --pass=1 --end-usage=vbr --target-bitrate=1000 --bit-depth=10 --fpf="' + outpath + '.log" --lag-in-frames=48 --enable-fwd-kf=1 --aq-mode=1 --deltaq-mode=0 --enable-chroma-deltaq=1 --quant-b-adapt=1 --enable-qm=1 --min-q=1 --enable-keyframe-filtering=0 --arnr-strength=1 --arnr-maxframes=4 --sharpness=3 --enable-dnl-denoising=0 –denoise-noise-level=2 --disable-trellis-quant=0 --threads=16 --tune-content=animation'
    indeeddotcom1 = 'ffmpeg -v error -i "' + inpath + '" -strict -1 -f yuv4mpegpipe - | ~/dev/aom-av1-lavish/aom_build/aomenc - --ivf -o "' + outpath + '" --cpu-used=4 --passes=2 --pass=2 --end-usage=vbr --target-bitrate=1000 --bit-depth=10 --fpf="' + outpath + '.log" --lag-in-frames=48 --enable-fwd-kf=1 --aq-mode=1 --deltaq-mode=0 --enable-chroma-deltaq=1 --quant-b-adapt=1 --enable-qm=1 --min-q=1 --enable-keyframe-filtering=0 --arnr-strength=1 --arnr-maxframes=4 --sharpness=3 --enable-dnl-denoising=0 –denoise-noise-level=2 --disable-trellis-quant=0 --threads=16 --tune-content=animation'

    syscmd(indeeddotcom)
    syscmd(indeeddotcom1)

    os.remove(outpath + ".log")

    currentlyProcessingPaths.remove(outpath)


def processSingle(tpl):
    global encodedScenes
    frag, i = tpl

    encodedScenePath = tempfolder + str(i) + ('.ivf' if useAom else '.mkv')

    if os.path.exists(encodedScenePath):
        encodedScenes.append(encodedScenePath)
        return

    losslessscenepath = tempfolder + 'losslesschnk' + str(i) + '.mkv'
    if not os.path.exists(losslessscenepath):
        sceneStartTimestamp = frag[0]
        sceneEndTimestamp = frag[1]
        extractLosslessChunk(sceneStartTimestamp, sceneEndTimestamp, inputfile, losslessscenepath)

    if useAom:
        encodeAomEnc(inpath=losslessscenepath, outpath=encodedScenePath)
    else:
        encodeVideo(inputpath=losslessscenepath, outputfilepath=encodedScenePath, format='360p')

    encodedScenes.append(encodedScenePath)

    os.remove(losslessscenepath)


def processSingleWithoutExtractingLossless(tpl):
    global encodedScenes
    frag, i = tpl

    encodedScenePath = tempfolder + str(i) + ('.ivf' if useAom else '.mkv')

    if os.path.exists(encodedScenePath):
        encodedScenes.append(encodedScenePath)
        return

    sceneStartTimestamp = frag[0]
    sceneEndTimestamp = frag[1]

    offsetFromStart = (sceneStartTimestamp - 1) / get_video_frame_rate(inputfile)

    global currentlyProcessingPaths

    currentlyProcessingPaths.append(encodedScenePath)

    booking_dot_com = 'ffmpeg -v error -i "' + inputfile + '"  -vf trim=start_frame=' + str(
        sceneStartTimestamp) + ':end_frame=' + str(
        sceneEndTimestamp) + ' -an -sn -copyts -avoid_negative_ts 1 -map_metadata -1  -ss ' + str(
        offsetFromStart) + ' -strict -1 -f yuv4mpegpipe - | ~/dev/aom-av1-lavish/aom_build/aomenc - --ivf -o "' + encodedScenePath + '" --cpu-used=4 --passes=2 ' \
                                                                                                                                     '--pass=1' \
                                                                                                                                     ' --end-usage=vbr --target-bitrate=1000 --bit-depth=10 --fpf="' + encodedScenePath + '.log" --lag-in-frames=48 --enable-fwd-kf=1 --aq-mode=1 --deltaq-mode=0 --enable-chroma-deltaq=1 --quant-b-adapt=1 --enable-qm=1 --min-q=1 --enable-keyframe-filtering=0 --arnr-strength=1 --arnr-maxframes=4 --sharpness=3 --enable-dnl-denoising=0 –denoise-noise-level=2 --disable-trellis-quant=0 --threads=16 --tune-content=animation'
    indeeddotcom1 = 'ffmpeg -v error -i "' + inputfile + '"  -vf trim=start_frame=' + str(
        sceneStartTimestamp) + ':end_frame=' + str(
        sceneEndTimestamp) + ' -an -sn -copyts -avoid_negative_ts 1 -map_metadata -1  -ss ' + str(
        offsetFromStart) + ' -strict -1 -f yuv4mpegpipe - | ~/dev/aom-av1-lavish/aom_build/aomenc - --ivf -o "' + encodedScenePath + '" --cpu-used=4 --passes=2 ' \
                                                                                                                                     '--pass=2' \
                                                                                                                                     ' --end-usage=vbr --target-bitrate=1000 --bit-depth=10 --fpf="' + encodedScenePath + '.log" --lag-in-frames=48 --enable-fwd-kf=1 --aq-mode=1 --deltaq-mode=0 --enable-chroma-deltaq=1 --quant-b-adapt=1 --enable-qm=1 --min-q=1 --enable-keyframe-filtering=0 --arnr-strength=1 --arnr-maxframes=4 --sharpness=3 --enable-dnl-denoising=0 –denoise-noise-level=2 --disable-trellis-quant=0 --threads=16 --tune-content=animation'

    syscmd(booking_dot_com)
    syscmd(indeeddotcom1)

    os.remove(encodedScenePath + ".log")

    currentlyProcessingPaths.remove(encodedScenePath)

    encodedScenes.append(encodedScenePath)

    os.remove(losslessscenepath)


useAom = True

if __name__ == "__main__":
    inputfile = '/mnt/sda1/movies/The.Quintessential.Quintuplets.Movie.2022.JAPANESE.1080p.AMZN.WEBRip.DDP5.1.x264-NOGRP/The.Quintessential.Quintuplets.Movie.2022.JAPANESE.1080p.AMZN.WEBRip.DDP5.1.x264-NOGRP.mkv'
    tempfolder = 'temp/'
    sceneCacheFileName = tempfolder + 'sceneCache.json'
    output = 'hentai.mkv'

    if os.path.exists(output):
        print('Output %s already exists' % output)
        finishedMerge = True
        exit()

    if not os.path.exists(tempfolder):
        os.mkdir(tempfolder)

    fragments = getVideoSceneList(inputfile, sceneCacheFileName)

    encodedScenes = []

    if DoubleEncode:
        jobs = []

        for i, frag in enumerate(fragments):
            jobs.append((frag, i))

        r = process_map(processSingle, jobs, max_workers=2, chunksize=1)

    else:
        for i, frag in enumerate(tqdm(fragments, total=len(fragments), desc='Encoding Scenes', unit='scene')):
            sceneStartTimestamp = frag[0]
            sceneEndTimestamp = frag[1]

            encodedScenePath = tempfolder + str(i) + ('.ivf' if useAom else '.mkv')

            if not os.path.exists(encodedScenePath):

                losslessscenepath = tempfolder + 'losslesschnk' + str(i) + '.mkv'
                if not os.path.exists(losslessscenepath):
                    extractLosslessChunk(sceneStartTimestamp, sceneEndTimestamp, inputfile, losslessscenepath)

                if useAom:
                    encodeAomEnc(inpath=losslessscenepath, outpath=encodedScenePath)
                else:
                    encodeVideo(inputpath=losslessscenepath, outputfilepath=encodedScenePath, format='360p')

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
