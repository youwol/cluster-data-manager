"""Assets service functions."""
import importlib.resources
import shutil
from enum import Enum
from pathlib import Path


class Assets(Enum):
    """Enumeration of the available assets."""

    KC_EXPORT_SH = "kc_export.sh"


def copy_to_file(asset: Assets, destination: Path) -> None:
    """Copy asset to destination.

    Args:
        asset (Assets): the source asset
        destination (Path): the destination of the copy

    Notes:
        This function use blindly shutil.copy(source, destination), with no check on the destination
    """
    source = importlib.resources.files(__package__) / asset.value
    if source.is_file():
        with importlib.resources.as_file(source) as source_fp:
            shutil.copy(source_fp, destination)
    else:
        raise RuntimeError(f"{source} is not a file")
