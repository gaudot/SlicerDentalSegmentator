#-----------------------------------------------------------------------------
set(MODULE_NAME DentalSegmentator)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  ${MODULE_NAME}Lib/__init__.py
  ${MODULE_NAME}Lib/IconPath.py
  ${MODULE_NAME}Lib/PythonDependencyChecker.py
  ${MODULE_NAME}Lib/SegmentationLogic.py
  ${MODULE_NAME}Lib/SegmentationWidget.py
  ${MODULE_NAME}Lib/Signal.py
  ${MODULE_NAME}Lib/Utils.py
  Testing/__init__.py
  Testing/IntegrationTestCase.py
  Testing/SegmentationWidgetTestCase.py
  Testing/Utils.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/Icons/${MODULE_NAME}_full_icon.png
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