# Slicer DentalSegmentator 

3D Slicer extension for fully-automatic segmentation of CT and CBCT dental volumes.

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/1.png" width="700"/>

After loading and selecting the volume to process, this module generates the following segmentations : 
* Maxilla & Upper Skull
* Mandible
* Upper Teeth
* Lower Teeth
* Mandibular canal

## DentalSegmentator model

DentalSegmentator is based on nnU-Net framework. It has been trained on 470 dento-maxillo-facial CT and CBCT scans, and evaluated on a hold-out test dataset of 256 CT and CBCT scans from 7 institutions. 

The results obtained on our highly diversified dataset demonstrate that our tool can provide fully automatic and robust multiclass segmentation for dento-maxillo-facial (CB)CT scans, independantly of the field of view of the scan.

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/dentalsegmentator_example.png" width="500"/>

If you use DentalSegmentator for your work, please cite our paper and nnU-Net:

>Dot G, Chaurasia A, Dubois G, et al. DentalSegmentator: robust deep learning-based CBCT image segmentation. Published online March 18, 2024:2024.03.18.24304458. doi:[10.1101/2024.03.18.24304458](https://doi.org/10.1101/2024.03.18.24304458)

>Isensee F, Jaeger PF, Kohl SAA, Petersen J, Maier-Hein KH. nnU-Net: a self-configuring method for deep learning-based biomedical image segmentation. Nat Methods. 2021;18(2):203-211. doi:[10.1038/s41592-020-01008-z](https://doi.org/10.1038/s41592-020-01008-z)

## Using the extension

This extension is compatible with 3D Slicer 5.7.0 and later versions.

The plugin can be installed in latest Slicer Preview Release (version 5.7.0 - rev32797, or later) using
the [extension manager]( https://slicer.readthedocs.io/en/latest/user_guide/extensions_manager.html#install-extensions).
It can be found using the search bar by typing "DentalSegmentator".

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/extension_manager.png" width="200" />

After the install process and restart of Slicer, the extension can be found in the module file explorer under `Segmentation>DentalSegmentator`.
It can also be found by using the `find` module button and searching for the keyword `DentalSegmentator`.

To use the extension, load a dental CT or CBCT by either drag and dropping the data in 3D Slicer or by using the
`DATA` or `DCM` load buttons.

To test the extension, you can use 3D Slicer's `CBCT Dental Surgery` volumes. These volumes can be found in the
`Sample Data` module.

After loading the data, the data will be displayed in the 2D views.
Switch module to the `DentalSegmentator` module and select the volume in the first drop down menu.

Click on the `Apply` button to start the segmentation.

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/4.png" width="300" />


https://github.com/gaudot/SlicerDentalSegmentator/assets/78350246/703bfaa1-8130-427c-8810-15d3454f510b


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

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/5.png" width="300"/>

After the segmentation process has run, the segmentation will be loaded into the application.
The segmentation results can be modified using the `Segment Editor` tools.

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/1.png" width="600"/>

The segmentation can be exported using the `Export segmentation` menu and selecting the export format to use.

The `Surface smoothing` slider allows to change the 3D view surface smoothing algorithm.

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/6.png" width="300"/>

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

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/7.png" width="300"/>

### Failed to download / find weights

If the weights are not correctly installed, you can install them manually.
To do so, go to https://github.com/gaudot/SlicerDentalSegmentator  and select the latest release.

Download the latest `.zip` file from the release.

Navigate to your `DentalSegmentator` folder (this folder can be also found in the module finder window).

<img src="https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/8.png" width="500"/>

Unzip the weight file in the `DentalSegmentator\Resources\ML\SegmentationModel` folder.

Create a `download_info.json` file containing the path to the downloaded zip file for future reference : 

{
  "download_url": "https://github.com/gaudot/SlicerDentalSegmentator/releases/download/v1.0.0-alpha/Dataset111_453CT_v100.zip"
}

## Command-line interface  

If you want tu use DentalSegmentator via nnU-Net command-line interface use, [the pretrained model is available on Zenodo platform](https://zenodo.org/doi/10.5281/zenodo.10829674).

## Contributing

This project welcomes contributions. If you want more information about how you can contribute, please refer to
the [CONTRIBUTING.md file](CONTRIBUTING.md).

## Acknowledgments 

Authors: G. Dot (Université Paris Cité, AP-HP, Arts-et-Métiers), L. Gajny (Arts-et-Métiers), R. Fenioux (Kitware SAS), T. Pelletier (Kitware SAS)

Supported by the [FFO (Fédération Française d'Orthodontie)](https://orthodontie-ffo.org/) and the [Fondation des Gueules Cassées](https://www.gueules-cassees.asso.fr/).

