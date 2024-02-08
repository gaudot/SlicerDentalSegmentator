import qt


def createButton(name, callback=None, isCheckable=False, icon=None, toolTip="", parent=None):
    """Helper function to create a button with a text, callback on click and checkable status

    :param name: Text of the button
    :param callback: Callback called on click if not None
    :param isCheckable: When True, button can be checked (click will send check state)
    :param icon: QIcon to use for button
    :param toolTip: Tooltip displayed when hovering button
    :param qtProperty: Optional list of property name and property value to set to button
    :param parent: QWidget parent of this button

    :returns: QPushButton
    """
    button = qt.QPushButton(name, parent)
    if callback is not None:
        button.connect("clicked(bool)", callback)
    if icon:
        button.setIcon(icon)
    button.setCheckable(isCheckable)
    button.setToolTip(toolTip)
    return button
