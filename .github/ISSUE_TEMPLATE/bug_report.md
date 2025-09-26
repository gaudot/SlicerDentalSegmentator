---
name: Bug report
about: Report problems or unexpected behavior
title: '[BUG] '
labels: type:bug
assignees: ''

---

## Summary

<!-- Provide a concise summary of the issue you're experiencing with SlicerDentalSegmentator. Before submitting, please verify whether the issue persists in the latest Slicer Preview Release. If it does not, the issue may already be resolved. If you're unsure whether this is a bug or a usage error, consider posting on the Slicer Forum: https://discourse.slicer.org -->

## Steps to Reproduce

<!--
To help developers reproduce and resolve the issue, please:
* Describe the exact steps you followed.
* Include expected vs. actual behavior.
* Use sample data from the Sample Data module if possible.
* If using custom data, provide a download link (with all patient identifiers removed).
* If the issue only occurs with custom Python or C++ code, include a minimal reproducible example (see http://sscce.org).

Example format:
1. Load sample data
2. Open Dental Segmentator module => UI loads correctly
3. Click "Apply" => ERROR: No segmentation output
4. Check logs => ERROR: Missing PyTorch model file
-->

## Troubleshooting Checklist

<!-- Please confirm you've tried the [troubleshooting steps](https://github.com/gaudot/SlicerDentalSegmentator?tab=readme-ov-file#troubleshooting): -->

- [ ] Verified that the PyTorch extension is installed and functional
- [ ] Confirmed that the model files are present in the expected location
- [ ] Restarted Slicer and reloaded the module after install
- [ ] Tested with sample data provided in the repository
- [ ] Reviewed the logs for Python errors or missing dependencies

## Logs

<!-- Paste the actual logs from the Slicer Python Interactor or Error Log window. Do NOT include screenshots or photos. -->

```
<Insert logs here>
```

## Environment Details

<!-- Provide complete environment information to help diagnose compatibility or dependency issues. -->

- 3D Slicer version: Slicer-?.?.?-YYYY-MM-DD
- PyTorch version (from PyTorch extension): x.x.x
- Operating system: Windows / macOS / Linux (include version and architecture)
- GPU (if applicable): <e.g., NVIDIA RTX 3080>
