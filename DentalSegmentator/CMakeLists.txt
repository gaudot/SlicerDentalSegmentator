#-----------------------------------------------------------------------------
set(MODULE_NAME DentalSegmentator)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  DentalSegmentatorLib/__init__.py
  DentalSegmentatorLib/IconPath.py
  DentalSegmentatorLib/PythonDependencyChecker.py
  DentalSegmentatorLib/SegmentationLogic.py
  DentalSegmentatorLib/SegmentationWidget.py
  DentalSegmentatorLib/Signal.py
  DentalSegmentatorLib/Utils.py
  Testing/__init__.py
  Testing/PythonDependencyCheckerTestCase.py
  Testing/SegmentationLogicTestCase.py
  Testing/SegmentationWidgetTestCase.py
  Testing/Utils.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/Icons/DentalSegmentator_full_icon.png
  Resources/Icons/info.png
  Resources/Icons/loading.gif
  Resources/Icons/start_icon.png
  Testing/Data/PostDentalSurgery_Segmentation.nii.gz
  Testing/Data/PostDentalSurgery_Segmentation_1_3_5.nii.gz
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)
endif()