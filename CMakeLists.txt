#-----------------------------------------------------------------------------
set(MODULE_NAME CMFSegmentator)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  CMFSegmentatorLib/__init__.py
  CMFSegmentatorLib/IconPath.py
  CMFSegmentatorLib/PythonDependencyChecker.py
  CMFSegmentatorLib/SegmentationLogic.py
  CMFSegmentatorLib/SegmentationWidget.py
  CMFSegmentatorLib/Signal.py
  CMFSegmentatorLib/Utils.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/Icons/loading.gif
  Resources/Icons/start_icon.png
  Resources/UI/${MODULE_NAME}.ui
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )
