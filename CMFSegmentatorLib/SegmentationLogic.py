import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import slicer
from MRMLCorePython import vtkMRMLScalarVolumeNode, vtkMRMLSegmentationNode


class SegmentationLogic:
    def __init__(self):
        fileDir = Path(__file__).parent
        mlResourcesDir = fileDir.joinpath("..", "Resources", "ML").resolve()
        assert mlResourcesDir.exists()

        # dir containing the result of the nnunet experiment (weight checkpoints, dataset.json, plans.json, ...)
        self._nnunet_results_folder = mlResourcesDir.joinpath("CMFSegmentationModel")
        assert self._nnunet_results_folder.exists()

    def runCmfSegmentation(self, volumeNode: vtkMRMLScalarVolumeNode) -> vtkMRMLSegmentationNode:
        """Run the segmentation on a slicer volumeNode, get the result as a segmentationNode"""
        with self._temporarySegmentationDir(volumeNode) as tmp:
            inDir, outDir = tmp
            self.run_nnUNetV2_inference(
                input_dir=inDir,
                output_dir=outDir,
            )
            return slicer.util.loadSegmentation(self._outFile(outDir))

    def run_nnUNetV2_inference(self, input_dir, output_dir, device='cuda', step_size=1.0, disable_tta=True):
        """ Run the nnU-Net V2 inference script

        :param input_dir: dir containing the input volume (.nii.gz)
        :param output_dir: dir containing the output segmentation (.nii.gz)
        :param device: 'cuda' or 'cpu'
        :param step_size: step size for the sliding window. (smaller = slower but more accurate).
         Must not be larger than 1.
        :param disable_tta: Set this flag to disable test time data augmentation in the form of mirroring.
         Faster, but less accurate inference.
        """
        # setup environment variables
        os.environ['nnUNet_preprocessed'] = self._nnunet_results_folder.as_posix()  # not needed, just needs to be an existing directory
        os.environ['nnUNet_raw'] = self._nnunet_results_folder.as_posix()  # not needed, just needs to be an existing directory
        os.environ['nnUNet_results'] = self._nnunet_results_folder.as_posix()

        dataset_name = 'Dataset111_453CT'
        configuration = '3d_fullres'
        fold = 0  # only fold available
        disable_tta_flag = '--disable_tta' if disable_tta else ''
        python_scripts_dir = Path(os.path.dirname(sys.executable)).joinpath("..", "lib", "Python", "Scripts")
        os.environ['PATH'] = os.pathsep.join([python_scripts_dir.as_posix(), os.environ['PATH']])

        # Construct the command for the nnunnet inference script
        command = f'nnUNetv2_predict -i {input_dir} -o {output_dir} -d {dataset_name} -c {configuration} ' \
                  f'-f {fold} {disable_tta_flag} -step_size {step_size} -device {device}'

        # Run the command
        subprocess.run(command, shell=True, env=os.environ)

    @staticmethod
    def _outFile(out_dir: Path) -> str:
        return next(file for file in out_dir.rglob("*.nii*")).as_posix()

    @staticmethod
    @contextmanager
    def _temporarySegmentationDir(volumeNode):
        with TemporaryDirectory() as tmpdir:
            inDir = Path(tmpdir).joinpath("input")
            inDir.mkdir()

            outDir = Path(tmpdir).joinpath("output")
            outDir.mkdir()
            volumePath = inDir.joinpath("volume.nii.gz")
            assert slicer.util.exportNode(volumeNode, volumePath)
            assert volumePath.exists(), "Failed to export volume for segmentation."

            yield inDir, outDir
