# The main script responsible for generating .strm files as needed.

import sys
from os import getcwd, mkdir
from os.path import exists, isdir, join, splitext
from pickle import dump as dump_pickle
from pickle import load as load_pickle
from re import match
from shutil import rmtree
from typing import Dict, List, Optional

from colorama import Fore, Style
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from reprint import output

import googleapiclient
import re

files_scanned = 0
directories_scanned = 0
files_skipped = 0
bytes_scanned = 0


class UserInputs:
    """
    Deals with fetching user inputs, processing and storing them
    """

    @staticmethod
    def fetch() -> UserInputs:
        """
        Reads input using `sys.argv`, extracts values for flags from the same
        """

        pass

    def __init__(
        self,
        source_drive: str,
        output_path: str,
        *,
        live_updates: bool = True,
        root_name: Optional[str] = None,
    ):
        # Folder ID of the source in Google Drive
        self.__source_drive: str = source_drive

        # Path to output directory - `.strm` files will be generated in this location
        self.__output_path: str = output_path

        # Print live updates to the screen if true
        self.__live_updates: bool = live_updates

        # Name of the root directory containing the `.strm` files
        self.__root_name: Optional[str] = root_name

    @property
    def source_drive(self) -> str:
        return self.__source_drive

    @property
    def output_path(self) -> str:
        return self.__output_path

    @property
    def live_updates(self) -> bool:
        return self.__live_updates

    @property
    def root_name(self) -> str:
        return self.__root_name if self.__root_name else ""


class DriveHandler:
    """
    Deals with Drive API and related stuff
    """

    def __init__(self):
        self.resource: googleapiclient.discovery.Resource = self.__authenticate()

    @staticmethod
    def __authenticate() -> googleapiclient.discovery.Resource:
        """
        Authenticates user session using Drive API. Will open a browser window asking user
        to login and grant required permissions for the first run. Saves a pickle file to
        skip sign-in from the second run

        Returns
        --------
        Object of `googleapiclient.discovery.Resource`
        """

        creds: Optional[Credentials] = None

        # Selectively asks for read-only permission
        SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

        if exists("token.pickle"):
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

    def __get_teamdrives(
        self, service: googleapiclient.discovery.Resource
    ) -> Dict[str, str]:
        """
        Fetches a list of all teamdrives associated with the Google account, returns the
        same as a mapping of teamdrive ID's and the corresponding name
        """

        drives: Dict[str, str] = {}

        next_page_token: Optional[str] = None
        first_run: bool = True

        while first_run or next_page_token:
            first_run = False
            page_content: Dict[str, Any] = (
                service.drives().list(pageSize=100, pageToken=next_page_token).execute()
            )

            for item in page_content["drives"]:
                drives[item["id"]] = item["name"]
                next_page_token = page_content.get("nextPageToken", None)

        return drives

    def select_teamdrive(self) -> Optional[str]:
        """
        Prints a list of all teamdrives, asks the user to select from the list displayed
        """

        drives: Dict[str, str] = self.__get_teamdrives(self.resource)
        if len(drives) == 0:
            return None

        counter: int = 1
        keys: List[str] = list(drives.keys())
        for id in keys:
            msg: str = (
                f"  {counter} " + ("/" if counter % 2 else "\\") + f"\t{drives[id]}"
            )

            print(f"{Fore.GREEN if counter % 2 else Fore.CYAN}{msg}{Style.RESET_ALL}")
            counter += 1

        while True:
            print("\nSelect a teamdrive from the list above")
            choice: str = input("teamdrive> ").strip()

            try:
                if not re.match(r"^[1-9]\d*$", choice):
                    raise ValueError(f"Unexpected input value `{choice}`")

                selected: int = int(choice)
                if selected > len(drives):
                    raise AssertionError(f"Expected input in range [1-{len(drives)}]")

                return keys[selected - 1]
            except (ValueError, AssertionError) as e:
                print(f"\t{Fore.RED}{type(e).__name__}: {e}{Style.RESET_ALL}")


class Helper:
    @staticmethod
    def walk(args: UserInputs):
        pass


def live_update(files: int, directories: int, skipped: int, size: int, out_stream):
    """
    Prints live updates to the screen.

    Parameters
    -----------
    files: Number of files scanned until now
    directories: Number of directories scanned
    skipped: Count of files that have been skipped
    size: Bytes processed so far - sum of sizes of all files processed
    out_stream: A dictionary-like object to which printed lines will be written
    """

    # Convert size into readable format
    # An array size units. Will be used to convert raw size into a readable format.
    sizes = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB"]

    counter = 0
    while size >= 1024:
        size /= 1024
        counter += 1

    readable_size = "{:.3f} {}".format(size, sizes[counter])

    out_stream[2] = f"Directories Scanned: {directories}"
    out_stream[3] = f"Files Scanned: {files}"
    out_stream[4] = f"Bytes Scanned: {readable_size}"
    out_stream[5] = f"Files Skipped: {skipped}"


def shrink_path(path: str, *, max_len: int = 70) -> str:
    """
    Shrinks the path name to fit into a fixed number of characters.
    """

    if len(path) <= max_len:
        # Direct return under max length
        return path

    allowed_len = max_len - 6
    return f"{path[:int(allowed_len / 2)]}......{path[-int(allowed_len / 2):]}"


def walk(
    origin_id: str,
    service: Resource,
    orig_path: str,
    item_details: Dict[str, str],
    out_stream,
    push_updates: bool,
    drive_path="~",
):
    """
    Traverses directories in Google Drive and replicates the file/folder structure similar to
    Google Drive.

    This method will create an equivalent `.strm` file for every media file found in a
    particular directory. The result will be the complete replication of entire directory
    structure with an strm file being generated for every media file, pointing to the original
    file on the internet.

    Parameters
    -----------
    origin_id: String containing the id of the root/source directory. \n
    service: Instance of `Resource` object used to interact with Google Drive API. \n
    orig_path: Path to the directory in which strm files are to be placed once generated. This
    directory will be made by THIS method internally. \n
    item_details: Dictionary containing details of the directory being scanned from Drive. \n
    out_stream: Dictionary to which the output is to be written to once (during updates). \n
    push_updates: Boolean indicating if updates are to be pushed to the screen or not. \n
    """

    global files_scanned, directories_scanned, bytes_scanned, files_skipped

    if not isinstance(origin_id, str) or not isinstance(service, Resource):
        raise TypeError("Unexpected argument type")

    # Updating the current path to be inside the path where this directory is to be created.
    cur_path = join(orig_path, item_details["name"])

    # Creating the root directory.
    mkdir(cur_path)

    page_token = None

    if push_updates:
        out_stream[0] = f"Scanning Directory: {shrink_path(drive_path)}/"
        out_stream[1] = "\n"  # Blank line

    while True:
        result = (
            service.files()
            .list(
                # Getting the maximum number of items available in a single API call
                # to reduce the calls required.
                pageSize=1000,
                pageToken=page_token,
                # The fields that are to be included in the response.
                fields="files(name, id, mimeType, teamDriveId, size)",
                # Getting item from all drives, this allows scanning team-drives too.
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                # Skipping trashed files and directories
                q=f"'{origin_id}' in parents and trashed=false",
            )
            .execute()
        )

        for item in result["files"]:
            if item["mimeType"] == "application/vnd.google-apps.folder":
                # If the current object is a folder, incrementing the folder count and recursively
                # calling the same method over the new directory encountered.
                directories_scanned += 1

                walk(
                    origin_id=item["id"],
                    service=service,
                    orig_path=cur_path,
                    item_details=item,
                    out_stream=out_stream,
                    push_updates=push_updates,
                    drive_path=f'{join(drive_path, item["name"])}',
                )
            elif "video" in item["mimeType"] or match(r".*\.(mkv|mp4)$", item["name"]):
                # Scanning the file, creating an equivalent strm file if the file is a media file
                # Since the mime-type of files in drive can be modified externally, scanning a file
                # as a media file even if it has an extension of `.mp4` or `.mkv`.

                # Creating string to be placed inside the strm file to ensure that the file can be
                # parsed by the drive add-on.
                file_content = (
                    f'plugin://plugin.googledrive/?action=play&item_id={item["id"]}'
                )
                if "teamDriveId" in item:
                    # Adding this part only for items present in a teamdrive.
                    file_content += (
                        f'&item_driveid={item["teamDriveId"]}'
                        f'&driveid={item["teamDriveId"]}'
                    )

                file_content += f"&content_type=video"
                with open(join(cur_path, item["name"] + ".strm"), "w+") as f:
                    f.write(file_content)

                # Updating the counter for files scanned as well as bytes scanned.
                files_scanned += 1
                bytes_scanned += int(item["size"])
            else:
                # Skipping the file if the file is not a video file. Updating counter to increment
                # number of files that have been skipped.
                files_skipped += 1

            if push_updates:
                # Updating counter on the screen if updates are to be pushed to the screen.
                live_update(
                    files=files_scanned,
                    directories=directories_scanned,
                    skipped=files_skipped,
                    size=bytes_scanned,
                    out_stream=out_stream,
                )

        if "nextPageToken" not in result:
            break


def main():
    # Starting by authenticating the connection.
    # service = authenticate()
    handler = DriveHandler()
    service = handler.resource

    destination = getcwd()
    source = None
    updates = True  # True by default.
    dir_name = None  # The name of the directory to store the strm files in.
    include_extensions = True

    # Pattern(s) to be used to match against the source argument. The group(s) are to extract
    # the value from (command-line) argument.
    pattern_source = r"^--source=(.*)"
    pattern_output = r'^--updates="?(off|on)"?$'
    patterns_extensions = r'^--no-ext$'

    # TODO: Might want to differentiate between platforms here. Especially for custom directories.
    pattern_custom_dir = r'^--rootname="?(.*)"?$'
    pattern_dest = r'^--dest="?(.*)"?$'

    # Looping over all arguments passed to the script. The first (zeroth) value shall be the
    # name of the python script.
    for i in range(len(sys.argv)):
        if i == 0:
            # Skipping the first argument, this would be the name of the python script file.
            continue

        if match(pattern_source, sys.argv[i]) and not source:
            # Pattern matching to select the source if the source is null. A better pattern match
            # can be obtained by ensuring that the only accepted value for the source is
            # alpha-numeric charter or hyphen/underscores. Skipping this implementation for now.

            # Extracting id from the argument using substitution. Substituting everything from the
            # argument string except for the value :p
            source = match(pattern_source, sys.argv[i]).groups()[0]
        elif match(pattern_dest, sys.argv[i]):
            # Again, extracting the value using regex substitution.
            destination = match(pattern_dest, sys.argv[i]).groups()[0]

            if not isdir(destination):
                print(f"Error: `{sys.argv[i]}` is not a directory.\n")
                exit(10)  # Force quit.
        elif match(pattern_output, sys.argv[i]):
            # Switching the updates off if the argument has been passed.
            # Since the default value is to allow updates, no change is required incase
            # updates are explicitly being allowed.
            if match(pattern_output, sys.argv[i]).groups()[0] == "off":
                updates = False
        elif match(pattern_custom_dir, sys.argv[i]):
            dir_name = match(pattern_custom_dir, sys.argv[i]).groups()[0]
        elif match(patterns_extensions, sys.argv[i]):
            include_extensions = False
        else:
            print(f"Unknown argument detected `{sys.argv[i]}`")
            exit(10)  # Non-zero exit code to indicate error.

    if not isinstance(source, str):
        # If a source has not been set, asking the user to select a teamdrive as root.
        # TODO: source = select_teamdrive(service)
        pass

    # Attempting to get the details on the folder/teamdrive being used as the source.
    item_details = service.files().get(fileId=source, supportsAllDrives=True).execute()

    if (
        "teamDriveId" in item_details
        and item_details["id"] == item_details["teamDriveId"]
    ):
        # If the source is a teamdrive, attempting to fetch details for the teamdrive instead.
        item_details = (
            service.drives().get(driveId=item_details["teamDriveId"]).execute()
        )

    if dir_name is not None:
        # If the directory name is already set, i.e. it has been supplied as a command-line argument
        # setting the name in the dictionary to be this custom name.
        item_details["name"] = dir_name
    else:
        # If the name of the root directory is not set, using the name of the teamdrive/drive.
        dir_name = item_details["name"]

    # Clearing the destination directory (if it exists).
    final_path = join(destination, dir_name)
    if isdir(final_path):
        rmtree(final_path)

    print()  # Empty print.

    # Calling the method to walk through the drive directory.
    with output(output_type="list", initial_len=6, interval=0) as out_stream:
        # Creating the output object here to ensure that the same object is being used
        # for updates internally.

        walk(
            origin_id=source,
            service=service,
            orig_path=destination,
            item_details=item_details,
            out_stream=out_stream,
            push_updates=updates,
        )

    print(f"\n\tTask completed. Saved the output at `{final_path}`")


if __name__ == "__main__":
    main()
