import slicer
from slicer.ScriptedLoadableModule import *
from slicer.i18n import tr, translate
from slicer.util import VTKObservationMixin

from CMFSegmentatorLib import SegmentationLogic, PythonDependencyChecker, SegmentationWidget


class CMFSegmentator(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = tr("CMFSegmentator")
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []
        self.parent.contributors = []

        self.parent.helpText = tr(
            "This module provides an AI segmentation tool for cranio-maxillofacial "
            "CT scans based on a nnUNet model.")
        self.parent.acknowledgementText = tr(
            "This file was originally developed for the "
            '<a href="https://orthodontie-ffo.org/">Fédération Française d\'Orthodonthie</a> '
            "(FFO) for the analysis of cranio-maxillofacial data"
        )


class CMFSegmentatorWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent=None) -> None:
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.logic = SegmentationLogic()

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)
        self.layout.addWidget(
            SegmentationWidget() if PythonDependencyChecker.areDependenciesSatisfied()
            else PythonDependencyChecker.downloadDependencyWidget()
        )
        self.layout.addStretch()


class CMFSegmentatorTest(ScriptedLoadableModuleTest):
    def runTest(self):
        try:
            from SlicerPythonTestRunnerLib import RunnerLogic, RunnerWidget, RunSettings
            from pathlib import Path
        except ImportError:
            slicer.util.warningDisplay("Please install SlicerPythonTestRunner extension to run the self tests.")
            return

        slicer.mrmlScene.Clear()

        currentDirTest = Path(__file__).parent.joinpath("Testing")
        results = RunnerLogic().runAndWaitFinished(currentDirTest, RunSettings(
            extraPytestArgs=RunSettings.pytestFileFilterArgs("*TestCase.py")
        ))

        if results.failuresNumber:
            slicer.util.errorDisplay(f"Test failed :\n{results.getFailingCasesString()}")
        else:
            slicer.util.delayDisplay("Test OK")
