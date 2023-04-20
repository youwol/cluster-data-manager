"""Main class and ancillary classes for service google_drive."""
import datetime
import io
import json
from google.auth.identity_pool import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from pathlib import Path
from typing import Any, Optional

from services.oidc_client import OidcClient
from services.reporting import Report

PAGESIZE = 50


class NonUniqResult(RuntimeError):
    """Simple RuntimeError for multiple results when at most one is expected."""

    def __init__(self):
        super().__init__("Non uniq result")


class FileInformation:
    """Represent Google Drive file informations (id, name and mimeType)."""

    def __init__(self, file_id: str, name: str, mime_type: str):
        self._file_id = file_id
        self._name = name
        self._mime_type = mime_type

    def file_id(self):
        """Sinple getter.

        Returns:
            str: the file ID.
        """
        return self._file_id

    def name(self):
        """Simple getter.

        Returns:
            str: the file name.
        """
        return self._name


class GoogleDrive:
    """Service google_drive."""

    def __init__(self, report: Report, drive_id: str, oidc_client: OidcClient):

        self._report = report.get_sub_report(task="GoogleDrive", init_status="InitializingComponent")
        self._drive_id = drive_id
        self._oidc_client = oidc_client
        self._service = None
        self._report.notify(f"Using drive_id {drive_id}")
        self._report.set_status("ComponentInitialized")

    def account(self) -> dict:
        """Simple getter.

        Returns:
            dict: Account informations
        """
        return {
            "type": "external_service_account",
            "issuer": self._oidc_client.issuer(),
            "client_id": self._oidc_client.client_id(),
        }

    def drive_id(self) -> str:
        """Simple getter.

        Returns:
            str: the drive ID
        """
        return self._drive_id

    def _get_path_oidc_tokens(self) -> Path:
        # TODO: determine a better place for this file ?
        report = self._report.get_sub_report("OidcCredentials")
        path_credentials_source_file = Path("/tmp/oidc_tokens.json")

        if path_credentials_source_file.exists():
            report.notify("found existing file : checking expiration for token")
            file_timestamp = path_credentials_source_file.stat().st_mtime
            tokens = json.loads(path_credentials_source_file.read_text("UTF-8"))
            token_expire_at = file_timestamp + tokens['expires_in']
            if token_expire_at < datetime.datetime.now().timestamp():
                report.notify("existing tokens has expired : removing tokens file")
                path_credentials_source_file.unlink()

        if not path_credentials_source_file.exists():
            report.notify("setup credentials")
            tokens = self._oidc_client.grant_client_credentials_tokens()
            path_credentials_source_file.write_text(json.dumps(tokens), encoding='UTF-8')
            report.notify("done")

        return path_credentials_source_file

    def _get_service(self) -> Any:
        # TODO: handle credentials expiration ?
        if self._service is None:
            report = self._report.get_sub_report("CreatingService")
            report.debug("creating google.auth.identity_pool.Credentials")
            # TODO: do not hardcode these informations
            creds = Credentials.from_info(
                {
                    "type": "external_account",
                    "audience": "//iam.googleapis.com/projects/664035388216/locations/global/workloadIdentityPools/youwol-platform/providers/youwol-int-platform-oidc",
                    "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
                    "token_url": "https://sts.googleapis.com/v1/token",
                    "service_account_impersonation_url": "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/backup-to-google-drive@youwol-services-accounts.iam.gserviceaccount.com:generateAccessToken",
                    "credential_source": {
                        "file": self._get_path_oidc_tokens(),
                        "format": {
                            "type": "json",
                            "subject_token_field_name": "id_token"
                        }
                    }
                }
            )
            report.notify("GoogleCloud credentials defined")

            report.debug("building service drive")
            self._service = build('drive', 'v3', credentials=creds)
            report.set_status("Done")
        return self._service

    def list_archives(self) -> list[FileInformation]:
        """List files in drive of mimeType 'application/x-tar'.

        Notes:
          Pagination is transparently handled by this method.

        Returns:
            [dict]: list of files information
        """
        try:
            files, page_token = self._list_files(request="mimeType='application/x-tar'", page_token=None)
            result = [*files]
            while page_token is not None:
                files, page_token = self._list_files(request="mimeType='application/x-tar'", page_token=page_token)
                result = [*result, *files]
            return result

        except HttpError as error:
            raise RuntimeError(f"listing drive archives failed with HttpError : {error}") from error

    def upload(self, path_local_file: Path, file_name: str, folder_name: str):
        """Upload a local file to a drive file into a drive folder.

        Args:
            path_local_file (Path): input file.
            file_name: destination filename.
            folder_name: destination folder.
        """
        report = self._report.get_sub_report("upload", init_status="in function")
        try:
            folder_id = self._get_folder_id(folder_name)
            report.debug(f"using folder_id {folder_id}")
            if folder_id is None:
                msg = f"No folder named '{folder_name}'"
                report.fatal(msg)
                raise RuntimeError(msg)

            file_id = self._get_file_id_in_folder(file_name, folder_id)
            if file_id is not None:
                msg = f"A file named '{file_name}' already exists in folder '{folder_name}'"
                report.fatal(msg)
                raise RuntimeError(msg)

            media = MediaFileUpload(path_local_file, resumable=True)
            report.set_status("Uploading")
            # pylint: disable=maybe-no-member
            request = self._get_service().files().create(media_body=media, supportsAllDrives=True, fields="id",
                                                         body={'name': file_name, 'parents': [folder_id]})

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    report.notify(f"Uploaded {int(status.progress() * 100):d}%.")

            result = response.get('id')
            report.set_status("Uploaded", level="NOTIFY")
            report.debug(f"file_id={result}")
            report.set_status("exit function")
            return result

        except HttpError as error:
            report.fatal(f"HTTP error '{error}'")
            raise RuntimeError(f"upload file failed with HttpError: {error}") from error

    def download(self, file_id: str, path_file: Path):
        """Download a drive file into a local file.

        Args:
            file_id (str): the file ID.
            path_file: output file.
        """
        report = self._report.get_sub_report("download", init_status="in function")
        try:
            # pylint: disable=maybe-no-member
            request = self._service.files().get_media(fileId=file_id)
            io_file = io.FileIO(file=path_file, mode="x")
            downloader = MediaIoBaseDownload(fd=io_file, request=request)

            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    report.notify(f"Downloaded {int(status.progress() * 100):d}%.")

        except HttpError as error:
            report.fatal(f"HTTP error '{error}'")
            raise RuntimeError(f"listing files failed with HttpError : {error}") from error

    def _get_folder_id(self, folder_name: str) -> Optional[str]:
        try:
            folder_id = self._get_file_id(
                f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}'"
            )
        except HttpError as error:
            raise RuntimeError(f"listing files failed with HttpError : {error}") from error
        except NonUniqResult as error:
            raise RuntimeError(f"More than one folder named '{folder_name}'") from error

        return folder_id

    def _get_file_id_in_folder(self, file_name: str, folder_id: str) -> Optional[str]:
        try:
            file_id = self._get_file_id(
                f"mimeType!='application/vnd.google-apps.folder' and name='{file_name}'and '{folder_id}' in parents"
            )
        except HttpError as error:
            raise RuntimeError(f"listing files failed with HttpError : {error}") from error
        except NonUniqResult as error:
            raise RuntimeError(f"More than one file named '{file_name}'") from error
        return file_id

    def get_archive_id(self, archive_name: str) -> Optional[str]:
        """Get the file Id for an archive.

        Search for the file with provided name and mimeTypes 'application/x-tar'

        Args
            archive_name (str): the archive name.

        Returns:
            Optional[str]: the file ID, or None if not found.
        """
        try:
            archive_id = self._get_file_id(f"mimeType='application/x-tar' and name='{archive_name}'")
        except HttpError as error:
            raise RuntimeError(f"listing files failed with HttpError : {error}") from error
        except NonUniqResult as error:
            raise RuntimeError(f"More than one archive named '{archive_name}'") from error

        return archive_id

    def _list_files(self, request: str, page_token=None) -> tuple[list[FileInformation], str]:
        # pylint: disable=maybe-no-member
        results = self._get_service().files().list(
            q=request,
            corpora="drive",
            driveId=self._drive_id,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            pageSize=PAGESIZE,
            pageToken=page_token,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        files_informations = [FileInformation(f['id'], f['name'], f['mimeType']) for f in (results.get('files', []))]
        return files_informations, results.get('nextPageToken', None)

    def _get_file_id(self, request: str) -> Optional[str]:
        files, next_page_token = self._list_files(request=request)
        if len(files) == 0:
            return None

        if len(files) > 1:
            raise NonUniqResult()

        if next_page_token is not None:
            raise NonUniqResult()

        return files[0].file_id()
