import io
from google.auth.identity_pool import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from pathlib import Path
from typing import Optional

from services.keycloak_client import KeycloakClient
from services.reporting import Report


class GoogleDrive:

    def __init__(self, report: Report, drive_id: str, oidc_client: KeycloakClient):

        self._report = report.get_sub_report(task="GoogleDrive", init_status="InitializingComponent")
        self._drive_id = drive_id
        self._oidc_client = oidc_client
        self._service = None
        self._report.notify(f"Using drive_id {drive_id}")
        self._report.set_status("ComponentInitialized")

    def _get_path_oidc_tokens(self):
        # TODO: determine a better place for this file ?
        report = self._report.get_sub_report("OidcCredentials")
        path_credentials_source_file = Path("/tmp/oidc_tokens.json")

        if not path_credentials_source_file.exists():
            report.notify("setup credentials")
            tokens = self._oidc_client.service_account_tokens()
            path_credentials_source_file.write_text(tokens)
            report.notify("done")

        # TODO: handle id_token expiration

        return path_credentials_source_file

    def _get_service(self):
        # TODO: handle credentials expiration ?
        if self._service is None:
            report = self._report.get_sub_report("CreatingService")
            report.debug("creating google.auth.identity_pool.Credentials")
            # TODO: do not hardcode these informations
            creds = Credentials.from_info({
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
            })
            report.notify("GoogleCloud credentials defined")

            report.debug("building service drive")
            self._service = build('drive', 'v3', credentials=creds)
            report.set_status("Done")
        return self._service

    def list_drive_files(self):
        try:
            results = self._get_service().files().list(pageSize=10, corpora="drive", driveId=self._drive_id,
                                                       supportsAllDrives=True,
                                                       includeItemsFromAllDrives=True,
                                                       fields="nextPageToken, files(id, name, mimeType)").execute()
            items = results.get('files', [])

            if not items:
                print('No files found.')
            else:
                print('Files:')
                for item in items:
                    print(u'{0} ({1}:{2})'.format(item['name'], item['id'], item['mimeType']))

        except HttpError as error:
            # TODO - Handle errors from drive API.
            print(f'An error occurred: {error}')

    def list_archives(self):
        try:
            files, page_token = self._list_archives_page()
            result = [*files]
            while page_token is not None:
                files, page_token = self._list_archives_page(page_token)
                result = [*result, *files]

            return result

        except HttpError as error:
            # TODO - Handle errors from drive API.
            print(f'An error occurred: {error}')

    def _list_archives_page(self, page_token=None):
        results = self._get_service().files().list(q="mimeType='application/x-tar'", pageSize=10, corpora="drive",
                                                   driveId=self._drive_id,
                                                   supportsAllDrives=True,
                                                   includeItemsFromAllDrives=True,
                                                   fields="nextPageToken, files(id, name, mimeType)",
                                                   pageToken=page_token).execute()
        return results.get('files', []), results.get('nextPageToken', None)

    def upload(self, path_local_file: Path, file_name: str, folder_name: str):
        report = self._report.get_sub_report("upload", init_status="in function")
        try:
            folder_id = self._get_folder_id(folder_name)
            report.debug(f"using folder_id {folder_id}")
            if folder_id is None:
                msg = f"No folder named '{folder_name}'"
                report.fatal(msg)
                raise RuntimeError(msg)

            file_id = self._get_file_id(file_name, folder_id)
            if file_id is not None:
                msg = f"A file named '{file_name}' already exists in folder '{folder_name}'"
                report.fatal(msg)
                raise RuntimeError(msg)

            media = MediaFileUpload(
                path_local_file,
                resumable=True
            )
            report.set_status("Uploading")
            request = self._get_service().files().create(media_body=media,
                                                         supportsAllDrives=True,
                                                         fields="id",
                                                         body={'name': file_name, 'parents': [folder_id]})

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    report.notify("Uploaded %d%%." % int(status.progress() * 100))

            result = response.get('id')
            report.set_status("Uploaded", level="NOTIFY")
            report.debug(f"file_id={result}")
            report.set_status("exit function")
            return result

        except HttpError as error:
            report.fatal(f"HTTP error '{error}'")
            # TODO - Handle errors from drive API.
            print(f'An error occurred: {error}')

    def download(self, file_id: str, path_file: Path):
        report = self._report.get_sub_report("download", init_status="in function")
        try:
            request = self._service.files().get_media(fileId=file_id)
            io_file = io.FileIO(file=path_file, mode="x")
            downloader = MediaIoBaseDownload(fd=io_file, request=request)

            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    report.notify("Downloaded %d%%." % int(status.progress() * 100))

        except HttpError as error:
            report.fatal(f"HTTP error '{error}'")
            # TODO - Handle errors from drive API.
            print(f'An error occurred: {error}')

    def _get_folder_id(self, folder_name: str) -> Optional[str]:
        try:
            request_q = f"mimeType='application/vnd.google-apps.folder' " \
                        f"and name='{folder_name}'"
            response = self._get_service().files().list(pageSize=10, q=request_q,
                                                        corpora='drive',
                                                        driveId=self._drive_id,
                                                        includeItemsFromAllDrives=True,
                                                        supportsAllDrives=True,
                                                        fields="files(id)").execute()
            files_id = response.get('files', [])

            if len(files_id) == 0:
                return None

            if len(files_id) > 1:
                raise RuntimeError(f"More than one folder named '{folder_name}'")

            return files_id[0]['id']

        except HttpError as error:
            # TODO - Handle errors from drive API.
            print(f'An error occurred: {error}')

    def _get_file_id(self, file_name: str, folder_id: str) -> Optional[str]:
        try:
            request_q = f"mimeType!='application/vnd.google-apps.folder' " \
                        f"and name='{file_name}'" \
                        f"and '{folder_id}' in parents"
            response = self._get_service().files().list(pageSize=10, q=request_q,
                                                        corpora='drive',
                                                        driveId=self._drive_id,
                                                        includeItemsFromAllDrives=True,
                                                        supportsAllDrives=True,
                                                        fields="files(id)").execute()
            files_id = response.get('files', [])

            if len(files_id) == 0:
                return None

            if len(files_id) > 1:
                raise RuntimeError(f"More than one file named '{file_name}'")

            return files_id[0]['id']
        except HttpError as error:
            # TODO - Handle errors from drive API.
            print(f'An error occurred: {error}')

    def get_archive_id(self, archive_name: str) -> Optional[str]:
        try:
            request_q = f"mimeType='application/x-tar' " \
                        f"and name='{archive_name}'"
            response = self._get_service().files().list(pageSize=10, q=request_q,
                                                        corpora='drive',
                                                        driveId=self._drive_id,
                                                        includeItemsFromAllDrives=True,
                                                        supportsAllDrives=True,
                                                        fields="files(id)").execute()
            files_id = response.get('files', [])

            if len(files_id) == 0:
                return None

            if len(files_id) > 1:
                raise RuntimeError(f"More than one archive named '{archive_name}'")

            return files_id[0]['id']
        except HttpError as error:
            # TODO - Handle errors from drive API.
            print(f'An error occurred: {error}')
