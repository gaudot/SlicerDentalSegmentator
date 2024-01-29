import qt


def createButton(name, callback=None, isCheckable=False):
  """Helper function to create a button with a text, callback on click and checkable status

  Parameters
  ----------
  name: str
    Label of the button
  callback: Callable
    Called method when button is clicked
  isCheckable: bool
    If true, the button will be checkable

  Returns
  -------
  QPushButton
  """
  button = qt.QPushButton(name)
  if callback is not None:
    button.connect("clicked(bool)", callback)
  button.setCheckable(isCheckable)
  return button