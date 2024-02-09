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

    def downloadDependenciesIfNeeded(self):
        if self.dependencyChecked:
            return

        progressDialog = slicer.util.createProgressDialog(maximum=0)
        progressDialog.setCancelButton(None)
        self.dependencyChecked = True

        try:
            if self.areDependenciesSatisfied():
                return

            progressDialog.labelText = "Installing PyTorch..."
            slicer.app.processEvents()

            # nnUNet requires at least PyTorch version 2.0 to work (otherwise, inference will return torch._dynamo
            # import error).
            slicer.util.pip_install('light-the-torch>=0.5')

            args = [
                "install",
                "torch>=2.0.0",
                f"--pytorch-computation-backend=cu118"
            ]
            slicer.util._executePythonModule('light_the_torch', args)  # noqa

            progressDialog.labelText = "Installing nnunetv2"
            slicer.app.processEvents()
            slicer.util.pip_install("nnunetv2==2.2.1")
        finally:
            progressDialog.close()
