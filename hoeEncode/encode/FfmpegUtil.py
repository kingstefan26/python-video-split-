import re
import subprocess


def get_quality_preset(resolution_canon_name):
    match resolution_canon_name:
        case '360p':
            return '-vf scale=-2:360'
        case '480p':
            return '-vf scale=-2:468'
        case '720p':
            return '-vf scale=-2:720'
        case '1080p':
            return '-vf scale=-2:1080'
    return ''


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

vmafRegex = re.compile(r'VMAF score: ([0-9]+\.[0-9]+)')
def get_video_vmeth(distorted_path, ref_path, time=-1):
    null_ = f"ffmpeg -hide_banner -i {distorted_path} -i {ref_path} "

    if time != -1:
        null_ += f"-t {(float(time) / get_video_frame_rate(distorted_path))} "

    null_ += f"-filter_complex libvmaf -f null -"

    result_string = syscmd(null_, "utf8")
    try:
        match = vmafRegex.search(result_string)
        vmaf_score = float(match.group(1))
        return vmaf_score
    except AttributeError:
        print(f"Failed getting vmeth comparing {distorted_path} agains {ref_path}")
        return 0


def create_chunk_ffmpeg_pipe_command(resolution_canon_name="source", start_clip_time=0, end_clip_time=0, in_path="./no",
                                     framerate=-1):
    if framerate == -1:
        framerate = get_video_frame_rate(in_path)

    end_thingy = (float(end_clip_time) / framerate)
    start_time = (float(start_clip_time) / framerate)
    duration = (end_thingy - start_time)

    end_command = "ffmpeg -v error -nostdin "

    if start_clip_time != -1:
        end_command += f"-ss {str(start_time)} "

    end_command += f"-i {in_path} "

    if end_clip_time != -1:
        end_command += f"-t {str(duration)} "

    end_command += f"-an -sn -strict -1 {get_quality_preset(resolution_canon_name)} -f yuv4mpegpipe - "

    return end_command
