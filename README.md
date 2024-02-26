# Slicer Dental Segmentator

## Table of contents

* [Introduction](#introduction)
* [Using the extension](#using-the-extension)
* [Troubleshooting](#troubleshooting)
* [Contributing](#contributing)

## Introduction

This module allows to segment CT and CBCT dental volumes.
It was developed by the AP-HP, Arts et metiers and financed by the FFO (Fédération Française d'Orthodonthie).

After loading and selecting the volume to process, this module generates the following segmentations : 
* "Maxilla & Upper Skull"
* "Mandible"
* "Upper Teeth"
* "Lower Teeth"
* "Mandibular canal"

## Using the extension

This extension is compatible with 3D Slicer 5.6.1 and later versions.
To install the extension, navigate to `Edit>Application Settings>Modules` and drag and drop the folder containing
the `DentalSegmentator.py` file in the `Additional module paths` area. Restart 3D Slicer as prompted.

After the restart, the extension can be found in the module file explorer under `Segmentation>DentalSegmentator`.
It can also be found by using the `find` module button and searching for the keyword `DentalSegmentator`.

To use the extension, load a dental CT or CBCT by either drag and dropping the data in 3D Slicer or by using the
`DATA` or `DCM` load buttons.

After loading the data, the data will be displayed in the 2D views.

Switch module to the `DentalSegmentator` module and select the patient in the first drop down menu.

Click on the `Apply` button to start the segmentation.

During the first launch, the module's dependencies will be installed. These dependencies include : 
* Light the torch
* PyTorch
* nnUNet V2 

After the install, the volume will be transferred and sent to the nnUNet V2 library for processing.
If your device doesn't include CUDA, the processing may be very long and a dialog will ask for confirmation before
starting the segmentation process.

After the segmentation process has run, the segmentation will be loaded into the application.
The segmentation results can be modified using the `Segment Editor` tools.

The segmentation can be exported using the `Export segmentation` menu and selecting the export format to use.

The `Surface smoothing` slider allows to change the 3D view surface smoothing algorithm.

## Troubleshooting

On Linux or WSL system, the inference can get stuck at the stage : "done with volume".
This indicates that the process has run out of memory. 32 GB of RAM is recommended to run this extension. If you run 
into this issue, you can create a SWAP file on SSD with 16 GB which should solve the problem.

## Contributing

This project welcomes contributions. If you want more information about how you can contribute, please refer to
the [CONTRIBUTING.md file](CONTRIBUTING.md).
