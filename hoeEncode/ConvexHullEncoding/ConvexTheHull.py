# paper describing what im doing here is in /somepapers/10000000_863740581203161_2149566830994795679_n.pdf
import os.path
import shutil

from matplotlib import pyplot as plt

from hoeEncode.encode.FfmpegUtil import syscmd, get_video_vmeth
from hoeEncode.encode.encoderImpl.Aomenc import AbstractEncoderAomEnc





class ConvexHullEncoder:
    def __init__(self, clip_path="", output="", vmaf_target=94, mode=1, bitrate_cap=-1, width=-1, height=-1,
                 tmppath="./tmp/convexHull/"):
        """
        MODES:
        0 means we optimise to get highest vmaf at the target bitrate,
        1 means we are searching for target vmaf at lowest bitrate possible
        """
        self.mode = mode
        self.mode = 0
        self.bitrate_cap = -1
        self.width = width
        self.height = height
        self.bitrate_cap = bitrate_cap
        self.vmaf_target = vmaf_target
        self.outpath_path = output
        self.clip_path = clip_path
        self.tmppath = tmppath + os.path.splitext(os.path.basename(output))[0] + "/"

    def prepare_test_dirs(self):
        if not os.path.exists(self.tmppath):
            os.makedirs(self.tmppath)

    def cleanup_test_dirs(self):
        shutil.rmtree(self.tmppath)

    test_counter = 0
    rd_points = []

    aom = None

    # since we encode at speed 9 speed the vmaf is going to be lower,
    # this is why im adding this offset to the speed 9 vmaf
    # that is an approximate the vmaf difference between speed 3 and 9
    vmaf_speed_offset_affect = 15

    # the minimum cq that will get picked
    min_cq = 16

    # the maximum cq that will get picked
    max_cq = 60

    # the maximum amount of tires that the program will try to optimise cq
    # going above 3 is wasteful
    max_tries = 3

    def create_rd_point(self, cq=0):
        dflt_test = f"{self.tmppath}{self.test_counter}.ivf"
        self.test_counter += 1

        self.aom.set_cq_level(cq)
        self.aom.init_encoder(inpath=self.clip_path, outpath=dflt_test, chunkend=100, chunkstart=0)

        for command in self.aom.get_encode_commands():
            print(command)
            print(syscmd(command, 'utf8'))

        vmaf = get_video_vmeth(dflt_test, self.clip_path, 100)
        file_size = os.path.getsize(dflt_test)

        print(f" Encoded using speed 9 and cq {cq} and got {vmaf}Vmaf at {file_size} file size")
        rd_point = [vmaf, file_size, dflt_test, cq]
        self.rd_points.append(rd_point)
        return rd_point

    def not_fine_enough(self, iteration_counter, vmaf_target):
        if iteration_counter > self.max_tries:
            return False
        best_point = None
        for rd_point in self.rd_points:
            if best_point is None:
                best_point = rd_point
                continue
            if rd_point[0] > best_point[0] and best_point[1] > rd_point[1]:
                # if file curr best is larger and has lower vmaf
                best_point = rd_point

        vmaf_diss = vmaf_target - (best_point[0] + self.vmaf_speed_offset_affect)

        # vmaf target miss is less than .5
        if vmaf_diss < 0.5:
            return False

        # if we already did two passes and vmaf target miss is less than 1
        if vmaf_diss < 1 and iteration_counter < 2:
            return False

        return True


    def do_the_funny(self):
        self.prepare_test_dirs()

        ideal_cq = self.max_cq

        self.aom = AbstractEncoderAomEnc()
        self.aom.set_vmaf_model_path("../../vmaf_v0.6.1neg.json")

        self.aom.set_encoder_speed(9)
        self.aom.set_photon_noise_path("/home/kokoniara/dev/VideoSplit/Photon-Noise-Tables-aomenc-repo/1920x1080/1920x1080-SRGB-ISO-Photon/1920x1080-SRGB-ISO400.tbl")

        if self.mode == 1:
            self.aom.set_bitrate_distribution_mode(2)
            self.aom.set_bitrate(self.bitrate_cap)
        else:
            self.aom.set_bitrate_distribution_mode(1)
            self.create_rd_point(cq=ideal_cq)

            iteration_counter = 0
            while self.not_fine_enough(iteration_counter, self.vmaf_target):
                # this will scale the vmaf difference to the target, and pick the cq value in
                ideal_cq = self.min_cq + ((ideal_cq - self.min_cq) / 2)
                if ideal_cq > self.max_cq:
                    ideal_cq = self.max_cq

                self.create_rd_point(cq=int(ideal_cq))
                iteration_counter += 1

        print("Listing rd points: ")

        for vmaf, size, path, cq in self.rd_points:
            print(f" path: {path} size:{size} {vmaf}VMAF, CQ: {cq}")

        print(f"Ideal cq for {self.vmaf_target}VMAF: {ideal_cq}")

        # Extract the VMAF and CQ values from the data
        vmaf_values = [item[0] for item in self.rd_points]
        cq_values = [item[3] for item in self.rd_points]

        plt.plot(vmaf_values, cq_values, 'ro')
        plt.xlabel("VMAF")
        plt.ylabel("CQ")
        plt.show()

        encodeAom = AbstractEncoderAomEnc()
        encodeAom.init_encoder(self.clip_path, self.outpath_path)
        encodeAom.set_photon_noise_path("/home/kokoniara/dev/VideoSplit/Photon-Noise-Tables-aomenc-repo/1920x1080"
                                        "/1920x1080-SRGB-ISO-Photon/1920x1080-SRGB-ISO400.tbl")
        encodeAom.set_bitrate_distribution_mode(1)
        encodeAom.set_encoder_speed(3)
        encodeAom.set_vmaf_model_path("../../vmaf_v0.6.1neg.json")
        encodeAom.set_cq_level(int(ideal_cq))
        for command in encodeAom.get_encode_commands():
            print(syscmd(command, 'utf8'))


if __name__ == '__main__':
    encoder = ConvexHullEncoder(clip_path="./ref.mkv", output="./test.mp4", mode=1, vmaf_target=94)
    encoder.do_the_funny()
    # encoder.cleanup_test_dirs()
