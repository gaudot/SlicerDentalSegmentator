import os
import sys
from pathlib import Path
from typing import Protocol

import qt
import slicer

from .Signal import Signal


class SegmentationLogicProtocol(Protocol):
    inferenceFinished: Signal
    errorOccurred: Signal
    progressInfo: Signal

    def startDentalSegmentation(self, volumeNode: "slicer.vtkMRMLScalarVolumeNode") -> None:
        pass

    def stopDentalSegmentation(self):
        pass

    def waitForSegmentationFinished(self):
        pass

    def loadDentalSegmentation(self) -> "slicer.vtkMRMLSegmentationNode":
        pass


class SegmentationLogic:
    def __init__(self):
        self.inferenceFinished = Signal()
        self.errorOccurred = Signal("str")
        self.progressInfo = Signal("str")

        self.inferenceProcess = qt.QProcess()
        self.inferenceProcess.setProcessChannelMode(qt.QProcess.MergedChannels)
        self.inferenceProcess.finished.connect(self.onFinished)
        self.inferenceProcess.errorOccurred.connect(self.onErrorOccurred)
        self.inferenceProcess.readyRead.connect(self.onCheckStandardOutput)

        self._nnUNet_predict_path = None
        self._tmpDir = qt.QTemporaryDir()

    @property
    def _dataSetPath(self):
        return next(self.nnUnetFolder().rglob("dataset.json"))

    @classmethod
    def nnUnetFolder(cls):
        fileDir = Path(__file__).parent
        mlResourcesDir = fileDir.joinpath("..", "Resources", "ML").resolve()
        return mlResourcesDir.joinpath("SegmentationModel")

    def __del__(self):
        self.stopDentalSegmentation()

    def onCheckStandardOutput(self):
        info = bytes(self.inferenceProcess.readAll().data()).decode()
        if info:
            self.progressInfo(info)

    def onErrorOccurred(self, *_):
        self.errorOccurred(bytes(self.inferenceProcess.readAllStandardError().data()).decode())

    def onFinished(self, *_):
        self.inferenceFinished()

    def startDentalSegmentation(self, volumeNode: "slicer.vtkMRMLScalarVolumeNode") -> None:
        """Run the segmentation on a slicer volumeNode, get the result as a segmentationNode"""
        self._stopInferenceProcess()
        self._prepareInferenceDir(volumeNode)
        self._startInferenceProcess()

    def stopDentalSegmentation(self):
        self._stopInferenceProcess()

    def waitForSegmentationFinished(self):
        self.inferenceProcess.waitForFinished(-1)

    def loadDentalSegmentation(self) -> "slicer.vtkMRMLSegmentationNode":
        try:
            return slicer.util.loadSegmentation(self._outFile)
        except StopIteration:
            raise RuntimeError(f"Failed to load the segmentation.\nCheck the inference folder content {self._outDir}")

    def _stopInferenceProcess(self):
        if self.inferenceProcess.state() == self.inferenceProcess.Running:
            self.progressInfo("Stopping previous inference...\n")
            self.inferenceProcess.kill()

    @property
    def nnUNet_predict_path(self):
        if self._nnUNet_predict_path is None:
            self._nnUNet_predict_path = self._findUNetPredictPath()
        return self._nnUNet_predict_path

    @staticmethod
    def _nnUNetPythonDir():
        return Path(sys.executable).parent.joinpath("..", "lib", "Python")

    @classmethod
    def _findUNetPredictPath(cls):
        # nnUNet install dir depends on OS. For Windows, install will be done in the Scripts dir.
        # For Linux and MacOS, install will be done in the bin folder.
        nnUNetPaths = ["Scripts", "bin"]
        for path in nnUNetPaths:
            predict_paths = list(sorted(cls._nnUNetPythonDir().joinpath(path).glob("nnUNetv2_predict*")))
            if predict_paths:
                return predict_paths[0].resolve()

        return None

    def _startInferenceProcess(self, device='cuda', step_size=0.5, disable_tta=True):
        """ Run the nnU-Net V2 inference script

        :param device: 'cuda' or 'cpu'
        :param step_size: step size for the sliding window. (smaller = slower but more accurate).
         Must not be larger than 1.
        :param disable_tta: Set this flag to disable test time data augmentation in the form of mirroring.
         Faster, but less accurate inference.
        """
        import torch

        if not self._dataSetPath.exists():
            self.errorOccurred(
                "nnUNet weights are not correctly installed."
                f" Missing path:\n{self._dataSetPath.as_posix()}"
            )
            return

        # setup environment variables
        # not needed, just needs to be an existing directory
        os.environ['nnUNet_preprocessed'] = self.nnUnetFolder().as_posix()

        # not needed, just needs to be an existing directory
        os.environ['nnUNet_raw'] = self.nnUnetFolder().as_posix()
        os.environ['nnUNet_results'] = self.nnUnetFolder().as_posix()

        if not self.nnUNet_predict_path:
            self.errorOccurred("Failed to find nnUNet predict path.")
            return

        configuration_folder = self._dataSetPath.parent
        configuration = configuration_folder.name
        configuration = configuration.replace("nnUNetTrainer__nnUNetPlans__", "")

        dataset_folder = configuration_folder.parent
        dataset_name = dataset_folder.name
        device = device if torch.cuda.is_available() else "cpu"

        # Construct the command for the nnunnet inference script
        args = [
            "-i", self._inDir.as_posix(),
            "-o", self._outDir.as_posix(),
            "-d", dataset_name,
            "-c", configuration,
            "-f", "0",
            "-step_size", step_size,
            "-device", device
        ]

        if disable_tta:
            args.append("--disable_tta")

        self.progressInfo("nnUNet preprocessing...\n")
        self.inferenceProcess.start(self.nnUNet_predict_path, args, qt.QProcess.Unbuffered | qt.QProcess.ReadOnly)

    @property
    def _outFile(self) -> str:
        return next(file for file in self._outDir.rglob("*.nii*")).as_posix()

    def _prepareInferenceDir(self, volumeNode):
        self._tmpDir.remove()
        self._outDir.mkdir(parents=True)
        self._inDir.mkdir(parents=True)

        # Name of the volume should match expected nnUNet conventions
        self.progressInfo(f"Transferring volume to nnUNet in {self._tmpDir.path()}\n")
        volumePath = self._inDir.joinpath("volume_0000.nii.gz")
        assert slicer.util.exportNode(volumeNode, volumePath)
        assert volumePath.exists(), "Failed to export volume for segmentation."

    @property
    def _outDir(self):
        return Path(self._tmpDir.path()).joinpath("output")

    @property
    def _inDir(self):
        return Path(self._tmpDir.path()).joinpath("input")
