from copy import copy
from typing import List

from hoeEncode.encode.AbstractEncoder import AbstractEncoder
from hoeEncode.encode.FfmpegUtil import create_chunk_ffmpeg_pipe_command
from hoeEncode.encode.global_encoder_config import configSingleton


class AbstractEncoderAomEnc(AbstractEncoder):
    def __init__(self):
        super().__init__()
        self.extra_param = ""

    def get_encode_commands(self) -> List[str]:
        encode_command = create_chunk_ffmpeg_pipe_command(
            end_clip_time=self.chunkEnd,
            start_clip_time=self.chunkStart,
            in_path=self.inPath,
            resolution_canon_name=self.resolution,
            framerate=self.framerate) \
                         + f'| {configSingleton.aom_lavifh_path} - --ivf -o "{self.outPath}" ' \
                           f'--cpu-used={self.encoder_speed} ' \
                           f'--bit-depth=10 ' \
                           f'--threads=2 ' \
                           f'--disable-kf ' \
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
                           f'--vmaf-model-path="{self.vmaf_model}" ' \
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

        # if UseFastLavis:
        # encode_command += ' --tune=lavish_fast'
        encode_command += ' --tune=vmaf_psy_qp'
        # else:
        #     encode_command += ' --tune=lavish_vmaf_rd'

        if self.bitrate_diss == 0 and self.bitrate != -1:
            encode_command += f" --end-usage=vbr --target-bitrate={self.bitrate}"
        elif self.bitrate_diss == 2:
            encode_command += f" --end-usage=cq --cq-level={self.cq_level} --target-bitrate={self.bitrate} "
        elif self.bitrate_diss == 1:
            encode_command += f" --end-usage=q --cq-level={self.cq_level}"

        encode_command += self.extra_param

        # if self.:
        #     encode_command += f" --max-q={MinimumQuantizerLvl}"

        if self.photon_noise_path != "":
            encode_command += f' --enable-dnl-denoising=0 --film-grain-table="{self.photon_noise_path}"'
        else:
            encode_command += f' --enable-dnl-denoising=0 --denoise-noise-level={self.grain_synth}'

        if self.two_pass:
            encode_command += f' --fpf="{self.outPath}.log"'
            encode_command += " --passes=2"

            pass1 = copy(encode_command)
            pass1 += " --pass=1"
            pass2 = copy(encode_command)
            pass2 += " --pass=2"

            return [pass1, pass2, f"rm {self.outPath}.log"]

        else:
            encode_command += " --pass=1"

            return [encode_command]

    def extra_flags(self, param):
        self.extra_param = param
