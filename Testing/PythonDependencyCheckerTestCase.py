from DentalSegmentatorLib import PythonDependencyChecker
from Testing.Utils import DentalSegmentatorTestCase
import qt


class PythonDependencyCheckerTestCase(DentalSegmentatorTestCase):
    def setUp(self):
        super().setUp()
        self.tmpDir = qt.QTemporaryDir()

    def test_can_auto_download_weights(self):
        deps = PythonDependencyChecker(destWeightFolder=self.tmpDir.path())
        self.assertTrue(deps.areWeightsMissing())
        deps.downloadWeights(lambda *_: None)
        self.assertFalse(deps.areWeightsMissing())
        self.assertFalse(deps.areWeightsOutdated())

    def test_can_update_weights(self):
        deps = PythonDependencyChecker(destWeightFolder=self.tmpDir.path())
        deps.downloadWeights(lambda *_: None)
        deps.writeDownloadInfoURL("outdated_url")
        self.assertFalse(deps.areWeightsMissing())
        self.assertTrue(deps.areWeightsOutdated())
        deps.downloadWeights(lambda *_: None)
        self.assertFalse(deps.areWeightsOutdated())
