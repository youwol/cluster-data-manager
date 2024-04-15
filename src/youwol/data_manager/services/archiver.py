"""Main class and ancillary classes for the archiver service.

The Archiver service should be used to obtain instance of ArchiveCreator (represent and manage a new archive) or
ArchiveExtractor (represent and manage an existing archive).
"""

# standard library
import json
import tarfile
import uuid

from pathlib import Path

# typing
from typing import Any

# relative
from ..configuration import ArchiveItem
from .reporting import Report


class ArchiveCreator:
    """Class used to handle archive creation.

    This class hold information about an archive to be created. References to directories and files to include are
    added using the add_* methods, and all these items will be used tar and compressed into an archive when finalize
    method is called.
    """

    def __init__(self, report: Report, path_work_dir: Path, job_uuid: str):
        """Constructor.

        Args:
            report (Report): logger
            path_work_dir (Path): path of the working directory, where archive will be created.
            job_uuid (str): job UUID, will be used in the archive name.
        """
        self._items: dict[str, Path] = {}
        self._job_uuid = job_uuid
        self._path_work_dir = path_work_dir
        self._archive_uuid = str(uuid.uuid4())
        self._path_archive = (
            path_work_dir / f"{self._job_uuid}_{self._archive_uuid}.tgz"
        )
        self._metadata = {
            "version": "v1",
            "job": self._job_uuid,
            "archive": self._archive_uuid,
        }
        self._report = report.get_sub_report(
            f"Archive_{self._archive_uuid}", init_status="ComponentInitialized"
        )

    def _get_path_metadata_file(self) -> Path:
        return (
            self._path_work_dir
            / f"{self._job_uuid}_{self._archive_uuid}_{ArchiveItem.METADATA.value}"
        )

    def _write_metadata(self) -> None:
        self._report.get_sub_report("_write_metadata", init_status="in function")
        with open(
            self._get_path_metadata_file(), mode="tw", encoding="UTF-8"
        ) as fp_metadata:
            json.dump(self._metadata, fp=fp_metadata)

    def finalize(self) -> Path:
        """Create the archive.

        All items and the metadata are added to a new TAR archive and gzipped.

        Returns:
            Path: The path of the created archive.
        """
        report = self._report.get_sub_report("finalize", init_status="in function")
        self._write_metadata()
        with tarfile.open(name=self._path_archive, mode="w:gz") as archive:
            for archive_item, path in self._items.items():
                report.notify(f"Adding item {path} as {archive_item}")
                archive.add(path, arcname=archive_item)
            report.notify("Adding metadata informations")
            archive.add(
                self._get_path_metadata_file(), arcname=ArchiveItem.METADATA.value
            )
        report.set_status("exit function")
        return self._path_archive

    def add_dir_item(self, path_dir: Path, archive_item: ArchiveItem) -> None:
        """Add a directory entry.

        Add a new directory to the archive to be created.

        Args:
            path_dir (Path): the path of the directory.
            archive_item (str): the name of the item in the archive.

        """
        self.add_file_item(path_file=path_dir, archive_item=archive_item.value)

    def add_file_item(self, path_file: Path, archive_item: str) -> None:
        """Add a file entry.

        Add a new file to the archive to be created.

        Args:
            path_file (Path): the path of the file.
            archive_item (str): the name of the item in the archive.

        """
        self._add_item(path=path_file, archive_item=archive_item)

    def add_metadata(self, key: str, metadata: Any) -> None:
        """Add a metadata entry.

        Add new information to the metadata.

        Args:
            key (str): the key under which the information will be added.
            metadata (Any): information, serializable to json.

        """
        self._metadata[key] = metadata

    def _add_item(self, path: Path, archive_item: str) -> None:
        report = self._report.get_sub_report("_add__item", init_status="in function")
        self._items[archive_item] = path
        report.set_status("exit function")


class ArchiveExtractor:
    """Class used to handle archive expansion.

    This class represent an existing archive, and can be used to extract specific items.
    """

    def __init__(self, report: Report, path_archive: Path, path_work_dir: Path):
        """Constructor.

        Args:
            report (Report): logging.
            path_archive (Path): path of the existing archive.
            path_work_dir (Path): path to the working directory, where extraction will happen.
        """
        self._report = report
        self._path_archive = path_archive
        self._path_work_dir = path_work_dir

    def extract_dir_item(self, archive_item: str) -> None:
        """Extract an item.

        Will extract the item from the archive into the working directory.

        Args:
            archive_item (str): name of the item.
        """
        report = self._report.get_sub_report(
            "extract_dir_item", init_status="in function"
        )
        report.debug(f"extraction {archive_item} in {self._path_work_dir}")
        with tarfile.open(name=self._path_archive, mode="r:gz") as archive:
            item_members = [
                tarinfo
                for tarinfo in archive.getmembers()
                if tarinfo.name.startswith(f"{archive_item}/")
            ]
            archive.extractall(path=self._path_work_dir, members=item_members)

    def metadata(self) -> Any:
        """Metadata.

        Not Implemented.

        Returns:
            dict: an empty dict.
        """
        return {}


class Archiver:
    """Class to instantiate ArchiveCreator or ArchiveExtractor."""

    def __init__(self, report: Report, path_work_dir: Path):
        """Simple constructor.

        Args:
            report (Report): the report
            path_work_dir (Path): the working directory path
            job_uuid (str): the Kubernetes Job uuid
        """
        self._report = report.get_sub_report(
            "Archiver", init_status="InitializingComponent"
        )
        self._path_work_dir = path_work_dir
        report.set_status("ComponentInitialized")

    def new_archive(self, job_uuid: str) -> ArchiveCreator:
        """Get an instance of ArchiveCreator.

        Returns:
            ArchiveCreator: An instance of ArchiveCreator, ready to be used.
        """
        return ArchiveCreator(
            report=self._report,
            path_work_dir=self._path_work_dir,
            job_uuid=job_uuid,
        )

    def existing_archive(self, path_archive: Path) -> ArchiveExtractor:
        """Get an instance on ArchiveExtractor.

        Args:
            path_archive (Path): path the to the existing archive.

        Returns:
            ArchiveExtractor: an instance of ArchiveExtractor, ready to be used.

        """
        return ArchiveExtractor(
            report=self._report,
            path_archive=path_archive,
            path_work_dir=self._path_work_dir,
        )
