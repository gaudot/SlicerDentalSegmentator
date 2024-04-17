import json
import sys
import zipfile
from pathlib import Path

import qt
import slicer
from github import Github, GithubException


class PythonDependencyChecker:
    """
    Class responsible for installing the Modules dependencies
    """

    def __init__(self, repoPath=None, destWeightFolder=None):
        from .SegmentationWidget import SegmentationWidget
        self.dependencyChecked = False
        self.destWeightFolder = Path(destWeightFolder or SegmentationWidget.nnUnetFolder())
        self.repo_path = repoPath or "gaudot/SlicerDentalSegmentator"

    @classmethod
    def areDependenciesSatisfied(cls):
        try:
            import torch
            import nnunetv2
            return True
        except ImportError:
            return False

    def downloadWeightsIfNeeded(self, progressCallback):
        if self.areWeightsMissing():
            return self.downloadWeights(progressCallback)

        elif self.areWeightsOutdated():
            if qt.QMessageBox.question(
                    None,
                    "New weights are available",
                    "New weights are available. Would you like to download them?"
            ):
                return self.downloadWeights(progressCallback)
        return True

    def areWeightsMissing(self):
        return self.getDatasetPath() is None

    def getLatestReleaseUrl(self):
        g = Github()
        repo = g.get_repo(self.repo_path)
        assets = [asset for release in repo.get_releases() for asset in release.get_assets()]
        return assets[0].browser_download_url

    def areWeightsOutdated(self):
        if not self.getWeightDownloadInfoPath().exists():
            return True

        try:
            return self.getLastDownloadedWeights() != self.getLatestReleaseUrl()
        except GithubException:
            return False

    def getDestWeightFolder(self):
        return self.destWeightFolder

    def getDatasetPath(self):
        try:
            return next(self.destWeightFolder.rglob("dataset.json"))
        except StopIteration:
            return None

    def getWeightDownloadInfoPath(self):
        return self.destWeightFolder / "download_info.json"

    def getLastDownloadedWeights(self):
        if not self.getWeightDownloadInfoPath().exists():
            return None

        with open(self.getWeightDownloadInfoPath(), "r") as f:
            return json.loads(f.read()).get("download_url")

    def downloadWeights(self, progressCallback):
        import shutil
        import requests

        progressCallback("Downloading model weights...")
        if self.destWeightFolder.exists():
            shutil.rmtree(self.destWeightFolder)
        self.destWeightFolder.mkdir(parents=True, exist_ok=True)

        try:
            download_url = self.getLatestReleaseUrl()
            session = requests.Session()
            response = session.get(download_url, stream=True)
            response.raise_for_status()

            file_name = download_url.split("/")[-1]
            destZipPath = self.destWeightFolder / file_name
            with open(destZipPath, "wb") as f:
                for chunk in response.iter_content(1024 * 1024):
                    f.write(chunk)

            self.extractWeightsToWeightsFolder(destZipPath)
            self.writeDownloadInfoURL(download_url)
            return True
        except Exception:  # noqa
            import traceback
            slicer.util.errorDisplay(
                "Failed to download weights. Please retry or manually install them to proceed.\n"
                "To manually install the weights, please refer to the documentation here :\n"
                "https://github.com/gaudot/SlicerDentalSegmentator",
                detailedText=traceback.format_exc()
            )
            return False

    def extractWeightsToWeightsFolder(self, zipPath):
        with zipfile.ZipFile(zipPath, "r") as f:
            f.extractall(self.destWeightFolder)

    def writeDownloadInfoURL(self, download_url):
        with open(self.destWeightFolder / "download_info.json", "w") as f:
            f.write(json.dumps({"download_url": download_url}))
