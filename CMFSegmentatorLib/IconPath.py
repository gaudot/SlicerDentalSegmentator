from pathlib import Path

import qt


def iconPath(icon_name) -> str:
    return Path(__file__).parent.joinpath("..", "Resources", "Icons", icon_name).as_posix()


def icon(icon_name) -> "qt.QIcon":
    return qt.QIcon(iconPath(icon_name))
