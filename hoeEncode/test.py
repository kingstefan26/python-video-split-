import unittest
import os
import tempfile

from encode import encode


class TestNumbers(unittest.TestCase):
    def test_fancynumber_decoder(self):
        t1 = encode.decodefancynumber('30K')
        self.assertEqual(t1, 30_000)

        t1 = encode.decodefancynumber('30k')
        self.assertEqual(t1, 30_000)

        t2 = encode.decodefancynumber('2M')
        self.assertEqual(t2, 2_000_000)

        t3 = encode.decodefancynumber('2m')
        self.assertEqual(t3, 2_000_000)

        self.assertRaises(Exception, lambda: encode.decodefancynumber('abc'))

        self.assertRaises(Exception, lambda: encode.decodefancynumber('1t'))

class TestFormatGen(unittest.TestCase):

    def test_resolution(self):
        self.assertEqual(encode.genFormat('1080p', None), ['-vf', 'scale=-2:1080:flags=lanczos', '-b:v', '2M', '-maxrate', '3M', '-bufsize', '2M'])

    def test_bitrate(self):
        self.assertEqual(encode.genFormat('', '2M'), ['-b:v', '2M', '-maxrate', '3000000', '-bufsize', '4000000'])
        self.assertEqual(encode.genFormat(None, '2k'), ['-b:v', '2k', '-maxrate', '3000', '-bufsize', '4000'])

        for i in range(100):
            self.assertEqual(encode.genFormat(None, str(i) + 'k'), ['-b:v', str(i) + 'k', '-maxrate',  str(i * 1500), '-bufsize', str(i * 2000)])

        for i in range(100):
            self.assertEqual(encode.genFormat(None, str(i) + 'm'), ['-b:v', str(i) + 'm', '-maxrate',  str(i * 1_500_000), '-bufsize', str(i * 2_000_000)])

    def test_bitrate_and_resolution(self):
        self.assertEqual(encode.genFormat('1080p', '2M'), ['-vf', 'scale=-2:1080:flags=lanczos', '-b:v', '2M', '-maxrate', '3000000', '-bufsize', '4000000'])

    def test_empty(self):
        self.assertEqual(encode.genFormat('', ''), ['-vf', 'scale=-2:1080:flags=lanczos', '-b:v', '1500k', '-maxrate', '2000k', '-bufsize', '6000k'])
        self.assertEqual(encode.genFormat(None, None), ['-vf', 'scale=-2:1080:flags=lanczos', '-b:v', '1500k', '-maxrate', '2000k', '-bufsize', '6000k'])

    def test_res_cap(self):
        capped = encode.genFormat('1080p', None, maxWidth=540)
        self.assertEqual(capped, ['-vf', 'scale=-2:480:flags=lanczos', '-b:v', '2M', '-maxrate', '3M', '-bufsize', '2M'])


class TestEncode(unittest.TestCase):

    def setUp(self):
        THIS_DIR = os.path.dirname(os.path.abspath(__file__))
        self.testclippath = os.path.join(THIS_DIR, 'test.mkv')

        if not os.path.exists(self.testclippath):
            raise Exception('Count find test clip')

    def test_simple_encode(self):
        tempf = tempfile.mkstemp(suffix='.mkv')
        encode.encodesvtav1('360p', '10k', self.testclippath, outpath=tempf[1], overwrite=True)

        videoexists = os.path.exists(tempf[1])

        filesize = os.path.getsize(tempf[1])

        self.assertEqual(videoexists, True)

        self.assertEqual(filesize > 1, True)

        os.remove(tempf[1])



if __name__ == '__main__':
    unittest.main()
