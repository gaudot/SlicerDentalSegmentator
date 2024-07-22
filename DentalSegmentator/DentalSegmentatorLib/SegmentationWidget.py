from enum import Flag, auto
from pathlib import Path

import SegmentEditorEffects
import ctk
import numpy as np
import qt
import slicer

from .IconPath import icon, iconPath
from .PythonDependencyChecker import PythonDependencyChecker, hasInternetConnection
from .Utils import (
    createButton,
    addInCollapsibleLayout,
    set3DViewBackgroundColors,
    setConventionalWideScreenView,
    setBoxAndTextVisibilityOnThreeDViews,
)


class ExportFormat(Flag):
    OBJ = auto()
    STL = auto()
    NIFTI = auto()
    GLTF = auto()


class SegmentationWidget(qt.QWidget):
    def __init__(self, logic=None, parent=None):
        super().__init__(parent)
        self.logic = logic or self._createSlicerSegmentationLogic()
        self._prevSegmentationNode = None
        self._minimumIslandSize_mm3 = 60

        self.inputSelector = slicer.qMRMLNodeComboBox(self)
        self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.inputSelector.addEnabled = False
        self.inputSelector.showHidden = False
        self.inputSelector.removeEnabled = False
        self.inputSelector.setMRMLScene(slicer.mrmlScene)
        self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onInputChanged)

        # Configure inference device options
        self.deviceComboBox = qt.QComboBox()
        self.deviceComboBox.addItems(["cuda", "cpu", "mps"])

        # Configure segment editor node selector
        self.segmentationNodeSelector = slicer.qMRMLNodeComboBox(self)
        self.segmentationNodeSelector.nodeTypes = ["vtkMRMLSegmentationNode"]
        self.segmentationNodeSelector.selectNodeUponCreation = True
        self.segmentationNodeSelector.addEnabled = True
        self.segmentationNodeSelector.removeEnabled = True
        self.segmentationNodeSelector.showHidden = False
        self.segmentationNodeSelector.renameEnabled = True
        self.segmentationNodeSelector.setMRMLScene(slicer.mrmlScene)
        self.segmentationNodeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateSegmentEditorWidget)

        # Override default segment node selector text to be more explicit than "Select Segmentation"
        segmentationSelectorComboBox = self.segmentationNodeSelector.findChild("ctkComboBox")
        segmentationSelectorComboBox.defaultText = "Create new Segmentation on Apply"

        # Create segment editor widget
        self.segmentEditorWidget = slicer.qMRMLSegmentEditorWidget(self)
        self.segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
        self.segmentEditorWidget.setSegmentationNodeSelectorVisible(False)
        self.segmentEditorWidget.setSourceVolumeNodeSelectorVisible(False)
        self.segmentEditorWidget.layout().setContentsMargins(0, 0, 0, 0)
        self.segmentEditorNode = None

        # Find show 3D Button in widget
        self.show3DButton = slicer.util.findChild(self.segmentEditorWidget, "Show3DButton")

        # Create surface smoothing and connect it to show3D button surface smoothing
        smoothingSlider = self.show3DButton.findChild("ctkSliderWidget")
        self.surfaceSmoothingSlider = ctk.ctkSliderWidget(self)
        self.surfaceSmoothingSlider.setToolTip(
            "Higher value means stronger smoothing during closed surface representation conversion."
        )
        self.surfaceSmoothingSlider.decimals = 2
        self.surfaceSmoothingSlider.maximum = 1
        self.surfaceSmoothingSlider.singleStep = 0.1
        self.surfaceSmoothingSlider.setValue(smoothingSlider.value)
        self.surfaceSmoothingSlider.tracking = False
        self.surfaceSmoothingSlider.valueChanged.connect(smoothingSlider.setValue)

        # Export Widget
        exportWidget = qt.QWidget()
        exportLayout = qt.QFormLayout(exportWidget)
        self.stlCheckBox = qt.QCheckBox(exportWidget)
        self.stlCheckBox.setChecked(True)
        self.objCheckBox = qt.QCheckBox(exportWidget)
        self.niftiCheckBox = qt.QCheckBox(exportWidget)
        self.gltfCheckBox = qt.QCheckBox(exportWidget)
        self.reductionFactorSlider = ctk.ctkSliderWidget()
        self.reductionFactorSlider.maximum = 1.0
        self.reductionFactorSlider.value = 0.9
        self.reductionFactorSlider.singleStep = 0.01
        self.reductionFactorSlider.toolTip = (
            "Decimation factor determining how much the mesh complexity will be reduced. "
            "Higher value means stronger reduction (smaller files, less details preserved)."
        )

        exportLayout.addRow("Export STL", self.stlCheckBox)
        exportLayout.addRow("Export OBJ", self.objCheckBox)
        exportLayout.addRow("Export NIFTI", self.niftiCheckBox)
        exportLayout.addRow("Export glTF", self.gltfCheckBox)
        exportLayout.addRow("glTF reduction factor :", self.reductionFactorSlider)
        exportLayout.addRow(createButton("Export", callback=self.onExportClicked, parent=exportWidget))

        layout = qt.QVBoxLayout(self)
        self.inputWidget = qt.QWidget(self)
        inputLayout = qt.QFormLayout(self.inputWidget)
        inputLayout.setContentsMargins(0, 0, 0, 0)
        inputLayout.addRow(self.inputSelector)
        inputLayout.addRow(self.segmentationNodeSelector)
        inputLayout.addRow("Device:", self.deviceComboBox)
        layout.addWidget(self.inputWidget)

        self.applyButton = createButton(
            "Apply",
            callback=self.onApplyClicked,
            toolTip="Click to run the segmentation.",
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
            toolTip="Click to Stop the segmentation."
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

        surfaceSmoothingLayout = qt.QFormLayout()
        surfaceSmoothingLayout.setContentsMargins(0, 0, 0, 0)
        surfaceSmoothingLayout.addRow("Surface smoothing :", self.surfaceSmoothingSlider)
        layout.addLayout(surfaceSmoothingLayout)
        layout.addWidget(exportWidget)
        addInCollapsibleLayout(exportWidget, layout, "Export segmentation", isCollapsed=False)
        layout.addStretch()

        self.isStopping = False

        self._dependencyChecker = PythonDependencyChecker()
        self.processedVolumes = {}

        self.onInputChanged()
        self.updateSegmentEditorWidget()
        self.sceneCloseObserver = slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onSceneChanged)
        self.onSceneChanged(doStopInference=False)
        self._connectSegmentationLogic()

    def __del__(self):
        slicer.mrmlScene.RemoveObserver(self.sceneCloseObserver)
        super().__del__()

    def onSceneChanged(self, *_, doStopInference=True):
        if doStopInference:
            self.onStopClicked()
        self.segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
        self.segmentEditorWidget.setMRMLSegmentEditorNode(self.segmentEditorNode)
        self.processedVolumes = {}
        self._prevSegmentationNode = None
        self._initSlicerDisplay()

    @staticmethod
    def _initSlicerDisplay():
        """
        Initialize 3D Slicer's display with white background and no 3D Cube / labels.
        """
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
        self.logic.stopSegmentation()
        self.logic.waitForSegmentationFinished()
        slicer.app.processEvents()
        self.isStopping = False
        self._setApplyVisible(True)

    def onApplyClicked(self, *_):
        """
        On apply, clear the output log infos, hide apply button, install dependencies and start the segmentation process
        """
        if not self.isNNUNetModuleInstalled() or self.logic is None:
            slicer.util.errorDisplay(
                "This module depends on the NNUNet module."
                " Please install the NNUNet module and restart to proceed."
            )
            return

        self.currentInfoTextEdit.clear()
        self._setApplyVisible(False)
        if not self._installNNUNetIfNeeded():
            self._setApplyVisible(True)
            return

        if not self._dependencyChecker.downloadWeightsIfNeeded(self.onProgressInfo):
            self._setApplyVisible(True)
            return

        self._runSegmentation()

    def _setApplyVisible(self, isVisible):
        """
        Toggles visibility of the apply / stop buttons and make sure the selectors are disabled when running
        segmentation.
        """
        self.applyWidget.setVisible(isVisible)
        self.stopWidget.setVisible(not isVisible)
        self.inputWidget.setEnabled(isVisible)

    def _runSegmentation(self):
        """
        Make sure the dependencies are available and user is aware CPU process may take time if current install doesn't
        support CUDA before starting the actual segmentation from the logic object.
        """
        from SlicerNNUNetLib import Parameter

        parameter = Parameter(folds="0", modelPath=self.nnUnetFolder(), device=self.deviceComboBox.currentText)
        if not parameter.isSelectedDeviceAvailable():
            deviceName = parameter.device.upper()
            ret = qt.QMessageBox.question(
                self,
                f"{deviceName} device not available",
                f"Selected device ({deviceName}) is not currently available on your system and will "
                "default to CPU device.\n"
                "Running the segmentation may take up to 1 hour.\n"
                "Would you like to proceed?"
            )
            if ret == qt.QMessageBox.No:
                self._setApplyVisible(True)
                return

        slicer.app.processEvents()
        self.logic.setParameter(parameter)
        self.logic.startSegmentation(self.getCurrentVolumeNode())

    def onInputChanged(self, *_):
        """
        When changing the input, update the apply button enable status and restore previous segmentation if any.
        """
        volumeNode = self.getCurrentVolumeNode()
        self.applyButton.setEnabled(volumeNode is not None)
        slicer.util.setSliceViewerLayers(background=volumeNode)
        slicer.util.resetSliceViews()
        self._restoreProcessedSegmentation()

    def _restoreProcessedSegmentation(self):
        """
        Restore the previous segmentation based on the currently selected volume node.
        """
        segmentationNode = self.processedVolumes.get(self.getCurrentVolumeNode())
        self.segmentationNodeSelector.setCurrentNode(segmentationNode)

    def _storeProcessedSegmentation(self):
        """
        Save the pair volumeNode / SegmentationNode for future input selector changes.
        """
        volumeNode = self.getCurrentVolumeNode()
        segmentationNode = self.getCurrentSegmentationNode()
        if volumeNode and segmentationNode:
            self.processedVolumes[volumeNode] = segmentationNode

    def updateSegmentEditorWidget(self, *_):
        """
        Update the segment editor status based on the current selected segmentation node.
        Hide previous segmentation node to make visualization smoother.
        """
        if self._prevSegmentationNode:
            self._prevSegmentationNode.SetDisplayVisibility(False)

        segmentationNode = self.getCurrentSegmentationNode()
        self._prevSegmentationNode = segmentationNode
        self._initializeSegmentationNodeDisplay(segmentationNode)
        self.segmentEditorWidget.setSegmentationNode(segmentationNode)
        self.segmentEditorWidget.setSourceVolumeNode(self.getCurrentVolumeNode())

    def _initializeSegmentationNodeDisplay(self, segmentationNode):
        """
        Make sure the current segmentation node has a display node and points to the current volume node.
        Reset the 3D view to default and make sure the segmentation node is visible.
        """
        if not segmentationNode:
            return

        segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(self.getCurrentVolumeNode())
        if not segmentationNode.GetDisplayNode():
            segmentationNode.CreateDefaultDisplayNodes()
            slicer.app.processEvents()

        segmentationNode.SetDisplayVisibility(True)

        # Reset 3D view to fit current segmentation
        layoutManager = slicer.app.layoutManager()
        threeDWidget = layoutManager.threeDWidget(0)
        threeDWidget.threeDView().rotateToViewAxis(3)
        slicer.util.resetThreeDViews()

    def getCurrentVolumeNode(self):
        return self.inputSelector.currentNode()

    def getCurrentSegmentationNode(self):
        return self.segmentationNodeSelector.currentNode()

    def onInferenceFinished(self, *_):
        """
        Restore apply button visibility, load the segmentation results if the inference was not manually stopped.
        """
        if self.isStopping:
            self._setApplyVisible(True)
            return

        try:
            self.onProgressInfo("Loading inference results...")
            self._loadSegmentationResults()
            self.onProgressInfo("Inference ended successfully.")
        except RuntimeError as e:
            slicer.util.errorDisplay(e)
            self.onProgressInfo(f"Error loading results :\n{e}")
        finally:
            self._setApplyVisible(True)

    def _loadSegmentationResults(self):
        """
        Load the segmentation results from the logic segmentation folder. Update the segmentation display names and
        run some simple post-processing on the segmentation.
        """
        currentSegmentation = self.getCurrentSegmentationNode()
        segmentationNode = self.logic.loadSegmentation()
        segmentationNode.SetName(self.getCurrentVolumeNode().GetName() + "_Segmentation")
        if currentSegmentation is not None:
            self._copySegmentationResultsToExistingNode(currentSegmentation, segmentationNode)
        else:
            self.segmentationNodeSelector.setCurrentNode(segmentationNode)
        slicer.app.processEvents()
        self._updateSegmentationDisplay()
        self._postProcessSegments()
        self._storeProcessedSegmentation()

    @staticmethod
    def _copySegmentationResultsToExistingNode(currentSegmentation, segmentationNode):
        """
        Copy the segmentation results from segmentationNode to currentSegmentationNode and remove segmentationNode from
        scene.
        """
        currentName = currentSegmentation.GetName()
        currentSegmentation.Copy(segmentationNode)
        currentSegmentation.SetName(currentName)
        slicer.mrmlScene.RemoveNode(segmentationNode)

    @staticmethod
    def toRGB(colorString):
        color = qt.QColor(colorString)
        return color.redF(), color.greenF(), color.blueF()

    def _updateSegmentationDisplay(self):
        """
        Update the segmentation node display by updating its names, colors, opacities and making sure 3D display is
        activated.
        """
        segmentationNode = self.getCurrentSegmentationNode()
        if not segmentationNode:
            return

        self._initializeSegmentationNodeDisplay(segmentationNode)
        segmentation = segmentationNode.GetSegmentation()
        labels = ["Maxilla & Upper Skull", "Mandible", "Upper Teeth", "Lower Teeth", "Mandibular canal"]
        colors = [self.toRGB(c) for c in ["#E3DD90", "#D4A1E6", "#DC9565", "#EBDFB4", "#D8654F"]]
        opacities = [0.45, 0.45, 1.0, 1.0, 1.0]
        segmentIds = [f"Segment_{i + 1}" for i in range(len(labels))]

        segmentationDisplayNode = self.getCurrentSegmentationNode().GetDisplayNode()
        for segmentId, label, color, opacity in zip(segmentIds, labels, colors, opacities):
            segment = segmentation.GetSegment(segmentId)
            if segment is None:
                continue

            segment.SetName(label)
            segment.SetColor(*color)
            segmentationDisplayNode.SetSegmentOpacity3D(segmentId, opacity)

        self.show3DButton.setChecked(True)
        slicer.util.resetThreeDViews()

    def _postProcessSegments(self):
        """
        Runs Island keep largest, and remove small islands on Maxilla, upper and lower teeth.
        """

        self.onProgressInfo("Post processing results...")
        self._keepLargestIsland("Segment_1")
        self._removeSmallIsland("Segment_3")
        self._removeSmallIsland("Segment_4")
        self.onProgressInfo("Post processing done.")

    def _keepLargestIsland(self, segmentId):
        """
        Keeps largest voxel islands for input segmentId.
        """
        segment = self._getSegment(segmentId)
        if not segment:
            return

        self.onProgressInfo(f"Keep largest region for {segment.GetName()}...")
        self.segmentEditorWidget.setCurrentSegmentID(segmentId)
        effect = self.segmentEditorWidget.effectByName("Islands")
        effect.setParameter("Operation", SegmentEditorEffects.KEEP_LARGEST_ISLAND)
        effect.self().onApply()

    def _removeSmallIsland(self, segmentId):
        """
        Removes small islands for input segmentId.
        """
        segment = self._getSegment(segmentId)
        if not segment:
            return

        self.onProgressInfo(f"Remove small voxels for {segment.GetName()}...")
        self.segmentEditorWidget.setCurrentSegmentID(segmentId)
        voxelSize_mm3 = np.cumprod(self.getCurrentVolumeNode().GetSpacing())[-1]
        minimumIslandSize = int(np.ceil(self._minimumIslandSize_mm3 / voxelSize_mm3))
        effect = self.segmentEditorWidget.effectByName("Islands")
        effect.setParameter("Operation", SegmentEditorEffects.REMOVE_SMALL_ISLANDS)
        effect.setParameter("MinimumSize", minimumIslandSize)
        effect.self().onApply()

    def _getSegment(self, segmentId):
        segmentationNode = self.getCurrentSegmentationNode()
        if not segmentationNode:
            return
        return segmentationNode.GetSegmentation().GetSegment(segmentId)

    def onInferenceError(self, errorMsg):
        """
        Displays error message in case of inference errors if inference was not manually stopped.
        """
        if self.isStopping:
            return

        self._setApplyVisible(True)
        slicer.util.errorDisplay("Encountered error during inference :\n" + errorMsg)

    def onProgressInfo(self, infoMsg):
        """
        Prints progress information in module log console and in separate log dialog.
        """
        infoMsg = self.removeImageIOError(infoMsg)
        self.currentInfoTextEdit.insertPlainText(infoMsg + "\n")
        self.moveTextEditToEnd(self.currentInfoTextEdit)
        self.insertDatedInfoLogs(infoMsg)
        slicer.app.processEvents()

    @staticmethod
    def removeImageIOError(infoMsg):
        """
        Filter out ImageIO error which comes from ITK and is of no interest to current processing.
        """
        return "\n".join([msg for msg in infoMsg.strip().splitlines() if "Error ImageIO factory" not in msg])

    def insertDatedInfoLogs(self, infoMsg):
        now = qt.QDateTime.currentDateTime().toString("yyyy/MM/dd hh:mm:ss.zzz")
        self.fullInfoLogs.extend([f"{now} :: {msgLine}" for msgLine in infoMsg.splitlines()])

    def showInfoLogs(self):
        """
        Displays all logs from previous runs in a separate dialog.
        """
        dialog = qt.QDialog()
        layout = qt.QVBoxLayout(dialog)

        textEdit = qt.QTextEdit()
        textEdit.setReadOnly(True)
        textEdit.append("\n".join(self.fullInfoLogs))
        textEdit.setLineWrapMode(qt.QTextEdit.NoWrap)
        self.moveTextEditToEnd(textEdit)
        layout.addWidget(textEdit)
        dialog.setWindowFlags(qt.Qt.WindowCloseButtonHint)
        dialog.resize(slicer.util.mainWindow().size * .7)
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
            self.gltfCheckBox: ExportFormat.GLTF
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

    def exportSegmentation(self, segmentationNode, folderPath, selectedFormats):
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

        if selectedFormats & ExportFormat.GLTF:
            self._exportToGLTF(segmentationNode, folderPath)

    def _exportToGLTF(self, segmentationNode, folderPath, tryInstall=True):
        """
        Export input segmentation node to glTF format.
        Export relies on the SlicerOpenAnatomy extension. If extension is not available, export will try to install it
        provided an internet connection is available.

        Otherwise, export will fail and will ask users to install the extension manually to proceed.
        """
        try:
            from OpenAnatomyExport import OpenAnatomyExportLogic

            logic = OpenAnatomyExportLogic()
            shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
            segmentationItem = shNode.GetItemByDataNode(self.segmentationNodeSelector.currentNode())
            logic.exportModel(segmentationItem, folderPath, self.reductionFactorSlider.value, "glTF")
        except ImportError:
            if not tryInstall or not hasInternetConnection():
                slicer.util.errorDisplay(
                    f"Failed to export to glTF. Try installing the SlicerOpenAnatomy extension manually to continue."
                )
                return
            self._installOpenAnatomyExtension()
            self._exportToGLTF(segmentationNode, folderPath, tryInstall=False)

    @classmethod
    def _installOpenAnatomyExtension(cls):
        # Install extension from extension manager
        extensionManager = slicer.app.extensionsManagerModel()
        extensionManager.setInteractive(False)
        extName = "SlicerOpenAnatomy"
        if extensionManager.isExtensionInstalled(extName):
            return

        success = extensionManager.installExtensionFromServer(extName, False, False)
        if not success:
            return

        # If install was successful, load the open anatomy export module to be used by the exporter
        moduleName = "OpenAnatomyExport"
        modulePath = extensionManager.extensionModulePaths(extName)[0] + f"/{moduleName}.py"
        factory = slicer.app.moduleManager().factoryManager()
        factory.registerModule(qt.QFileInfo(modulePath))
        factory.loadModules([moduleName])

    @staticmethod
    def isNNUNetModuleInstalled():
        try:
            import SlicerNNUNetLib
            return True
        except ImportError:
            return False

    def _installNNUNetIfNeeded(self) -> bool:
        from SlicerNNUNetLib import InstallLogic
        logic = InstallLogic()
        logic.progressInfo.connect(self.onProgressInfo)
        return logic.setupPythonRequirements()

    def _createSlicerSegmentationLogic(self):
        if not self.isNNUNetModuleInstalled():
            return None

        from SlicerNNUNetLib import SegmentationLogic
        return SegmentationLogic()

    def _connectSegmentationLogic(self):
        if self.logic is None:
            return

        self.logic.progressInfo.connect(self.onProgressInfo)
        self.logic.errorOccurred.connect(self.onInferenceError)
        self.logic.inferenceFinished.connect(self.onInferenceFinished)

    @classmethod
    def nnUnetFolder(cls) -> Path:
        fileDir = Path(__file__).parent
        return fileDir.joinpath("..", "Resources", "ML").resolve()
