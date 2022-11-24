from multiprocessing import Process
import time
import os
import subprocess
from shutil import which

FFMPEGPATH = '/home/kokoniara/ffmpeg_sources/ffmpeg/ffmpeg'

def decodefancynumber(number):
    suffixes = {'K': 1000, 'M': 1000000, 'k': 1000, 'm': 1000000}
    # value = '3.2B' #  for example
    if number[-1] in suffixes.keys():
        number = int(number[:-1]) * suffixes.get(number[-1])
    if not isinstance(number, int):
        raise Exception('suplied not a number')
    return number

def genFormat(resolution, bitrate, maxWidth = 0):
    outcommandvec = []

    if (resolution is None and bitrate is None) or (resolution == '' and bitrate == ''):
        outcommandvec += ['-vf', 'scale=-2:1080:flags=lanczos']
        outcommandvec += ['-b:v', '1500k']
        outcommandvec += ['-maxrate', '2000k']
        outcommandvec += ['-bufsize', '6000k']
    else:
        possileresolutions = [360, 480, 720, 1080]

        if resolution != '' and resolution is not None:
            width = int(resolution[0:len(resolution)-1])

            if maxWidth != 0:
                biggestallowedwidth = 0
                for res in possileresolutions:
                    if res > biggestallowedwidth and res < width and maxWidth >= res:
                        biggestallowedwidth = res

                if biggestallowedwidth != 0:
                    outcommandvec += ['-vf', 'scale=-2:%d:flags=lanczos' % biggestallowedwidth]

            else:
                if width in possileresolutions:
                    outcommandvec += ['-vf', 'scale=-2:%d:flags=lanczos' % width]

        # match resolution:
        #     case '360p':
        #         outcommandvec += ['-vf', 'scale=-2:360:flags=lanczos']
        #     case '480p':
        #         outcommandvec += ['-vf', 'scale=-2:468:flags=lanczos']
        #     case '720p':
        #         outcommandvec += ['-vf', 'scale=-2:720:flags=lanczos']
        #     case '1080p':
        #         outcommandvec += ['-vf', 'scale=-2:1080:flags=lanczos']

        if bitrate is None or bitrate == '':
            outcommandvec += ['-b:v', '2M']
            outcommandvec += ['-maxrate', '3M']
            outcommandvec += ['-bufsize', '2M']
        else:
            outcommandvec += ['-b:v', bitrate]
            bitratenumber = decodefancynumber(bitrate)

            outcommandvec += ['-maxrate', str(int(round(bitratenumber * 1.5)))]
            outcommandvec += ['-bufsize', str(bitratenumber * 2)]

    return outcommandvec

def doesBinaryExist(pathOrLocation):
    return which(pathOrLocation) is not None


def doesSupportsvtEncode(path):
    result = subprocess.run([
        path,
        '-codecs',
        '-hide_banner'
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = result.stdout.decode('utf-8').find('libsvtav1')
    return result > -1


def encodesvtav1(resolution='1080p', bitrate=-1, inpath='', outpath='', overwrite=False):
    if inpath == '' or outpath == '' or not os.path.exists(inpath):
        raise Exception('invalid out/in paths')

    if not doesBinaryExist(FFMPEGPATH):
        raise Exception('cannot find ffmpeg')

    if not doesSupportsvtEncode(FFMPEGPATH):
        raise Exception('ffmpeg build does not support svtav1')

    command_vec = [FFMPEGPATH]

    if overwrite:
        command_vec += ['-y']
    else:
        command_vec += ['-n']

    command_vec += ['-v', 'error', '-stats']

    command_vec += ['-i', inpath]

    command_vec += ['-c:v', 'libsvtav1']

    command_vec += ['-preset', '4']

    command_vec += genFormat(resolution, bitrate)

    command_vec += ['-vsync', '0']

    command_vec += ['-svtav1-params',
                    'tune=0:enable-overlays=1:scd=0:rc=0:film-grain=14:chroma-u-dc-qindex-offset=-2:chroma-u-ac'
                    '-qindex-offset=-2:chroma-v-dc-qindex-offset=-2:chroma-v-ac-qindex-offset=-2 '
                    ]

    # open gop
    command_vec += ['-g', '-1']

    command_vec += ['-pix_fmt', 'yuv420p10le']

    command_vec += [outpath]

    result = subprocess.run(command_vec, stdout=subprocess.PIPE)




# if __name__ == '__main__':
#     process = Process(target=my_func_1)
#     process.start()
#
#     process.join()
#
    # print(f'Two thread total time: {time.time() - start}')
