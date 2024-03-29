from unittest.mock import MagicMock

import pytest
import slicer

from DentalSegmentatorLib import SegmentationLogic
from .Utils import DentalSegmentatorTestCase, load_test_CT_volume


class SegmentationLogicTestCase(DentalSegmentatorTestCase):
    def setUp(self):
        super().setUp()
        self.logic = SegmentationLogic()
        self.volume = load_test_CT_volume()

    @pytest.mark.slow
    def test_can_run_head_segmentation(self):
        inferenceFinishedMock = MagicMock()
        errorMock = MagicMock()
        infoMock = MagicMock()

        self.logic.inferenceFinished.connect(inferenceFinishedMock)
        self.logic.errorOccurred.connect(errorMock)
        self.logic.progressInfo.connect(infoMock)

        self.logic.startDentalSegmentation(self.volume)
        while not inferenceFinishedMock.called and not errorMock.called:
            slicer.app.processEvents()

        inferenceFinishedMock.assert_called()
        infoMock.assert_called()
        errorMock.assert_not_called()

        segmentation = self.logic.loadDentalSegmentation()
        self.assertIsNotNone(segmentation)
        self.assertEqual(segmentation.GetSegmentation().GetNumberOfSegments(), 5)
