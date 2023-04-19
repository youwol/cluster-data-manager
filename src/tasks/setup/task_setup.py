"""Main class for setup task."""
import os
from pathlib import Path
from typing import Optional

from services.archiver import Archiver
from services.google_drive import GoogleDrive
from services.reporting import Report


class TaskSetup:
    """Task setup.

    Will download an archive and extract the specified item(s).

    Notes:
      Can be call with or without an archive name: in the latter case the last archive will be downloaded.
    """
    def __init__(self,
                 report: Report,
                 path_work_dir: Path,
                 google_drive: GoogleDrive,
                 archiver: Archiver,
                 extract_items: [str],
                 archive_name: Optional[str] = None
                 ):
        self._path_work_dir = path_work_dir
        self._google_drive = google_drive
        self._archiver = archiver
        self._extract_items = extract_items
        self._archive_name = archive_name
        self._report = report.get_sub_report("Setup", default_status_level="NOTIFY", init_status="ComponentInitialized")

    def run(self):
        """Run setup task : download archive & extract item(s)."""
        if self._archive_name is None:
            self._setup_last_archive()
        else:
            self._setup_explicit_archive(self._archive_name)

    def _setup_last_archive(self):
        archives = self._google_drive.list_archives()

        if len(archives) == 0:
            self._report.warning("No archive found. Skipping setup")
            return

        last_archive = sorted(archives, key=lambda arc: arc.name())[len(archives) - 1]
        self._report.notify(f"using last archive : {last_archive.name()} ({last_archive.file_id()})")
        self.__setup_archive(last_archive.file_id())

    def _setup_explicit_archive(self, archive_name):
        archive_id = self._google_drive.get_archive_id(archive_name)
        if archive_id is None:
            raise RuntimeError(f"Archive named {archive_name} not found in Google Drive")
        self._report.notify(f"using archive : {archive_name}, ({archive_id}")
        self.__setup_archive(archive_id)

    def __setup_archive(self, archive_id):
        path_archive = self._path_work_dir / "setup_archive.tgz"
        self._google_drive.download(archive_id, path_file=path_archive)
        archive = self._archiver.existing_archive(path_archive=path_archive)
        for item in self._extract_items:
            archive.extract_dir_item(item)
        os.unlink(path_archive)
