import os.path
from unittest import TestCase

from hoeEncode.ConvexHullEncoding.ConvexTheHull import ConvexHullEncoder


class TestConvexHullEncoder(TestCase):
    def test_do_the_funny(self):
        encoder = ConvexHullEncoder(clip_path="../test.mkv", output="../test.mp4")
        encoder.do_the_funny()
        self.assertTrue(os.path.exists('../test.mp4'))
        encoder.cleanup_test_dirs()
