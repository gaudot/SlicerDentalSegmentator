import json
import zipfile
from pathlib import Path
from typing import Optional, Callable

import qt
import slicer
from github import Github, GithubException


def hasInternetConnection(timeOut_sec=1) -> bool:
    """
    Check if user has access to the internet.
    """
    import requests
    try:
        requests.get("https://www.google.com", timeout=timeOut_sec)
        return True
    except requests.ConnectionError:
        return False


class PythonDependencyChecker:
    """
    Class responsible for installing the Modules dependencies and downloading the model weights.
    """

    def __init__(
            self,
            repoPath: Optional[str] = None,
            destWeightFolder: Optional[Path] = None,
            hasInternetConnectionF: Optional[Callable[[], bool]] = None,
            errorDisplayF=None
    ):
        """
        :param repoPath: Optional path to the github repository from which the weights will be downloaded from.
        :param destWeightFolder: Optional path to where the weights will be saved.
        :param hasInternetConnectionF: Optional function returning True when internet connection is available, False
            otherwise.
        :param errorDisplayF: Optional function used to display error information.
        """
        from .SegmentationWidget import SegmentationWidget
        self.dependencyChecked = False
        self.destWeightFolder = Path(destWeightFolder or SegmentationWidget.nnUnetFolder())
        self.repo_path = repoPath or "gaudot/SlicerDentalSegmentator"
        self.hasInternetConnectionF = hasInternetConnectionF or hasInternetConnection
        self.errorDisplay = errorDisplayF or slicer.util.errorDisplay

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

    def areWeightsOutdated(self) -> bool:
        """
        :returns: True if weights information are missing or internet connection is available and weights information
            don't match the ones on the GitHub page. False otherwise.
        """
        if not self.getWeightDownloadInfoPath().exists():
            return True

        if not self.hasInternetConnectionF():
            return False

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

    def downloadWeights(self, progressCallback) -> bool:
        """
        Removes the weight folder and tries to download the weights from the GitHub page.
        If an internet connection is not available, keeps the current weights unchanged.

        :returns: True if download was successful. False in case of no internet or failure during download.
        """
        import shutil
        import requests

        progressCallback("Downloading model weights...")
        if not self.hasInternetConnectionF():
            self.errorDisplay(
                "Failed to download weights (no internet connection). "
                "Please retry or manually install them to proceed.\n"
                "To manually install the weights, please refer to the documentation here :\n"
                "https://github.com/gaudot/SlicerDentalSegmentator",
            )
            return False

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
            self.errorDisplay(
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
