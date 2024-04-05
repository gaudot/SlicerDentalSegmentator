cmake_minimum_required(VERSION 3.13.4)

project(DentalSegmentator)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/gaudot/SlicerDentalSegmentator")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "Gauthier DOT (AP-HP), Laurent GAJNY (ENSAM), Roman FENIOUX (KITWARE SAS), Thibault PELLETIER (KITWARE SAS)")
set(EXTENSION_DESCRIPTION "Fully automatic AI segmentation tool for Dental CT and CBCT scans based on DentalSegmentator nnU-Net model.")
set(EXTENSION_ICONURL "https://github.com/gaudot/SlicerDentalSegmentator/raw/main/DentalSegmentator/Resources/Icons/DentalSegmentator.png")
set(EXTENSION_SCREENSHOTURLS "https://github.com/gaudot/SlicerDentalSegmentator/raw/main/Screenshots/1.png")
set(EXTENSION_DEPENDS "NNUNet") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(DentalSegmentator)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
