import slicer
from slicer.ScriptedLoadableModule import *
from slicer.i18n import tr, translate
from slicer.util import VTKObservationMixin

from DentalSegmentatorLib import SegmentationLogic, SegmentationWidget


class DentalSegmentator(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = tr("DentalSegmentator")
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Segmentation")]
        self.parent.dependencies = []
        self.parent.contributors = [
            "Gauthier DOT (AP-HP)",
            "Laurent GAJNY (ENSAM)",
            "Roman FENIOUX (KITWARE SAS)",
            "Thibault PELLETIER (KITWARE SAS)"
        ]

        self.parent.helpText = tr(
            "Fully automatic AI segmentation tool for Dental CT and CBCT scans based on DentalSegmentator nnU-Net "
            "model."
        )
        self.parent.acknowledgementText = tr(
            "This module was originally developed for the "
            '<a href="https://orthodontie-ffo.org/">Fédération Française d\'Orthodontie</a> '
            "(FFO) for the analysis of dento-maxillo-facial data."
        )


class DentalSegmentatorWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent=None) -> None:
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.logic = SegmentationLogic()

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)
        self.layout.addWidget(SegmentationWidget())
        self.layout.addStretch()


class DentalSegmentatorTest(ScriptedLoadableModuleTest):
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
