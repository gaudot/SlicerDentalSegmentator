import os
from unittest.mock import MagicMock

import slicer

from DentalSegmentatorLib import PythonDependencyChecker, SegmentationWidget
from .Utils import DentalSegmentatorTestCase, load_test_CT_volume
import qt
import pytest


@pytest.mark.slow
class IntegrationTestCase(DentalSegmentatorTestCase):
    def setUp(self):
        super().setUp()
        self.tmpDir = qt.QTemporaryDir()
        self.noConnectionF = MagicMock(return_value=False)
        self.mockProgressCallback = MagicMock()
        self.mockErrorDisplay = MagicMock()
        self.deps = PythonDependencyChecker(destWeightFolder=self.tmpDir.path(), errorDisplayF=self.mockErrorDisplay)

    def test_can_auto_download_weights(self):
        self.assertTrue(self.deps.areWeightsMissing())
        self.assertTrue(self.deps.downloadWeights(self.mockProgressCallback))
        self.assertFalse(self.deps.areWeightsMissing())
        self.assertFalse(self.deps.areWeightsOutdated())
        self.mockErrorDisplay.assert_not_called()

    def test_can_update_weights(self):
        self.assertTrue(self.deps.downloadWeights(self.mockProgressCallback))
        self.deps.writeDownloadInfoURL("outdated_url")
        self.assertFalse(self.deps.areWeightsMissing())
        self.assertTrue(self.deps.areWeightsOutdated())
        self.assertTrue(self.deps.downloadWeights(self.mockProgressCallback))
        self.assertFalse(self.deps.areWeightsOutdated())
        self.mockErrorDisplay.assert_not_called()

    def test_given_weights_and_no_internet_connection_weights_are_up_to_date(self):
        self.assertTrue(self.deps.downloadWeights(self.mockProgressCallback))
        self.deps.writeDownloadInfoURL("outdated_url")
        self.deps.hasInternetConnectionF = self.noConnectionF
        self.assertFalse(self.deps.areWeightsMissing())
        self.assertFalse(self.deps.areWeightsOutdated())

    def test_given_weights_and_no_download_url_weights_are_up_to_date(self):
        self.assertTrue(self.deps.downloadWeights(self.mockProgressCallback))
        os.remove(self.deps.getWeightDownloadInfoPath())
        self.assertFalse(self.deps.areWeightsMissing())
        self.assertFalse(self.deps.areWeightsOutdated())

    def test_given_no_weights_and_no_internet_connection_download_yield_error(self):
        self.deps.hasInternetConnectionF = self.noConnectionF
        self.assertTrue(self.deps.areWeightsMissing())
        self.assertFalse(self.deps.downloadWeights(self.mockProgressCallback))
        self.assertFalse(self.deps.downloadWeightsIfNeeded(self.mockProgressCallback))
        self.mockErrorDisplay.assert_called()

    def test_dental_segmentator_can_run_segmentation(self):
        self.widget = SegmentationWidget()
        self.widget.inputSelector.setCurrentNode(load_test_CT_volume())
        self.widget.applyButton.clicked()
        self.widget.logic.waitForSegmentationFinished()
        slicer.app.processEvents()
        segmentations = list(slicer.mrmlScene.GetNodesByClass("vtkMRMLSegmentationNode"))
        self.assertEqual(len(segmentations), 1)
