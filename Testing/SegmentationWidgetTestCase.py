from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

import slicer

from DentalSegmentatorLib import SegmentationWidget, Signal, ExportFormat
from .Utils import DentalSegmentatorTestCase, get_test_multi_label_path


class MockLogic:
    def __init__(self):
        self.inferenceFinished = Signal()
        self.errorOccurred = Signal("str")
        self.progressInfo = Signal("str")
        self.startDentalSegmentation = MagicMock()
        self.stopDentalSegmentation = MagicMock()
        self.waitForSegmentationFinished = MagicMock()
        self.loadDentalSegmentation = MagicMock()
        self.loadDentalSegmentation.side_effect = self.load_segmentation

    @staticmethod
    def load_segmentation():
        return slicer.util.loadSegmentation(get_test_multi_label_path())


class SegmentationWidgetTestCase(DentalSegmentatorTestCase):
    def setUp(self):
        import SampleData
        super().setUp()
        self.logic = MockLogic()
        self.node = SampleData.SampleDataLogic().downloadMRHead()

        self.widget = SegmentationWidget(logic=self.logic)
        self.widget.inputSelector.setCurrentNode(self.node)
        self.widget.show()
        slicer.app.processEvents()

    def test_can_be_displayed(self):
        slicer.app.processEvents()

    def test_can_run_segmentation(self):
        slicer.app.processEvents()
        self.assertTrue(self.widget.applyButton.isEnabled())
        self.assertFalse(self.widget.stopButton.isVisible())

        self.widget.applyButton.click()
        slicer.app.processEvents()
        self.assertFalse(self.widget.applyButton.isVisible())
        self.assertTrue(self.widget.stopButton.isVisible())

        self.logic.startDentalSegmentation.assert_called_once_with(self.node)
        self.logic.inferenceFinished()
        slicer.app.processEvents()

        self.assertTrue(self.widget.applyButton.isVisible())
        self.assertFalse(self.widget.stopButton.isVisible())
        self.logic.loadDentalSegmentation.assert_called_once()

    def test_can_kill_segmentation(self):
        self.widget.applyButton.click()
        self.logic.startDentalSegmentation.assert_called_once()

        self.widget.stopButton.click()
        self.logic.stopDentalSegmentation.assert_called_once()
        self.logic.waitForSegmentationFinished.assert_called_once()
        self.assertTrue(self.widget.applyButton.isVisible())
        self.assertFalse(self.widget.stopButton.isVisible())

    def test_loading_replaces_existing_segmentation_node(self):
        self.logic.inferenceFinished()
        slicer.app.processEvents()
        self.logic.inferenceFinished()
        slicer.app.processEvents()
        self.assertEqual(self.logic.loadDentalSegmentation.call_count, 2)
        self.assertEqual(len(list(slicer.mrmlScene.GetNodesByClass("vtkMRMLSegmentationNode"))), 1)

    def test_loading_sets_correct_segment_names(self):
        self.logic.inferenceFinished()
        slicer.app.processEvents()
        node = self.widget.getCurrentSegmentationNode()
        self.assertIsNotNone(node)

        exp_names = {"Maxilla / Upper Skull", "Mandible", "Upper Teeth", "Lower Teeth", "Mandibular canal"}
        segmentation = node.GetSegmentation()
        segmentIds = [segmentation.GetNthSegmentID(i) for i in range(segmentation.GetNumberOfSegments())]
        segmentNames = {segmentation.GetSegment(segmentId).GetName() for segmentId in segmentIds}
        self.assertEqual(segmentNames, exp_names)

    def test_can_export_segmentation_to_file(self):
        self.logic.inferenceFinished()
        slicer.app.processEvents()
        self.widget.objCheckBox.setChecked(True)
        self.widget.stlCheckBox.setChecked(True)
        self.widget.niftiCheckBox.setChecked(True)
        allFormats = self.widget.getSelectedExportFormats()
        self.assertEqual(
            allFormats,
            ExportFormat.NIFTI | ExportFormat.STL | ExportFormat.OBJ
        )

        with TemporaryDirectory() as tmp:
            self.widget.exportSegmentation(self.widget.getCurrentSegmentationNode(), tmp, allFormats)
            slicer.app.processEvents()

            tmpPath = Path(tmp)
            self.assertEqual(len(list(tmpPath.glob("*.stl"))), 5)
            self.assertEqual(len(list(tmpPath.glob("*.obj"))), 1)
            self.assertEqual(len(list(tmpPath.glob("*.nii.gz"))), 1)
