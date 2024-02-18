import sys

import qt
import slicer


class PythonDependencyChecker:
    """
    Class responsible for installing the Modules dependencies
    """

    def __init__(self):
        self.dependencyChecked = False

    @classmethod
    def areDependenciesSatisfied(cls):
        try:
            import torch
            import nnunetv2
            return True
        except ImportError:
            return False

    @staticmethod
    def runPythonProcess(args, progressCallback, stopSignal):
        def onRead():
            progressCallback(bytes(proc.readAll().data()).decode())

        proc = qt.QProcess()
        proc.setProcessChannelMode(qt.QProcess.MergedChannels)
        proc.readyRead.connect(onRead)
        stopSignal.connect(proc.kill)
        proc.start(sys.executable, args, qt.QProcess.Unbuffered | qt.QProcess.ReadWrite)
        while proc.state() == proc.Running:
            slicer.app.processEvents(1000)

    def downloadDependenciesIfNeeded(self, progressCallback, stopSignal):
        if self.dependencyChecked:
            return

        progressCallback("Checking dependencies...")
        if self.areDependenciesSatisfied():
            return

        # nnUNet requires at least PyTorch version 2.0 to work (otherwise, inference will return torch._dynamo
        # import error).
        progressCallback("Installing PyTorch...")
        self.runPythonProcess(["-m", "pip", "install", "light-the-torch>=0.5"], progressCallback, stopSignal)
        self.runPythonProcess(["-m", "light_the_torch", "install", "torch>=2.0.0"], progressCallback, stopSignal)

        progressCallback("Installing nnunetv2")
        self.runPythonProcess(["-m", "pip", "install", "nnunetv2"], progressCallback, stopSignal)
        progressCallback("Dependencies correctly installed.")
        progressCallback("")
