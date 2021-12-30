from collections import deque
from os.path import exists as path_exists
from os.path import join as join_path
from pickle import dump as dump_pickle
from pickle import load as load_pickle
from typing import Any, Callable, Dict, List, Optional, Tuple

import googleapiclient
import googleapiclient.discovery as discovery
import typer
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


class DriveHandler:
    """
    Deals with Drive API and related stuff
    """

    def __init__(self):
        self.resource: googleapiclient.discovery.Resource = self.__authenticate()

        # Dictionary mapping ID's to their (human-readable) name. Acts as a simple cache
        # to reduce API calls. Can be used for teamdrives, and normal directories
        self.dirs: Dict[str, str] = {}

    def __authenticate(self) -> discovery.Resource:
        """
        Authenticates user session using Drive API.

        Remarks
        --------
        Attempts to open a browser window asking user to login and grant permissions
        during the first run. Saves a `.pickle` file to skip this step in future runs

        Returns
        --------
        Object of `googleapiclient.discovery.Resource`
        """

        creds: Optional[Credentials] = None

        # Selectively asks for read-only permission
        SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

        if path_exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds: Credentials = load_pickle(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open("token.pickle", "wb") as token:
                dump_pickle(creds, token)  # save credentials for next run

        return googleapiclient.discovery.build("drive", "v3", credentials=creds)

    def __get_teamdrives(self) -> Dict[str, str]:
        """
        Fetches and returns a list of all teamdrives associated with the Google account

        Remarks
        --------
        Returns a dictionary of all teamdrives associated with the account. Aborts if
        the account has no teamdrive associated with it.

        Teamdrives (if found) will be cached in `self.dirs`
        """

        next_page_token: Optional[str] = None
        first_run: bool = True

        tds: Dict[str, str] = {}
        while next_page_token or first_run:
            first_run = False
            page_content: Dict[str, Any] = (
                self.resource.drives()
                .list(pageSize=100, pageToken=next_page_token)
                .execute()
            )

            for item in page_content["drives"]:
                self.dirs[item["id"]] = item["name"]
                tds[item["id"]] = item["name"]

            # Loops as long as there is a `nextPageToken`
            next_page_token = page_content.get("nextPageToken", None)

        return tds

    def drive_name(self, drive_id: str) -> str:
        """
        Returns name for a teamdrive using its ID

        Remarks
        --------
        Looks for info in local cache - if not found, will internally make a network
        call and return the directory name
        """

        if drive_id not in self.dirs:
            self.fetch_dir_name(dir_id=drive_id)  # fetch info if not cached already

        return self.dirs[drive_id]

    def fetch_dir_name(self, *, dir_id: str) -> str:
        """
        Returns info obtained regarding a directory/file from Google Drive API

        Remarks
        --------
        Designed to get directory name from drive API, but can work with files as well.
        Internally caches directory name against folder id in `self.dirs`

        Always fetches info through a network call. Use `drive_name` to look through
        cache before making a network call
        """

        try:
            result = (
                self.resource.files()
                .get(fileId=dir_id, supportsAllDrives=True)
                .execute()
            )

            if result.get("id", True) == result.get("teamDriveId", None):
                # Enters this block only if the `dir_id` belongs to a teamdrive
                result = self.resource.drives().get(driveId=dir_id).execute()

            # Cache directory name -- works with teamdrives and folders, id's are unique
            self.dirs[result["id"]] = result["name"]
            return result["name"]
        except Exception as e:
            typer.secho(
                f"Unable to find drive directory `{dir_id}`", fg=typer.colors.RED
            )
            raise typer.Abort()

    def select_teamdrive(self) -> str:
        """
        Gets user to select source drive from team-drives

        Returns
        --------
        String containing ID of the selected teamdrive
        """

        tds = self.__get_teamdrives()

        if len(tds) == 0:
            typer.secho("Unable to locate any teamdrives!", fg=typer.colors.RED)
            raise typer.Abort()

        counter: int = 1
        keys: List[str] = list(tds.keys())
        for id in keys:
            typer.secho(
                f"  {counter}. " + ("/" if counter % 2 else "\\") + f"\t{tds[id]}",
                fg=typer.colors.GREEN if counter % 2 else typer.colors.CYAN,
            )

            counter += 1

        while True:
            typer.echo("\nSelect a teamdrive \nteamdrive> ", err=True, nl=False)
            choice: str = input().strip()

            try:
                selected: int = int(choice)
                if selected > len(tds):
                    raise AssertionError(f"Expected input in range [1-{len(tds)}]")
                return keys[selected - 1]
            except AssertionError as e:
                typer.secho(f"\t{type(e).__name__}: {e}", fg=typer.colors.RED, err=True)
            except ValueError as e:
                typer.secho(
                    f"\tValueError: Invalid input `{choice}`",
                    fg=typer.colors.RED,
                    err=True,
                )

    def walk(
        self,
        source: str,
        *,
        orig_path: str,
        change_dir: Callable[[str], None],
        generator: Callable[[str, str, str, int, Optional[str], Optional[str]], None],
        custom_root: Optional[str] = None,
    ):
        """
        Walks through the source folder in Google Drive - creating `.strm` files for
        each media file encountered

        Params
        -------
        source: String containing ID of the source directory
        orig_path: String containing path to the destination directory
        change_dir: Method call to create, and change directories. Should accept
            complete path to the directory as parameter
        generator: Method call to create `strm` files
        strm_creator: Function to create `.strm` files - supplied arguments; item id,
            item name, teamdrive id [optional]
        custom_root: Optional. String containing custom name for root directory
        """

        if not custom_root and not self.dirs.get(source, False):
            # The source directory has not been cached, fetch the same
            self.fetch_dir_name(dir_id=source)

        # Stack to track directories encountered. Each entry in the stack will be a
        # tuple consisting of the directory id, and a path to the local directory,
        # and a string containing the name of the directory
        queue: deque[Tuple[str, str]] = deque()
        queue.append(
            [
                source,
                join_path(orig_path, custom_root if custom_root else self.dirs[source]),
                self.dirs[source],
            ]
        )

        page_token: str = None
        while len(queue):

            dir_id, path, dir_name = queue.pop()
            change_dir(path, dir_name)

            page = (
                self.resource.files()
                .list(
                    pageSize=1000,  # get max items possible with each call
                    pageToken=page_token,  # decides page for pagination
                    fields="files(name, id, mimeType, teamDriveId, driveId, size)",
                    supportsAllDrives=True,  # enable support for teamdrives
                    includeItemsFromAllDrives=True,
                    # Ensure items are in parent directory, exclude deleted items
                    q=f"'{dir_id}' in parents and trashed=false",
                )
                .execute()
            )

            for item in page["files"]:
                if item["mimeType"] == "application/vnd.google-apps.folder":
                    # Add this directory to the queue
                    queue.append(
                        [item["id"], join_path(path, item["name"]), item["name"]]
                    )
                    continue

                # Generate STRM file if the flow-of-control reaches this point
                # The function will internally ignore non-media files
                generator(
                    item_id=item["id"],
                    item_name=item["name"],
                    mime_type=item["mimeType"],
                    item_size=int(item["size"]),
                    drive_id=item.get("driveId", None),
                    td_id=item.get("teamDriveId", None),
                )
