import unittest
from pathlib import Path

import slicer


class DentalSegmentatorTestCase(unittest.TestCase):
    def setUp(self):
        self._clearScene()

    @staticmethod
    def _clearScene():
        slicer.app.processEvents()
        slicer.mrmlScene.Clear()
        slicer.app.processEvents()

    def tearDown(self):
        slicer.app.processEvents()


def _dataFolderPath():
    return Path(r"\\wheezy\DevApp\Projects\FFO_3DSlicer\Data\TestingData")


def load_test_CT_volume():
    return slicer.util.loadVolume(_dataFolderPath().joinpath("Patient_020_0000.nii.gz").as_posix())


def get_test_multi_label_path():
    return _dataFolderPath().joinpath("Patient_020.nii.gz").as_posix()


def get_test_multi_label_path_with_segments_1_3_5():
    return _dataFolderPath().joinpath("Patient_020_segment_1_3_5.nii.gz").as_posix()
