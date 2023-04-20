"""Assets service functions."""
import importlib.resources
import shutil
from pathlib import Path

from services.assets.enum_assets import Assets


def copy_file(asset: Assets, destination: Path):
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
