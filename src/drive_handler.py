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

        # Dictionary mapping teamdrive ID's to their name
        self.dirs: Dict[str, str] = {}

    def drive_name(self, drive_id: str) -> str:
        """
        Returns name for a teamdrive using its ID
        """

        return self.dirs[drive_id]

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

    def get_dir_details(self, *, dir_id: str) -> Dict[Any, Any]:
        """
        Returns info obtained regarding a directory/file from Google Drive API

        Remarks
        --------
        Designed to get folder info from drive API, but can work with files as well
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
            return result
        except Exception as e:
            typer.secho(
                f"Unable to find folder with ID `{dir_id}`", fg=typer.colors.RED
            )
            raise typer.Abort()

    def get_teamdrives(self):
        """
        Fetches a list of all teamdrives associated with the Google account

        Remarks
        --------
        Needs to be executed before `select_teamdrive` method -- will fetch all
        teamdrives linked to the Google Account
        """

        next_page_token: Optional[str] = None
        first_run: bool = True
        while next_page_token or first_run:
            first_run = False
            page_content: Dict[str, Any] = (
                self.resource.drives()
                .list(pageSize=100, pageToken=next_page_token)
                .execute()
            )

            for item in page_content["drives"]:
                self.dirs[item["id"]] = item["name"]

            # Loops as long as there is a `nextPageToken`
            next_page_token = page_content.get("nextPageToken", None)

    def select_teamdrive(self) -> str:
        """
        Gets user to select source drive from team-drives

        Returns
        --------
        String containing ID of the selected teamdrive
        """

        if len(self.dirs) == 0:
            typer.secho("Unable to locate any teamdrives!", fg=typer.colors.RED)
            raise typer.Abort()

        counter: int = 1
        keys: List[str] = list(self.dirs.keys())
        for id in keys:
            typer.secho(
                f"  {counter}. "
                + ("/" if counter % 2 else "\\")
                + f"\t{self.dirs[id]}",
                fg=typer.colors.GREEN if counter % 2 else typer.colors.CYAN,
            )

            counter += 1

        while True:
            typer.echo("\nSelect a teamdrive \nteamdrive> ", err=True, nl=False)
            choice: str = input().strip()

            try:
                selected: int = int(choice)
                if selected > len(self.dirs):
                    raise AssertionError(
                        f"Expected input in range [1-{len(self.dirs)}]"
                    )
                return keys[selected - 1]
            except AssertionError as e:
                typer.secho(f"\t{type(e).__name__}: {e}", fg=typer.colors.RED, err=True)
            except ValueError as e:
                typer.secho(
                    f"ValueError: Invalid input `{choice}`",
                    fg=typer.Colors.RED,
                    err=True,
                )

    def walk(
        self,
        source: str,
        *,
        change_dir: Callable[[str], None],
        generator: Callable[[str, str, str, int, Optional[str], Optional[str]], None],
        orig_path: str,
        custom_root: Optional[str] = None,
    ):
        """
        Walks through the source folder in Google Drive - creating `.strm` files for
        each media file encountered

        Params
        -------
        source: String containing ID of the source directory
        source_details: Dictionary containing info regarding the source directory
        change_dir: Method call to create, and change directories. Should accept
            complete path to the directory as parameter
        handler: Method call to create `strm` files
        strm_creator: Function to create `.strm` files - supplied arguments; item id,
            item name, teamdrive id [optional]
        custom_root: Optional. String containing custom name for root directory
        """

        # Stack to track directories encountered. Each entry in the stack will be a
        # tuple consisting of the directory id, and a path to the local directory
        queue: deque[Tuple[str, str]] = deque()
        queue.append(
            [
                source,
                join_path(orig_path, custom_root if custom_root else self.dirs[source]),
            ]
        )

        page_token: str = None
        while len(queue):

            dir_id, path = queue.pop()
            change_dir(path)

            page = (
                self.resource.files()
                .list(
                    pageSize=1000,  # get max items possible with each call
                    pageToken=page_token,  # decides page for pagination
                    fields="files(name, id, mimeType, teamDriveId, driveId, size)",  # response
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
                    queue.append([item["id"], join_path(path, item["name"])])
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
