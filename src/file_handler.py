from os import mkdir
from os.path import exists as path_exists
from os.path import join as join_path
from os.path import splitext
from typing import Optional


class FileHandler:
    def __init__(
        self,
        destination: str,
        include_extensions: bool,
        live_updates: bool,
    ) -> None:
        self.__cur_path: str = destination

        self.__directories: int = 0
        self.__files: int = 0
        self.__skipped: int = 0
        self.__size: int = 0

        self.__include_ext = include_extensions

    @staticmethod
    def __is_media_file(file_name: str, mime_type: str) -> bool:
        """
        Decides if a file is a media file -- used to decide which files to create
        `.strm` file for

        Params
        -------
        file_name: Name of the file. Used to identify media files from their extension
        mime_type: Mime type of the file on google drive

        Returns
        --------
        Boolean indicating if the file is a media file, or not
        """

        if "video" in mime_type:
            return True
        elif file_name.endswith(
            (
                ".mp4",
                ".mkv",
            )
        ):
            # Skip if item doesn't have media-file extension, or mime type
            return True

        return False

    @staticmethod
    def __shrink(input: str, *, max_len: int = 60) -> str:
        """
        Shrinks the string to fit into a fixed number of characters

        Remarks
        --------
        Shortens string to fit `max_len` characters by replacing with period(s) [...]

        For example, the string
            `This is a long string`

        When shrunk to 10 max characters using this method, will be
            `Thi....ing`

        Returns
        --------
        String containing `input` string shrunk to fit within `max_len` charcters
        """

        if len(input) <= max_len:
            return input

        # Leave space for 4 period(s) - two on each side, divide rest characters in two
        half_len = int((max_len / 2) - 2)
        return f"{input[:half_len]}....{input[-half_len:]}"

    def switch_dir(self, path: str):
        if not path_exists(path):
            mkdir(path=path)
            self.__directories += 1

        self.__cur_path = path

    def __create_strm(
        self,
        item_id: str,
        item_name: str,
        drive_id: Optional[str],
        td_id: Optional[str],
    ) -> bool:
        """
        Creates `.strm` file for files using their ID

        Params
        -------
        item_id: ID of the item on Google Drive
        item_name: Name of the item - as on Drive
        drive_id: Optional, ID of the drive containing the item
        td_id: Optional, ID of teamdrive containing the item. For items in a teamdrive
        """

        # The hard-coded strings are simply how the `Drive Add-on` extension expects 
        # them to be
        file_contents: str = (
            f"plugin://plugin.googledrive/?action=play&item_id={item_id}"
        )

        if td_id:
            file_contents += f"&item_driveid={td_id}"
        if drive_id:
            file_contents += f"&driveid={drive_id}"

        file_name = (
            f"{item_name}.strm"
            if self.__include_ext
            else f"{splitext(item_name)[0]}.strm"  # remove extension if not needed
        )

        # Create strm file, and write to it
        with open(join_path(self.__cur_path, file_name), "w+") as f:
            f.write(file_contents)

        return True

    def strm_generator(
        self,
        item_id: str,
        item_name: str,
        mime_type: str,
        item_size: int,
        drive_id: Optional[str],
        td_id: Optional[str],
    ):
        """
        Internally creates `.strm` files -- ignores non-media files
        """

        # Check if the file is a media file -- if not, direct return
        if not self.__is_media_file(file_name=item_name, mime_type=mime_type):
            self.__skipped += 1  # calculate this as a `skipped` file
            return

        result = self.__create_strm(
            item_id=item_id,
            item_name=item_name,
            drive_id=drive_id,
            td_id=td_id,
        )

        if result:
            self.__size += item_size
            self.__files += 1
