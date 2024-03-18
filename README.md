# Slicer Dental Segmentator

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/1.png" width="800"/>

## Table of contents

* [Introduction](#introduction)
* [Using the extension](#using-the-extension)
* [Troubleshooting](#troubleshooting)
* [Contributing](#contributing)

## Introduction

<div style="text-align:center">
<img class="center" src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/DentalSegmentator/Resources/Icons/DentalSegmentator_full_icon.png"/>
</div>

This module allows to segment CT and CBCT dental volumes.
It was developed by the [AP-HP](https://www.aphp.fr/), [Arts et metiers](https://www.artsetmetiers.fr/fr) and financed 
by the [FFO (Fédération Française d'Orthodonthie)](https://orthodontie-ffo.org/).

After loading and selecting the volume to process, this module generates the following segmentations : 
* "Maxilla & Upper Skull"
* "Mandible"
* "Upper Teeth"
* "Lower Teeth"
* "Mandibular canal"

## Using the extension

This extension is compatible with 3D Slicer 5.6.1 and later versions.

The plugin can be installed in Slicer3D using
the [extension manager]( https://slicer.readthedocs.io/en/latest/user_guide/extensions_manager.html#install-extensions).
It can be found using the search bar by typing "DentalSegmentator".

The extension can also be installed manually from the sources. To install the extension, navigate to 
`Edit>Application Settings>Modules` and drag and drop the folder containing  the `DentalSegmentator.py` file in the 
`Additional module paths` area. Restart 3D Slicer as prompted.

After the restart, the extension can be found in the module file explorer under `Segmentation>DentalSegmentator`.
It can also be found by using the `find` module button and searching for the keyword `DentalSegmentator`.

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/2.png"/>

To use the extension, load a dental CT or CBCT by either drag and dropping the data in 3D Slicer or by using the
`DATA` or `DCM` load buttons.

To test the extension, you can use 3D Slicer's `CBCT Dental Surgery` volumes. These volumes can be found in the
`Sample Data` module.

After loading the data, the data will be displayed in the 2D views.
Switch module to the `DentalSegmentator` module and select the volume in the first drop down menu.

Click on the `Apply` button to start the segmentation.

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/4.png"/>

During the first launch, the module's dependencies will be installed. These dependencies include : 
* The AI model weights
* Light the torch
* PyTorch
* nnUNet V2 

After the install, the volume will be transferred and sent to the nnUNet V2 library for processing.
If your device doesn't include CUDA, the processing may be very long and a dialog will ask for confirmation before
starting the segmentation process.

During execution, the processing can be canceled using the `Stop` button.
The progress will be reported in the console logs.

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/5.png"/>

After the segmentation process has run, the segmentation will be loaded into the application.
The segmentation results can be modified using the `Segment Editor` tools.

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/1.png"/>

The segmentation can be exported using the `Export segmentation` menu and selecting the export format to use.

The `Surface smoothing` slider allows to change the 3D view surface smoothing algorithm.

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/6.png"/>

## Troubleshooting

### Linux Processing hang

On Linux or WSL system, the inference can get stuck at the stage : "done with volume".
This indicates that the process has run out of memory. 32 GB of RAM is recommended to run this extension. If you run 
into this issue, you can create a SWAP file on SSD with 16 GB which should solve the problem.

### Torch CUDA not properly installed

On Windows, the torch CUDA dependency may not properly be detected and installed.

To solve this problem, you can use the `PyTorch Utils` extension, uninstall the version of PyTorch and install 
a new version of PyTorch by setting the `Computation backend` compatible with your hardware.

The PyTorch version should be greater than `2.0.0` for nnUNet compatibility.

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/7.png"/>

### Failed to download / find weights

If the weights are not correctly installed, you can install them manually.
To do so, go to https://github.com/gaudot/SlicerDentalSegmentator  and select the latest release.

Download the latest `.zip` file from the release.

Navigate to your `DentalSegmentator` folder (this folder can be also found in the module finder window).

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/8.png"/>

Unzip the weight file in the `DentalSegmentator\Resources\ML\SegmentationModel` folder.

Create a `download_info.json` file containing the path to the downloaded zip file for future reference : 

{
  "download_url": "https://github.com/gaudot/SlicerDentalSegmentator/releases/download/v1.0.0-alpha/Dataset111_453CT_v100.zip"
}

## Contributing

This project welcomes contributions. If you want more information about how you can contribute, please refer to
the [CONTRIBUTING.md file](CONTRIBUTING.md).
