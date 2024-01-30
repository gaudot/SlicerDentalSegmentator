import pytest
import slicer

from CMFSegmentatorLib import SegmentationWidget
from .Utils import CMFTestCase


class SegmentationWidgetTestCase(CMFTestCase):
    def test_can_be_displayed(self):
        widget = SegmentationWidget()
        widget.show()
        slicer.app.processEvents()

    @pytest.mark.slow
    def test_can_run_segmentation(self):
        import SampleData
        node = SampleData.SampleDataLogic().downloadMRHead()
        slicer.app.processEvents()

        widget = SegmentationWidget()
        widget.show()
        widget.inputSelector.setCurrentNode(node)

        slicer.app.processEvents()
        self.assertTrue(widget.applyButton.isEnabled())
        self.assertFalse(widget.stopButton.isVisible())

        widget.applyButton.click()
        slicer.app.processEvents()
        self.assertFalse(widget.applyButton.isVisible())
        self.assertTrue(widget.stopButton.isVisible())

        widget.logic.waitForSegmentationFinished()
        slicer.app.processEvents()

        self.assertTrue(widget.applyButton.isVisible())
        self.assertFalse(widget.stopButton.isVisible())

    def test_can_kill_segmentation(self):
        import SampleData
        node = SampleData.SampleDataLogic().downloadMRHead()
        slicer.app.processEvents()

        widget = SegmentationWidget()
        widget.show()
        widget.inputSelector.setCurrentNode(node)
        widget.applyButton.click()
        slicer.app.processEvents()
        widget.stopButton.click()

        self.assertTrue(widget.applyButton.isVisible())
        self.assertFalse(widget.stopButton.isVisible())
