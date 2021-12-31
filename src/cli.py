import os
import platform
import sysconfig
from pathlib import Path
from typing import Optional

import typer
from reprint import output

from src.drive_handler import DriveHandler
from src.file_handler import FileHandler

__VERSION: Optional[str] = "1.5.1-alpha"
__APP_NAME: Optional[str] = "kodi-strm"

# Switch to flip all flags to be case in/sensitive
__CASE_SENSITIVE: bool = False


def __callback_version(fired: bool):
    """
    Callback function - fired when the `--version` flag is invoked. Check the value
    of `fired` to know if the user has actually used the flag
    """

    if not fired:
        return  # flag was not invoked

    typer.echo(
        f"{__APP_NAME} v{__VERSION}\n"
        + f"- os/kernel: {platform.release()}\n"
        + f"- os/type: {sysconfig.get_platform()}\n"
        + f"- os/machine: {platform.machine()}\n"
        + f"- os/arch: {platform.architecture()[0]}\n"
        + f"- python/version: {platform.python_version()}\n",
    )

    raise typer.Exit()  # direct exit


def cmd_interface(
    source: Optional[str] = typer.Option(
        None,
        "--source",
        show_default=False,
        case_sensitive=__CASE_SENSITIVE,
        help="Folder ID for source directory on Google Drive",
    ),
    destination: Optional[Path] = typer.Option(
        None,
        "--dest",
        "--destination",
        exists=True,  # path needs to exist
        writable=True,  # ensures a writeable path
        dir_okay=True,  # allows path to directory
        file_okay=False,  # rejects path to a file
        resolve_path=True,  # resolves complete path
        case_sensitive=__CASE_SENSITIVE,
        help="Set a destination directory where strm files will be placed",
    ),
    root_name: Optional[str] = typer.Option(
        None,
        "--root",
        "--rootname",
        case_sensitive=__CASE_SENSITIVE,
        help="Set a custom name for the source directory",
    ),
    rem_extensions: bool = typer.Option(
        False,
        "--no-ext",
        "--no-extensions",
        show_default=False,
        case_sensitive=__CASE_SENSITIVE,
        help="Remove original extensions from generated strm files",
    ),
    updates: bool = typer.Option(
        True,
        show_default=False,
        case_sensitive=__CASE_SENSITIVE,
        help="Show progress during transfers",
    ),
    version: bool = typer.Option(
        None,
        "--version",
        is_eager=True,
        callback=__callback_version,
        case_sensitive=__CASE_SENSITIVE,
        help="Display current app version",
    ),
) -> None:
    drive_handler = DriveHandler()  # authenticate drive api

    with output(output_type="list", initial_len=9, interval=500) as outstream:
        # Replace destination directory with the current directory path if not supplied
        destination = destination if destination else os.getcwd()
        file_handler = FileHandler(
            destination=destination,
            include_extensions=not rem_extensions,
            live_updates=updates,
            outstream=outstream,
        )

        if not source or len(source) == 0:
            # No source directory is provided, get the user to choose a teamdrive
            source = drive_handler.select_teamdrive()

        if updates:
            typer.secho(
                f"Walking  through `{drive_handler.drive_name(source)}`\n",
                fg=typer.colors.RED,
                err=True,
            )

        drive_handler.walk(
            source=source,
            change_dir=file_handler.switch_dir,
            generator=file_handler.strm_generator,
            orig_path=destination,
            custom_root=root_name,
        )

    typer.secho(f"Completed generating strm files\nFiles located in: {destination}", fg=typer.colors.GREEN)


def main():
    typer.run(cmd_interface)
