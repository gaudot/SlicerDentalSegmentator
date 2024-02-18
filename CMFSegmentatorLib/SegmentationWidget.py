import datetime
from enum import Flag, auto
from typing import Optional

import qt
import slicer
from slicer.util import VTKObservationMixin

from .IconPath import icon, iconPath
from .PythonDependencyChecker import PythonDependencyChecker
from .SegmentationLogic import SegmentationLogic, SegmentationLogicProtocol
from .Utils import createButton, addInCollapsibleLayout, set3DViewBackgroundColors, setConventionalWideScreenView, \
    setBoxAndTextVisibilityOnThreeDViews


class ExportFormat(Flag):
    OBJ = auto()
    STL = auto()
    NIFTI = auto()


class SegmentationWidget(qt.QWidget):
    def __init__(self, logic: Optional[SegmentationLogicProtocol] = None, parent=None):
        super().__init__(parent)
        self.logic = logic or SegmentationLogic()
        self._initSlicerDisplay()
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

        # Export Widget
        exportWidget = qt.QWidget()
        exportLayout = qt.QFormLayout(exportWidget)
        self.stlCheckBox = qt.QCheckBox(exportWidget)
        self.stlCheckBox.setChecked(True)
        self.objCheckBox = qt.QCheckBox(exportWidget)
        self.niftiCheckBox = qt.QCheckBox(exportWidget)
        exportLayout.addRow("Export STL", self.stlCheckBox)
        exportLayout.addRow("Export OBJ", self.objCheckBox)
        exportLayout.addRow("Export NIFTI", self.niftiCheckBox)
        exportLayout.addRow(createButton("Export", callback=self.onExportClicked, parent=exportWidget))

        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.inputSelector)
        layout.addWidget(self.segmentationNodeSelector)
        self.applyButton = createButton(
            "Apply",
            callback=self.onApplyClicked,
            toolTip="Click to run the CMF segmentation.",
            icon=icon("start_icon.png")
        )

        self.currentInfoTextEdit = qt.QTextEdit()
        self.currentInfoTextEdit.setReadOnly(True)
        self.currentInfoTextEdit.setLineWrapMode(qt.QTextEdit.NoWrap)
        self.fullInfoLogs = []
        self.stopWidget = qt.QVBoxLayout()

        self.stopButton = createButton(
            "Stop",
            callback=self.onStopClicked,
            toolTip="Click to Stop the CMF segmentation."
        )
        self.stopWidget = qt.QWidget(self)
        stopLayout = qt.QVBoxLayout(self.stopWidget)
        stopLayout.setContentsMargins(0, 0, 0, 0)
        stopLayout.addWidget(self.stopButton)
        stopLayout.addWidget(self.currentInfoTextEdit)
        self.stopWidget.setVisible(False)
        self.loading = qt.QMovie(iconPath("loading.gif"))
        self.loading.setScaledSize(qt.QSize(24, 24))
        self.loading.frameChanged.connect(self._updateStopIcon)
        self.loading.start()

        self.applyWidget = qt.QWidget(self)
        applyLayout = qt.QHBoxLayout(self.applyWidget)
        applyLayout.setContentsMargins(0, 0, 0, 0)
        applyLayout.addWidget(self.applyButton, 1)
        applyLayout.addWidget(
            createButton("", callback=self.showInfoLogs, icon=icon("info.png"), toolTip="Show logs.")
        )

        layout.addWidget(self.applyWidget)
        layout.addWidget(self.stopWidget)
        layout.addWidget(self.segmentEditorWidget)
        layout.addWidget(exportWidget)
        addInCollapsibleLayout(exportWidget, layout, "Export segmentation", isCollapsed=False)

        self.logic.inferenceFinished.connect(self.onInferenceFinished)
        self.logic.errorOccurred.connect(self.onInferenceError)
        self.logic.progressInfo.connect(self.onProgressInfo)
        self.onInputChanged()

        self.isStopping = False

        self.dependencyChecker = PythonDependencyChecker()

    @staticmethod
    def _initSlicerDisplay():
        set3DViewBackgroundColors([1, 1, 1], [1, 1, 1])
        setConventionalWideScreenView()
        setBoxAndTextVisibilityOnThreeDViews(False)

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

        self.stopWidget.setVisible(False)
        self.applyWidget.setVisible(True)

    def onApplyClicked(self, *_):
        self.dependencyChecker.downloadDependenciesIfNeeded()
        self.applyWidget.setVisible(False)
        self.stopWidget.setVisible(True)
        self.currentInfoTextEdit.clear()
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

        self.stopWidget.setVisible(False)
        self.applyWidget.setVisible(True)

        try:
            self.onProgressInfo("Loading inference results...\n")
            self._loadSegmentationResults()
            self.onProgressInfo("Inference ended successfully.\n")
        except RuntimeError as e:
            slicer.util.errorDisplay(e)
            self.onProgressInfo(f"Error loading results {e}\n")

    def _loadSegmentationResults(self):
        currentSegmentation = self.getCurrentSegmentationNode()
        segmentationNode = self.logic.loadCmfSegmentation()
        segmentationNode.SetName(self.getCurrentVolumeNode().GetName() + "_Segmentation")
        if currentSegmentation is not None:
            self._copySegmentationResultsToExistingNode(currentSegmentation, segmentationNode)
        else:
            self.segmentationNodeSelector.setCurrentNode(segmentationNode)
        slicer.app.processEvents()
        self._updateSegmentationDisplay()

    @staticmethod
    def _copySegmentationResultsToExistingNode(currentSegmentation, segmentationNode):
        currentName = currentSegmentation.GetName()
        currentSegmentation.Copy(segmentationNode)
        currentSegmentation.SetName(currentName)
        slicer.mrmlScene.RemoveNode(segmentationNode)

    @staticmethod
    def toRGBF(colorString):
        color = qt.QColor(colorString)
        return color.redF(), color.greenF(), color.blueF()

    def _updateSegmentationDisplay(self):
        segmentationNode = self.getCurrentSegmentationNode()
        if not segmentationNode:
            return

        segmentation = segmentationNode.GetSegmentation()
        segmentIds = [segmentation.GetNthSegmentID(i) for i in range(segmentation.GetNumberOfSegments())]

        labels = ["Maxilla / Upper Skull", "Mandible", "Upper Teeth", "Lower Teeth", "Mandibular canal"]
        colors = [self.toRGBF(c) for c in ["#E3DD90", "#D4A1E6", "#DC9565", "#EBDFB4", "#D8654F"]]
        opacities = [0.45, 0.45, 1.0, 1.0, 1.0]

        segmentationDisplayNode = self.getCurrentSegmentationNode().GetDisplayNode()
        for segmentId, label, color, opacity in zip(segmentIds, labels, colors, opacities):
            segment = segmentation.GetSegment(segmentId)
            segment.SetName(label)
            segment.SetColor(*color)
            segmentationDisplayNode.SetSegmentOpacity3D(segmentId, opacity)

    def onInferenceError(self, errorMsg):
        if self.isStopping:
            return

        slicer.util.errorDisplay("Encountered error during inference :\n" + errorMsg)

    def onProgressInfo(self, infoMsg):
        infoMsg = self.removeImageIOError(infoMsg)
        self.currentInfoTextEdit.insertPlainText(infoMsg)
        self.moveTextEditToEnd(self.currentInfoTextEdit)
        self.insertDatedInfoLogs(infoMsg)
        slicer.app.processEvents()

    @staticmethod
    def removeImageIOError(infoMsg):
        """
        Filter out ImageIO error which comes from ITK and is of no interest to current processing.
        """
        return "\n".join([msg for msg in infoMsg.split("\n") if "Error ImageIO factory" not in msg])

    def insertDatedInfoLogs(self, infoMsg):
        now = qt.QDateTime.currentDateTime().toString("yyyy/MM/dd hh:mm:ss.zzz")
        self.fullInfoLogs.extend([f"{now} :: {msgLine}" for msgLine in infoMsg.split("\n")])

    def showInfoLogs(self):
        dialog = qt.QDialog()
        layout = qt.QVBoxLayout(dialog)

        textEdit = qt.QTextEdit()
        textEdit.setReadOnly(True)
        textEdit.append("\n".join(self.fullInfoLogs))
        textEdit.setLineWrapMode(qt.QTextEdit.NoWrap)
        self.moveTextEditToEnd(textEdit)
        layout.addWidget(textEdit)
        dialog.setWindowFlags(qt.Qt.WindowCloseButtonHint)
        dialog.exec()

    @staticmethod
    def moveTextEditToEnd(textEdit):
        textEdit.verticalScrollBar().setValue(textEdit.verticalScrollBar().maximum)

    def getSelectedExportFormats(self):
        selectedFormats = ExportFormat(0)
        checkBoxes = {
            self.objCheckBox: ExportFormat.OBJ,
            self.stlCheckBox: ExportFormat.STL,
            self.niftiCheckBox: ExportFormat.NIFTI,
        }

        for checkBox, exportFormat in checkBoxes.items():
            if checkBox.isChecked():
                selectedFormats |= exportFormat

        return selectedFormats

    def onExportClicked(self):
        segmentationNode = self.getCurrentSegmentationNode()
        if not segmentationNode:
            slicer.util.warningDisplay("Please select a valid segmentation before exporting.")
            return

        selectedFormats = self.getSelectedExportFormats()
        if selectedFormats == ExportFormat(0):
            slicer.util.warningDisplay("Please select at least one export format before exporting.")
            return

        folderPath = qt.QFileDialog.getExistingDirectory(self, "Please select the export folder")
        if not folderPath:
            return

        with slicer.util.tryWithErrorDisplay(f"Export to {folderPath} failed.", waitCursor=True):
            self.exportSegmentation(segmentationNode, folderPath, selectedFormats)
            slicer.util.infoDisplay(f"Export successful to {folderPath}.")

    @staticmethod
    def exportSegmentation(segmentationNode, folderPath, selectedFormats):
        for closedSurfaceExport in [ExportFormat.STL, ExportFormat.OBJ]:
            if selectedFormats & closedSurfaceExport:
                slicer.vtkSlicerSegmentationsModuleLogic.ExportSegmentsClosedSurfaceRepresentationToFiles(
                    folderPath,
                    segmentationNode,
                    None,
                    closedSurfaceExport.name,
                    True,
                    1.0,
                    False
                )

        if selectedFormats & ExportFormat.NIFTI:
            slicer.vtkSlicerSegmentationsModuleLogic.ExportSegmentsBinaryLabelmapRepresentationToFiles(
                folderPath,
                segmentationNode,
                None,
                "nii.gz"
            )
