import qt
import slicer
from slicer.util import VTKObservationMixin

from .IconPath import icon, iconPath
from .SegmentationLogic import SegmentationLogic
from .Utils import createButton


class SegmentationWidget(qt.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logic = SegmentationLogic()

        self.inputSelector = slicer.qMRMLNodeComboBox(self)
        self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.inputSelector.selectNodeUponCreation = False
        self.inputSelector.addEnabled = False
        self.inputSelector.showHidden = False
        self.inputSelector.removeEnabled = False
        self.inputSelector.setMRMLScene(slicer.mrmlScene)
        self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateApplyEnabled)

        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.inputSelector)
        self.applyButton = createButton(
            "Apply",
            callback=self.onApplyClicked,
            toolTip="Click to run the CMF segmentation.",
            icon=icon("start_icon.png")
        )
        self.stopButton = createButton(
            "Stop",
            callback=self.onStopClicked,
            toolTip="Click to Stop the CMF segmentation."
        )
        self.stopButton.setVisible(False)
        self.loading = qt.QMovie(iconPath("loading.gif"))
        self.loading.setScaledSize(qt.QSize(24, 24))
        self.loading.frameChanged.connect(self._updateStopIcon)
        self.loading.start()

        layout.addWidget(self.applyButton)
        layout.addWidget(self.stopButton)

        self.logic.inferenceFinished.connect(self.onInferenceFinished)
        self.logic.errorOccurred.connect(self.onInferenceError)
        self.updateApplyEnabled()

        self.isStopping = False

    def _updateStopIcon(self):
        self.stopButton.setIcon(qt.QIcon(self.loading.currentPixmap()))

    def onStopClicked(self):
        """
        When user kills the execution, don't show any error window and wait for process to be killed in the logic.
        Once cleanup is done, restore buttons.
        """

        self.isStopping = True
        self.logic.stopCmfSegmentation()
        self.logic.waitForSegmentationFinished()
        slicer.app.processEvents()
        self.isStopping = False

        self.stopButton.setVisible(False)
        self.applyButton.setVisible(True)

    def onApplyClicked(self, *_):
        import torch
        if not torch.cuda.is_available():
            slicer.util.errorDisplay(
                "This module is only compatible with torch CUDA.\n"
                "Please make sure you have a compatible device, reinstall PyTorch 2.2.0+ with CUDA\n"
                "and restart 3D Slicer to proceed."
            )
            return

        self.applyButton.setVisible(False)
        self.stopButton.setVisible(True)
        slicer.app.processEvents()
        self.logic.startCmfSegmentation(self._currentVolumeNode())

    def updateApplyEnabled(self, *_):
        self.applyButton.setEnabled(self._currentVolumeNode() is not None)

    def _currentVolumeNode(self):
        return self.inputSelector.currentNode()

    def onInferenceFinished(self, *_):
        if self.isStopping:
            return

        self.stopButton.setVisible(False)
        self.applyButton.setVisible(True)

        try:
            self.logic.loadCmfSegmentation()
        except RuntimeError as e:
            slicer.util.errorDisplay(e)

    def onInferenceError(self, errorMsg):
        if self.isStopping:
            return

        slicer.util.errorDisplay("Encountered error during inference :\n" + errorMsg)
