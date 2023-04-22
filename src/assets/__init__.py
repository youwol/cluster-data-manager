"""Assets.

Export KnownAssets, a enumeration of known assets, and function copy_asset_to_file(KnownAssets, Path).
"""

from .utils import Assets as KnownAssets, copy_to_file as copy_asset_to_file

__all__ = ['KnownAssets', 'copy_asset_to_file']
