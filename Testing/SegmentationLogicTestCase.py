import pytest

from CMFSegmentatorLib import SegmentationLogic
from .Utils import CMFTestCase, load_test_CT_volume


class SegmentationLogicTestCase(CMFTestCase):
    def setUp(self):
        super().setUp()
        self.logic = SegmentationLogic()
        self.volume = load_test_CT_volume()

    @pytest.mark.slow
    def test_can_run_head_segmentation(self):
        segmentation = self.logic.runCmfSegmentation(self.volume)
        self.assertIsNotNone(segmentation)
        self.assertEqual(segmentation.GetSegmentation().GetNumberOfSegments(), 5)


