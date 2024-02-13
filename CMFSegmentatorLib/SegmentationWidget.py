from typing import Optional

import qt
import slicer
from slicer.util import VTKObservationMixin

from .IconPath import icon, iconPath
from .PythonDependencyChecker import PythonDependencyChecker
from .SegmentationLogic import SegmentationLogic, SegmentationLogicProtocol
from .Utils import createButton


class SegmentationWidget(qt.QWidget):
    def __init__(self, logic: Optional[SegmentationLogicProtocol] = None, parent=None):
        super().__init__(parent)
        self.logic = logic or SegmentationLogic()
        self._prevSegmentationNode = None

        self.inputSelector = slicer.qMRMLNodeComboBox(self)
        self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.inputSelector.selectNodeUponCreation = False
        self.inputSelector.addEnabled = False
        self.inputSelector.showHidden = False
        self.inputSelector.removeEnabled = False
        self.inputSelector.setMRMLScene(slicer.mrmlScene)
        self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onInputChanged)

        # Configure segment editor
        self.segmentationNodeSelector = slicer.qMRMLNodeComboBox(self)
        self.segmentationNodeSelector.nodeTypes = ["vtkMRMLSegmentationNode"]
        self.segmentationNodeSelector.selectNodeUponCreation = False
        self.segmentationNodeSelector.addEnabled = True
        self.segmentationNodeSelector.removeEnabled = True
        self.segmentationNodeSelector.showHidden = False
        self.segmentationNodeSelector.renameEnabled = True
        self.segmentationNodeSelector.setMRMLScene(slicer.mrmlScene)
        self.segmentationNodeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateSegmentEditorWidget)

        # Create segment editor widget
        self.segmentEditorWidget = slicer.qMRMLSegmentEditorWidget(self)
        self.segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
        self.segmentEditorWidget.setSegmentationNodeSelectorVisible(False)
        self.segmentEditorWidget.setSourceVolumeNodeSelectorVisible(False)
        self.segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
        self.segmentEditorWidget.setMRMLSegmentEditorNode(self.segmentEditorNode)

        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.inputSelector)
        layout.addWidget(self.segmentationNodeSelector)
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
        layout.addWidget(self.segmentEditorWidget)

        self.logic.inferenceFinished.connect(self.onInferenceFinished)
        self.logic.errorOccurred.connect(self.onInferenceError)
        self.onInputChanged()

        self.isStopping = False

        self.dependencyChecker = PythonDependencyChecker()

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
        self.dependencyChecker.downloadDependenciesIfNeeded()
        self.applyButton.setVisible(False)
        self.stopButton.setVisible(True)
        slicer.app.processEvents()
        self.logic.startCmfSegmentation(self.getCurrentVolumeNode())

    def onInputChanged(self, *_):
        self.applyButton.setEnabled(self.getCurrentVolumeNode() is not None)
        self.updateSegmentEditorWidget()

    def updateSegmentEditorWidget(self, *_):
        if self._prevSegmentationNode:
            self._prevSegmentationNode.SetDisplayVisibility(False)

        segmentationNode = self.getCurrentSegmentationNode()
        self._prevSegmentationNode = segmentationNode
        self._initializeSegmentationNodeDisplay(segmentationNode)
        self.segmentEditorWidget.setSegmentationNode(segmentationNode)
        self.segmentEditorWidget.setSourceVolumeNode(self.getCurrentVolumeNode())

    def _initializeSegmentationNodeDisplay(self, segmentationNode):
        if not segmentationNode:
            return

        segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(self.getCurrentVolumeNode())
        if not segmentationNode.GetDisplayNode():
            segmentationNode.CreateDefaultDisplayNodes()

        segmentationNode.SetDisplayVisibility(True)

    def getCurrentVolumeNode(self):
        return self.inputSelector.currentNode()

    def getCurrentSegmentationNode(self):
        return self.segmentationNodeSelector.currentNode()

    def onInferenceFinished(self, *_):
        if self.isStopping:
            return

        self.stopButton.setVisible(False)
        self.applyButton.setVisible(True)

        try:
            self._loadSegmentationResults()
        except RuntimeError as e:
            slicer.util.errorDisplay(e)

    def _loadSegmentationResults(self):
        currentSegmentation = self.getCurrentSegmentationNode()
        segmentationNode = self.logic.loadCmfSegmentation()
        segmentationNode.SetName(self.getCurrentVolumeNode().GetName() + "_Segmentation")
        if currentSegmentation is not None:
            self._copySegmentationResultsToExistingNode(currentSegmentation, segmentationNode)
        else:
            self.segmentationNodeSelector.setCurrentNode(segmentationNode)
        slicer.app.processEvents()
        self._updateSegmentationLabels()

    @staticmethod
    def _copySegmentationResultsToExistingNode(currentSegmentation, segmentationNode):
        currentName = currentSegmentation.GetName()
        currentSegmentation.Copy(segmentationNode)
        currentSegmentation.SetName(currentName)
        slicer.mrmlScene.RemoveNode(segmentationNode)

    def _updateSegmentationLabels(self):
        segmentationNode = self.getCurrentSegmentationNode()
        if not segmentationNode:
            return

        segmentation = segmentationNode.GetSegmentation()
        segmentIds = [segmentation.GetNthSegmentID(i) for i in range(segmentation.GetNumberOfSegments())]

        labels = [
            k for k, v in
            sorted(self.logic.getSegmentationLabels().items(), key=lambda x: x[1]) if
            k != "background"
        ]

        for segmentId, label in zip(segmentIds, labels):
            segmentation.GetSegment(segmentId).SetName(label)

    def onInferenceError(self, errorMsg):
        if self.isStopping:
            return

        slicer.util.errorDisplay("Encountered error during inference :\n" + errorMsg)
