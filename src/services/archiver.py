import json
import tarfile
import uuid
from pathlib import Path
from typing import Any

from services.reporting import Report


class Archiver:
    METADATA_FILENAME = "metadata.txt"

    def __init__(self, report: Report, path_work_dir: Path, job_uuid: str):
        self._report = report.get_sub_report("Archiver", init_status="InitializingComponent")
        self._path_work_dir = path_work_dir
        self._job_uuid = job_uuid
        report.set_status("ComponentInitialized")

    def new_archive(self):
        return NewArchive(report=self._report, path_work_dir=self._path_work_dir, job_uuid=self._job_uuid)

    def existing_archive(self, path_archive: Path):
        return ExistingArchive(report=self._report, path_archive=path_archive, path_work_dir=self._path_work_dir)


class NewArchive:

    def __init__(self, report: Report, path_work_dir: Path, job_uuid: str):
        self._items = {}
        self._job_uuid = job_uuid
        self._path_work_dir = path_work_dir
        self._archive_uuid = str(uuid.uuid4())
        self._path_archive = path_work_dir / f"{self._job_uuid}_{self._archive_uuid}.tgz"
        self._metadata = {"version": "v1", "job": self._job_uuid, "archive": self._archive_uuid}
        self._report = report.get_sub_report(f"Archive_{self._archive_uuid}", init_status="ComponentInitialized")

    def _get_path_metadata_file(self):
        return self._path_work_dir / f"{self._job_uuid}_{self._archive_uuid}_{Archiver.METADATA_FILENAME}"

    def _write_metadata(self):
        self._report.get_sub_report("_write_metadata", init_status="in function")
        with open(self._get_path_metadata_file(), mode="tw") as fp_metadata:
            json.dump(self._metadata, fp=fp_metadata)

    def finalize(self):
        report = self._report.get_sub_report("finalize", init_status="in function")
        self._write_metadata()
        with tarfile.open(name=self._path_archive, mode="w:gz") as archive:
            for (archive_item, path) in self._items.items():
                report.notify(f"Adding item {path} as {archive_item}")
                archive.add(path, arcname=archive_item)
            report.notify("Adding metadata informations")
            archive.add(self._get_path_metadata_file(), arcname=Archiver.METADATA_FILENAME)
        report.set_status("exit function")
        return self._path_archive

    def add_dir_item(self, path_dir: Path, archive_item: str):
        self.add_file_item(path_file=path_dir, archive_item=archive_item)

    def add_file_item(self, path_file: Path, archive_item: str):
        self._add_item(path=path_file, archive_item=archive_item)

    def add_metadata(self, key: str, metadata: Any):
        self._metadata[key] = metadata

    def _add_item(self, path: Path, archive_item: str):
        report = self._report.get_sub_report("_add__item", init_status="in function")
        self._items[archive_item] = path
        report.set_status("exit function")


class ExistingArchive:
    def __init__(self, report: Report, path_archive: Path, path_work_dir: Path):
        self._report = report
        self._path_archive = path_archive
        self._path_work_dir = path_work_dir

    def extract_dir_item(self, archive_item: str):
        report = self._report.get_sub_report("extract_dir_item", init_status="in function")
        report.debug(f"extraction {archive_item} in {self._path_work_dir}")
        with tarfile.open(name=self._path_archive, mode="r:gz") as archive:
            item_members = [tarinfo for tarinfo in archive.getmembers() if tarinfo.name.startswith(f"{archive_item}/")]
            archive.extractall(path=self._path_work_dir, members=item_members)
