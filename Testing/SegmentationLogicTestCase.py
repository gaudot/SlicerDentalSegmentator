from unittest.mock import MagicMock

import pytest

from CMFSegmentatorLib import SegmentationLogic
from .Utils import CMFTestCase, load_test_CT_volume
import slicer


class SegmentationLogicTestCase(CMFTestCase):
    def setUp(self):
        super().setUp()
        self.logic = SegmentationLogic()
        self.volume = load_test_CT_volume()

    @pytest.mark.slow
    def test_can_run_head_segmentation(self):
        inferenceFinishedMock = MagicMock()
        errorMock = MagicMock()

        self.logic.inferenceFinished.connect(inferenceFinishedMock)
        self.logic.errorOccurred.connect(errorMock)

        self.logic.startCmfSegmentation(self.volume)
        while not inferenceFinishedMock.called and not errorMock.called:
            slicer.app.processEvents()

        inferenceFinishedMock.assert_called()
        errorMock.assert_not_called()

        segmentation = self.logic.loadCmfSegmentation()
        self.assertIsNotNone(segmentation)
        self.assertEqual(segmentation.GetSegmentation().GetNumberOfSegments(), 5)
