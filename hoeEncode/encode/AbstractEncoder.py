from abc import abstractmethod, ABC
from typing import List


class AbstractEncoder(ABC):
    def __init__(self):
        self.vmaf_model = "vmaf_v0.6.1neg.json"
        self.two_pass = False
        self.encoder_speed = 3
        self.is_high_detail = True
        self.is_anime = False
        self.framerate = -1
        self.resolution = "source"
        self.photon_noise_path = ""
        self.grain_synth = -1
        self.bitrate = -1
        self.cq_level = -1
        self.bitrate_diss = 2
        self.chunkStart = -1
        self.chunkEnd = -1
        self.outPath = ""
        self.inPath = ""

    def init_encoder(self, inpath="", outpath="", chunkstart=-1, chunkend=-1):
        self.inPath = inpath
        self.outPath = outpath
        self.chunkStart = chunkstart
        self.chunkEnd = chunkend

    def set_bitrate_distribution_mode(self, mode=1):
        """
        :param mode: 0:bitrate limited 1:quality level  2:quality level constrained by bitrate
        """
        self.bitrate_diss = mode

    def set_cq_level(self, cq=24):
        self.cq_level = cq

    def set_bitrate(self, bitrate=2500):
        self.bitrate = bitrate

    def set_grain_synth_level(self, level=12):
        self.grain_synth = level

    def set_photon_noise_path(self, path="./no"):
        self.photon_noise_path = path


    def set_vmaf_model_path(self, path=""):
        self.vmaf_model = path

    def encode_properties(self, resolution="source", framerate="auto"):
        self.resolution = resolution
        self.framerate = framerate

    def content_properties(self, is_anime=False, is_high_detail=False):
        self.is_anime = is_anime
        self.is_high_detail = is_high_detail

    def set_encoder_speed(self, speed=3):
        self.encoder_speed = speed

    def use_two_pass(self):
        self.two_pass = True

    @abstractmethod
    def get_encode_commands(self) -> List[str]:
        pass
