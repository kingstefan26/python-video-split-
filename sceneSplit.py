import atexit
import json
import os
import shutil
import subprocess
import time

from copy import copy

from scenedetect import detect, ContentDetector
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map

from hoeEncode.encode.FfmpegUtil import get_video_frame_rate

MultiProcessEncode = True
DebugMode = True


finishedMerge = False


def deleteCUrrentlyencoded():
    if not finishedMerge:
        print('App quiting, deleting currently encoded scenes. to resume just rerun the script with the same settings')


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


ResolutionCannonName = "720p"


def getQualityPreset():
    match ResolutionCannonName:
        case '360p':
            return '-vf scale=-2:360'
        case '480p':
            return '-vf scale=-2:468'
        case '720p':
            return '-vf scale=-2:720'
        case '1080p':
            return '-vf scale=-2:1080'
    return ''


def encodeSvtAv1(inputpath, outputfilepath, format='1080p', chanellmapping=None,
                 ffmpegpath='/home/kokoniara/ffmpeg_sources/ffmpeg/ffmpeg', preset='4'):
    if chanellmapping is None:
        chanellmapping = []
    command_vec = [ffmpegpath]

    if DebugMode:
        command_vec += ['-v', 'error']
        command_vec.append('-stats')

    command_vec += ['-i', inputpath]

    command_vec += ['-c:v', 'libsvtav1']

    command_vec += ['-preset', preset]

    command_vec += getQualityPreset(format)

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

        if DebugMode:
            subprocess.run(command_vec)
        else:
            subprocess.run(command_vec, stdout=open(os.devnull, 'wb'))


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


def extractLosslessFast(start_time, end_time, inputpath, outpath):
    if os.path.exists(outpath):
        return
    else:
        endThingy = (float(end_time) / framerate)
        startTime = (float(start_time) / framerate)
        duration = (endThingy - startTime)
        yas = f'ffmpeg -v error -nostdin -y -ss {str(startTime)} -i "{inputpath}" -t {str(duration)} -c:v ffv1 -threads 12 -an -sn {outpath}'
        syscmd(yas)



AomLavishPath = "~/dev/aom-av1-lavish/aom_build/aomenc"

# 0=q 1=vbr 2=cq
BitRateDistribution = 2

CqLevel = 26
VbrBitRate = 1000

encodeForMobile = False
isAnime = False
TwoPass = True

# AOM EXCLUSIVE SETTINGS

UseFastLavis = True

UsePhotonNoise = True
GrainSynthTablePath = "/home/kokoniara/dev/VideoSplit/Photon-Noise-Tables-aomenc-repo/1920x1080/1920x1080-SRGB-ISO" \
                      "-Photon/1920x1080-SRGB-ISO400.tbl "
denoiseLevel = 13

MinimumQuantizer = True
MinimumQuantizerLvl = 50  # 0-63



def encodeAomEnc(inpath="", outpath="", start_time="", end_time=""):
    endThingy = (float(end_time) / framerate)
    startTime = (float(start_time) / framerate)
    duration = (endThingy - startTime)
    extractCommand = f'ffmpeg -v error -nostdin -ss {str(startTime)} -i "{inpath}" -t {str(duration)} -an -sn -strict -1 {getQualityPreset()} -f yuv4mpegpipe - '

    print(extractCommand)
    quit()
    # encodeCommand = f'ffmpeg -v error -nostdin -ss {str(startTime)} -i "{inpath}" -t {str(duration)} -an -sn -strict -1 -f yuv4mpegpipe - | {AomLavishPath} - --ivf -o "{outpath}" --cpu-used=4 --tune=lavish_vmaf_rd --bit-depth=10 --lag-in-frames=64 --enable-fwd-kf=1 --disable-kf --aq-mode=1 --deltaq-mode=0 --enable-chroma-deltaq=1 --quant-b-adapt=1 --enable-qm=1 --min-q=1 --enable-keyframe-filtering=1 --arnr-strength=1 --arnr-maxframes=7 --quant-sharpness=3 --vmaf-resize-factor=1 --vmaf-preprocessing=1 --threads=1 --tune-content=psy'
    encodeCommand = extractCommand + f'| {AomLavishPath} - --ivf -o "{outpath}" --cpu-used=3 --bit-depth=10 --threads=2 --disable-kf ' \
                    f'--lag-in-frames=64 ' \
                    f'--enable-fwd-kf=1 ' \
                    f'--kf-min-dist=200 ' \
                    f'--aq-mode=1 ' \
                    f'--deltaq-mode=2 ' \
                    f'--enable-chroma-deltaq=1 ' \
                    f'--quant-b-adapt=1 ' \
                    f'--enable-qm=1 ' \
                    f'--min-q=1 ' \
                    f'--enable-keyframe-filtering=2 ' \
                    f'--tune-content=psy ' \
                    f'--disable-trellis-quant=0 ' \
                    f'--arnr-maxframes=7 ' \
                    f'--arnr-strength=1 ' \
                    f'--vmaf-model-path="vmaf_v0.6.1neg.json" ' \
                    f'--vmaf-resize-factor=1 ' \
                    f'--enable-cdef=1 ' \
                    f'--vmaf-preprocessing=1 ' \
                    # f'--loopfilter-sharpness=1 ' \
                    # f'--quant-sharpness=4 ' \
                    # f'--sharpness=1 ' \
                    # f'--vmaf-model-path="vmaf_v0.6.1neg-nomotion.json" ' \
                    # f'--vmaf-quantization=1 ' \
                    # f'--ssim-rd-mult=150 ' \
                    # f'--vmaf-motion-mult=200 '

    if UseFastLavis:
        # encodeCommand += ' --tune=lavish_fast'
        encodeCommand += ' --tune=vmaf_psy_qp'
    else:
        encodeCommand += ' --tune=lavish_vmaf_rd'

    if BitRateDistribution == 1:
        encodeCommand += f" --end-usage=vbr --target-bitrate={VbrBitRate}"
    elif BitRateDistribution == 2:
        encodeCommand += f" --end-usage=cq --cq-level={CqLevel} --target-bitrate={VbrBitRate} "
    else:
        encodeCommand += f" --end-usage=q --cq-level={CqLevel}"

    if MinimumQuantizer:
        encodeCommand += f" --max-q={MinimumQuantizerLvl}"

    if UsePhotonNoise:
        encodeCommand += f' --enable-dnl-denoising=0 --film-grain-table="{GrainSynthTablePath}"'
    else:
        encodeCommand += f' --enable-dnl-denoising=0 --denoise-noise-level={denoiseLevel}'

    # Start the performance counter
    start = time.perf_counter()

    if TwoPass:
        encodeCommand += f' --fpf="{outpath}.log"'
        encodeCommand += " --passes=2"

        pass1 = copy(encodeCommand)
        pass1 += " --pass=1"
        # print(syscmd(pass1, encoding='utf8'))

        syscmd(pass1)

        pass2 = copy(encodeCommand)
        pass2 += " --pass=2"
        syscmd(pass2)

        os.remove(outpath + '.log')

    else:
        encodeCommand += " --pass=1"

        syscmd(encodeCommand)

    # Stop the performance counter
    end = time.perf_counter()

    # Calculate the elapsed time in seconds
    elapsed_time = end - start

    # Print the elapsed time in seconds
    print(f'Chunk {os.path.basename(outpath)} took {elapsed_time} seconds to run')


def processSingle(tpl):
    global encodedScenes
    frag, i = tpl

    # if i != 1238:
    #     return

    encodedScenePath = tempfolder + str(i) + ('.ivf' if useAom else '.mkv')

    if os.path.exists(encodedScenePath):
        encodedScenes.append(encodedScenePath)
        return

    if useAom:
        encodeAomEnc(inpath=inputfile, outpath=encodedScenePath, start_time=frag[0], end_time=frag[1])
    # else:
    #     encodeSvtAv1(inpath=inputfile, outpath=encodedScenePath, start_time=frag[0], end_time=frag[1], format='360p')

    encodedScenes.append(encodedScenePath)


useAom = True
NumberOfWorkers = 3

if __name__ == "__main__":
    inputfile = '/mnt/sda1/Coraline.2009.BDRemux 1080p.mkv'
    tempfolder = 'temp/'
    sceneCacheFileName = tempfolder + 'sceneCache.json'
    output = 'coraline.mkv'

    if os.path.exists(output):
        print('Output %s already exists' % output)
        finishedMerge = True
        exit()

    if not os.path.exists(tempfolder):
        os.mkdir(tempfolder)
    else:
        # syscmd('for i in ./temp/*.ivf; ffmpeg -v error -i $i -c copy -f null -; if [ $status != "0" ]; echo "File $i is invalid deleting"; rm "$i"; end; end')
        syscmd(f'rm {tempfolder}*.log')
        syscmd(f'rm {tempfolder}*.mkv')

    framerate = get_video_frame_rate(inputfile)

    encodedScenes = []

    if MultiProcessEncode:
        fragments = getVideoSceneList(inputfile, sceneCacheFileName)
        jobs = []

        for i, frag in enumerate(fragments):
            jobs.append((frag, i))
        print(f'Encoding Scenes using {NumberOfWorkers} workers')
        processMap = process_map(processSingle,
                                 jobs,
                                 max_workers=NumberOfWorkers,
                                 chunksize=1,
                                 desc='Encoding Scenes',
                                 unit="scene")

    else:
        fragments = getVideoSceneList(inputfile, sceneCacheFileName)
        for i, frag in enumerate(tqdm(fragments, total=len(fragments), desc='Encoding Scenes', unit='scene')):
            sceneStartTimestamp = frag[0]
            sceneEndTimestamp = frag[1]

            encodedScenePath = tempfolder + str(i) + ('.ivf' if useAom else '.mkv')

            if not os.path.exists(encodedScenePath):
                if useAom:
                    encodeAomEnc(inpath=inputfile, outpath=encodedScenePath, start_time=sceneStartTimestamp,
                                 end_time=sceneEndTimestamp)
                # else:
                #     encodeSvtAv1(inpath=inputfile, outpath=encodedScenePath, start_time=sceneStartTimestamp, end_time=sceneEndTimestamp, format='360p')

            else:
                tqdm.write('Chunk ' + encodedScenePath + ' already exists skipping')

            encodedScenes.append(encodedScenePath)

    quit()
    print('Encoding finished, merging Scenes')
    mergeVideoFiles(encodedScenes, output)

    if not os.path.exists(output):
        print('Failed merge, file %s does not exist try again' % output)
        exit()

    finishedMerge = True

    if not DebugMode:
        shutil.rmtree(tempfolder)
