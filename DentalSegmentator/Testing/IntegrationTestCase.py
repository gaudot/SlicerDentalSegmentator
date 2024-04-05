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

    def test_can_auto_download_weights(self):
        deps = PythonDependencyChecker(destWeightFolder=self.tmpDir.path())
        self.assertTrue(deps.areWeightsMissing())
        deps.downloadWeights(lambda *_: None)
        self.assertFalse(deps.areWeightsMissing())
        self.assertFalse(deps.areWeightsOutdated())

    def test_can_update_weights(self):
        deps = PythonDependencyChecker(destWeightFolder=self.tmpDir.path())
        deps.downloadWeights(lambda *_: None)
        deps.writeDownloadInfoURL("outdated_url")
        self.assertFalse(deps.areWeightsMissing())
        self.assertTrue(deps.areWeightsOutdated())
        deps.downloadWeights(lambda *_: None)
        self.assertFalse(deps.areWeightsOutdated())

    def test_dental_segmentator_can_run_segmentation(self):
        self.widget = SegmentationWidget()
        self.widget.inputSelector.setCurrentNode(load_test_CT_volume())
        self.widget.applyButton.clicked()
        self.widget.logic.waitForSegmentationFinished()
        slicer.app.processEvents()
        segmentations = list(slicer.mrmlScene.GetNodesByClass("vtkMRMLSegmentationNode"))
        self.assertEqual(len(segmentations), 1)
