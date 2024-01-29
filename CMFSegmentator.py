import logging
from typing import Optional

import qt
import slicer
import vtk
from slicer import vtkMRMLScalarVolumeNode
from slicer.ScriptedLoadableModule import *
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
)
from slicer.util import VTKObservationMixin

from CMFSegmentatorLib import SegmentationLogic
from CMFSegmentatorLib.Utils import createButton


#
# CMFSegmentator
#


class CMFSegmentator(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("CMFSegmentator")
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []
        self.parent.contributors = []
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This module provides an AI segmentation tool for cranio-maxillofacial CT scans based on a nnUNet model.
""")
        self.parent.acknowledgementText = _("""
This file was originally developed for the <a href="https://orthodontie-ffo.org/">Fédération Française d'Orthodonthie</a> (FFO) for the analysis of cranio-maxillofacial data
""")


class PythonDependencyChecker(object):
    """
    Class responsible for installing the Modules dependencies
    """

    @classmethod
    def areDependenciesSatisfied(cls):
        try:
            import torch
            import nnunetv2
            return True
        except ImportError:
            return False

    @classmethod
    def installDependenciesIfNeeded(cls, progressDialog=None):
        if cls.areDependenciesSatisfied():
            return

        progressDialog = progressDialog or slicer.util.createProgressDialog(maximum=0)
        progressDialog.labelText = "Installing PyTorch"

        try:
            # Try to install the best available pytorch version for the environment using the PyTorch Slicer extension
            import PyTorchUtils
            PyTorchUtils.PyTorchUtilsLogic().installTorch()
        except ImportError:
            # Fallback on default torch available on PIP
            slicer.util.pip_install("torch")

        progressDialog.labelText = "Installing nnunetv2"
        slicer.util.pip_install("nnunetv2")


#
# CMFSegmentatorParameterNode
#


@parameterNodeWrapper
class CMFSegmentatorParameterNode:
    """
    The parameters needed by module.

    inputVolume - The input volume that will be segmented.
    segmentedVolume - The output volume that will contain the segmented volume.
    """

    inputVolume: vtkMRMLScalarVolumeNode
    segmentedVolume: vtkMRMLScalarVolumeNode


#
# CMFSegmentatorWidget
#


class CMFSegmentatorWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        if not PythonDependencyChecker.areDependenciesSatisfied():
            error_msg = "Pytorch and nnUNetv2 are required by this plugin.\n" \
                        "Please click on the Download button below to download and install these dependencies." \
                        "(This may take several minutes)"
            self.layout.addWidget(qt.QLabel(error_msg))
            downloadDependenciesButton = createButton("Download dependencies and restart",
                                                      self.downloadDependenciesAndRestart)
            self.layout.addWidget(downloadDependenciesButton)
            self.layout.addStretch()
            return

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/CMFSegmentator.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = CMFSegmentatorLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # Buttons
        self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def downloadDependenciesAndRestart(self):
        progressDialog = slicer.util.createProgressDialog(maximum=0)

        extensionManager = slicer.app.extensionsManagerModel()
        if not extensionManager.isExtensionInstalled("PyTorch"):
            progressDialog.labelText = "Installing the PyTorch Slicer extension"
            extensionManager.interactive = False  # avoid popups
            extensionManager.installExtensionFromServer("PyTorch")

        PythonDependencyChecker.installDependenciesIfNeeded(progressDialog)

        slicer.app.restart()

    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        if self.logic is not None:
            self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode

    def setParameterNode(self, inputParameterNode: Optional[CMFSegmentatorParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()

    def _checkCanApply(self, caller=None, event=None) -> None:
        if self._parameterNode and self._parameterNode.inputVolume and self._parameterNode.segmentedVolume:
            self.ui.applyButton.toolTip = _("Run segmentation on input volume")
            self.ui.applyButton.enabled = True
        else:
            self.ui.applyButton.toolTip = _("Select input and output volume nodes")
            self.ui.applyButton.enabled = False

    def onApplyButton(self) -> None:
        """Run processing when user clicks "Apply" button."""
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            # Compute output
            self.logic.runSegmentation(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode())


#
# CMFSegmentatorLogic
#


class CMFSegmentatorLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)
        self.segmentationLogic = SegmentationLogic()

    def getParameterNode(self):
        return CMFSegmentatorParameterNode(super().getParameterNode())

    def runSegmentation(self,
                        inputVolume: vtkMRMLScalarVolumeNode,
                        outputVolume: vtkMRMLScalarVolumeNode) -> None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        """

        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time

        startTime = time.time()
        logging.info("Processing started")

        self.segmentationLogic.runCmfSegmentation(inputVolume)

        stopTime = time.time()
        logging.info(f"Processing completed in {stopTime - startTime:.2f} seconds")


#
# CMFSegmentatorTest
#


class CMFSegmentatorTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_CMFSegmentator1()

    def test_CMFSegmentator1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """
        self.delayDisplay("No test implemented")
