## kodi-strm

<div align="center">

  ![A gif displaying `kodi-strm` in action][demo-gif]

  ![Release][latest-release]
  ![Release Date][release-date]
  ![Language][language]
  ![License][license]
  ![Code Size][code-size]

  A project to complement the Google Drive AddOn for Kodi

  <p align="center">
    <a href="#usage"><strong>Jump to Docs »</strong></a>
    <br><br>
    ·
    <a href="../../issues/new?template=bug_report.md">Bug Report</a>
    ·
    <a href="../../issues/new?template=feature_request.md">Request Feature</a>
    ·
    <a href="../../fork">Fork Repo</a>
    ·
  </p>

</div>

<!-- ABOUT THE PROJECT -->
## About The Project

A python script to complement the functionality of [Google Drive AddOn][kodi-addon] for Kodi.

While the add-on [claims][speed-claim] to be "*extremely fast*", I found this claim to
be dubious. Based on my usage so far, the addon was slow, unreliable, crashed frequently,
and often got stuck. Eventually, frustration drove me to write a simple python script to
generate strm files for the add-on, post which all the add-on had to do was simply play
them! Over time, the small script grew into this project.

To reiterate, the sole purpose of this project is to create strm files for media file(s)
present in a directory on Google Drive — and achieve this more reliably than the than
the existing Kodi add-on.

No ill-will is intended towards Carlos (the creator of the Google Drive add-on), I am
extremely thankful for all the work that went into making the add-on — *kodi-strm* is
in no way meant to be a replacement for the Google Drive add-on.

### What is a strm file?

In simple terms, *strm* files refer to files having an extension of `.strm`. They are
created by multimedia applications (Kodi and Plex being the main examples) and, primarily
contain a URL pointing to the media file(s) stored in a remote server/cloud,

These files are then parsed by the application, post which the URL is used to stream the
actual media file.

## Pre-Requisites
* Python 3.9 or above — get it from [here][python-dl]

## Setup
1. Clone this project
2. Create a [Google Project][google-console] and [enable Google Drive API][enable-api]
3. Setup credentials to use this API
4. Download these credentials as a JSON file, rename this file to be `credentials.json`
5. Move `credentials.json` into this project directory
6. Install the project dependencies.

```shell
pip install -r requirements.txt
```

Alternatively, for the last step, you can directly use the `setup.sh` or `setup.bat`
scripts and have them create an efficient setup for you.

#### What do the setup scripts do?

The setup script will;
 * Update `pip`
 * Install `virtualenv`
 * Create a virtual environment named `venv`
 * Activate this environment
 * Install required dependencies into this virtual environment

While anyone is free to use the direct setup scripts, do note that they are primarily
for my use (to quickly setup a system for testing/debugging) - and *aren't guaranteed*
to work in your system.

### Post Setup

Once you're done with setting up a working enviroment, simply run the script

```sh
python strm-generator.py

OR

python -m kodi_strm
```

For the first run, the script will ask you to login to a Google account. While not
necessary, it is recommended to use the same Google account for this script, and the
Google Drive Add-On.

P.S. Make sure to install the [Google Drive add-on][kodi-addon] in your Kodi installation.

## Usage

Running the script without any arguments will fetch a list of all teamdrives to which
the account has access, allowing you to select a teamdrive from this list. The selected
teamdrive will then be treated as the source directory for the script.

Alternatively, you can use [custom arguments](#custom-arguments) to modify the source
directory, destination, or more!

Once the script finishes generating strm files after a scan, add the resulting
[directory as a source](https://kodi.wiki/view/Adding_video_sources) in your Kodi
installation. From there on, the Google Drive AddOn will treat these `.strm` files as
actual media files and will be able to scan/play them normally.

> Note:
>
> If you are unable to play the media files with Kodi, make sure that you have installed
> the [Kodi AddOn for Google Drive][kodi-addon] and have logged into the add-on with the
> **same** Google Account that you are using for this script.

Once you're comfortable with the usage of this script, you might want to take a look at
the [advanced setup](#advanced-setup) section for some ideas :)

### Quick Overview

|        Flag       |  ShortHand |                        Description                        |           Default          |
|:-----------------:|:----------:|:---------------------------------------------------------:|:--------------------------:|
|    `--version`    |    `-v`    |            Display `kodi-strm` version and exit           |             NA             |
|      `--help`     |            |                   Display help and exit                   |             NA             |
|     `--source`    |            |               Drive ID for the source folder              |             NA             |
|  `--destination`  |  `--dest`  |  Destination directory where `.strm` files are generated  |  Current Working Directory |
|    `--rootname`   |  `--root`  |               Name of the `source` directory              | Name of `source` directory |
| `--no-extensions` | `--no-ext` | Remove original file extensions from generated strm files |             NA             |
|   `--no-updates`  |            |             Disable live updates on the screen            |             NA             |
|     `--force`     |    `-f`    |  Directly wipe out `root` directory in case of collision  |             NA             |

By default, the strm files generated after a scan are stored in the **working directory**.
Use `pwd` in Unix-based systems, or `cd` in Windows get the location of current working
directory.

Note: Take a look at the flag for [custom destination directory](#custom-destination-directory)
and to modify this behaviour.

## Custom Arguments

Custom arguments passed when executing the script from the terminal allow you to modify
the behaviour of the script!

```sh
python strm-generator.py [OPTIONS]

OR

python -m kodi_strm [OPTIONS]
```

#### Source Directory

**Flag:** `--source=<folder-id>`<br>
**Shorthand:** `NA`<br>
**Value Expected:** ID of a folder/teamdrive on Google Drive

This flag allows you to scan the contents of a folder/teamdrive from Google Drive, i.e.
with the help of this flag instead of scanning a complete teamdrive (or the main drive),
an individual folder can be selectively scanned using its ID.

> A source directory is a folder/teamdrive in Google Drive that is used as the **source**
> to generate strm files by *kodi-strm*

If source directory is **not** specified, the script will ask you to select  a teamdrive
as the source - the selected teamdrive will be scanned by the script.

> Note: Check [Getting Folder IDs](#getting-folder-ids) section to learn how to get the
> ID of a folder/teamdrive from Google Drive.

#### Custom Destination Directory

**Flag:** `--destination="</path/to/destination>"`<br>
**Shorthand:** `--dest`<br>
**Expected Value:** Path to an ***existing*** directory.<br>

This flag is used to decide the destination directory in which the root directory
(containing the strm files) will be placed. Should be a path to an existing directory!

[>> Resource: Destination Directory vs Root Directory](#destination-directory-vs-root-directory)

P.S. If the path contains spaces, wrap it in double quotes.

#### Updates

**Flag:** `--no-updates`<br>
**Shorthand:** `NA`<br>
**Expected Value:** `NA`<br>

Obviously enough, using this flag disables any updates from *kodi-strm* (expect for the
final completion message).

By default, *kodi-strm* prints realtime updates on the terminal - this includes info
on the directory and file(s) being scanned, and more!

Having realtime updates might not always be desirable (especially if run in background).
Using this flag will run the script in silent mode - the only console message will be to
completion.

#### Custom Name for Root Directory

**Flag:** `--rootname=<root-directory>`<br>
**Shorthand:** `--root`<br>
**Expected Value:** Name for the root directory<br>

Optional flag to modify the name of root directory. By default, the name of the
teamdrive/folder being scanned  will be used as the name of the root directory.

[>> Resource: Destination Directory vs Root Directory](#destination-directory-vs-root-directory)

Important: If a directory with the same name as the root directory already exists inside
destination directory, the script will ask you for confirmation before proceeding to
wipe the existing path.

#### Force-Wipe Existing Paths

**Flag:** `--force`<br>
**Shorthand:** `-f`<br>
**Expected Value:** `NA`<br>

With the `force` flag enabled, if there is a collision when creating the `root`
directory, the existing path will be wiped completely - without any confirmation!

By default, in case of a path collision, *kodi-strm* will ask you for confirmation
before deleting the existing path. However, this may not always be desired - especially
if you already plan to overwrite the existing directory.

For such *specific* scenarios, enabling the `force` flag ensures *kodi-strm* will
directly proceed by wiping the existing path (without asking for a confirmation).

#### Version

**Flag:** `--version`<br>
**Shorthand:** `-v`<br>
**Expected Value:** `NA`<br>

Prints info related to the operating system, and the current version of *kodi-strm*,
following which the script directly terminates

#### Help

**Flag:** `--help`<br>
**Shorthand:** `NA`<br>
**Expected Value:** `NA`<br>

Prints a list of all flags available, and a brief description regarding them

## Resources

#### Getting Folder ID's

You can get the id for a particular folder from the url to the directory.

For example, in the URL `https://drive.google.com/drive/folders/0AOC6NXsE2KJMUk9PTA`,
the folder-id is `0AOC6NXsE2KJMUk9PTA`.

This method can also be used to get the ID of a particular TeamDrive and use it as a
[custom argument](#scanning-a-folder-selectively) to directly scan the teamdrive.


#### Destination Directory vs Root Directory

In simplifed terms, `destination` directory is "destination" directory, which will
contain the *root* directory. When run, `kodi-strm` will create a `root` directory
in the destination directory - this *root* directory will contain the contents of
scanned Google Drive folder.

The `root` directory will be the directory/teamdrive that is being scanned from Google
Drive. As an example, if you scan a Google Drive folder *Movies* with folder ID 
`0TRC6NXsE2KJMUkasdA` and want to store the generated *strm* files in `~/Downloads`;
  - The directory `~/Downloads` will be the `destination` directory
  - Inside `~/Downloads`, *kodi-strm* will **create** a directory named "Movies". This
      is the `root` directory - that is placed inside the `destination` directory.

You can modify destination path (the `destination` directory) with the`--destination`
flag, at the same time, you can modify the name of the created directory ("Movies") to
be, say "*Drive Movies*" with the `--rootname` flag!

The following command will use `~/home` as the destination directory - i.e. strm files
will be placed at this location, and "*output files*" as the name of source
root directory that will contain the actual strm files

```sh
python strm-generator.py --source=0TRC6NXsE2KJMUkasdA --destination="~/home" --rootname="output files"
```

From the example above, the folder `0TRC6NXsE2KJMUkasdA` is named "Movies" on Google
Drive, but running the above command will rename the root folder to be "output files" 
in the *destination* directory.

P.S. The `destination` path should point to an **existing directory**, while the
`rootname` will be a folder that is **created by the script in destination directory**,
and should **not** exist.

## Examples

#### Scanning a folder selectively

Simply scan a Google drive folder with the ID `0AOC6NXsE2KJMUk9PVA` and place the root
directory at the destination `/home/kodi library`

```sh
python -m kodi_strm --source=0AOC6NXsE2KJMUk9PVA --destination="/home/kodi library"
```

Note the additional destination flag in the command, instead of placing the results in
the working directory, the script will now place them inside `/home/kodi library`.

Also, since the destination path contains a space, it needs to be wrapped in quotes. It
is recommended to wrap paths in double quotes regardless of whether it contains spaces.

#### Custom root directory

Running the following command will rename the root directory to be `new root directory`

```sh
python strm-generator.py --source=0AOC6NXsE2KJMUk9PVA --dest="/home/kodi library" --rootname="new root directory"
```

The strm files will inside a directory named `new root directory` (the root directory).
The root directory by itself will be present in `"/home/kodi library"` (the destination
directory).

### Miscellaneous Examples

* Scanning a particular folder on drive, with custom destination and root directories,
plus no updates to the console (using all the flags at once).

```sh
python -m kodi_strm --source=0AOC6NXsE2KJMUk9PVA --dest="/home/kodi libraries" --rootname="Staging; Media" --no-updates
```

* Scanning a folder with no updates
```sh
python strm-generator.py --source=0AOC6NXsE2KJMUk9PVA --no-updates
```

* Scanning a folder selectively with custom root directory
```sh
python strm-generator.py --source=0AOC6NXsE2KJMUk9PVA --rootname="Media"
```

* Scanning a folder with custom destination directory and no updates on console
```sh
python strm-generator.py --source=0AOC6NXsE2KJMUk9PVA --dest="/home/Videos" --no-updates
```

## Advanced Setup

This section contains ideas and suggestions to how you can use this script to get a
seamless experience with you Kodi setup.

With a little help of [custom arguments](#custom-arguments) supported by the script,
you can set up the script to be run on fixed intervals (with pre-fixed parameters).

For example, I'm on Linux, I've setup a [systemd.service][systemd] to run this script
once every couple of days. At every run, the script scans a folder from Google Drive,
and places it inside an existing Kodi library.

Whenever I open up Kodi, it automatically scrapes the new files, and adds them to my
library. And so, my system automatically fetches any updates on Google Drive, syncs
them, and adds them to Kodi without requiring any input from me.

If needed, the systemd service can be modified to run the script multiple times,
scanning different sources each time to be able to scale my current setup to span
across multiple teamdrives/folders, all this without requiring any sort of input.

Windows users can achieve the same functionality as systemd.service using
[Windows Task Scheduler](https://en.wikipedia.org/wiki/Windows_Task_Scheduler). In case
someone wants to replicate a similar setup as mine, here are some useful links to help
you get started.

- [Creating a systemd.service](https://medium.com/@benmorel/creating-a-linux-service-with-systemd-611b5c8b91d6)
- [Using Windows Task Scheduler](https://windowsreport.com/schedule-tasks-windows-10)
- [Setting up Kodi for auto-scan](https://www.howtogeek.com/196025/ask-htg-how-do-you-set-your-xbmc-library-to-automatically-update/)

P.S. If you're setting up a service for automated runs, you might want to add the
`--force` flag to your command ([docs](#force-wipe-existing-paths)) - especially for
setups similar to mine! The flag ensures *kodi-strm* will wipe the existing
directory instead of (permanently) waiting for a confirmation in the background.

<!-- ROADMAP -->
## Roadmap

The main aim for this project isn't to replace the exising Google Drive AddOn, but to build upon it and fix the flaws. As such, a large part of what I found missing in the add-on has already been fixed -- namely, speed and reliablitly.

Based on the tests I've run, this script is ~20% faster than the Google Drive Add-On, and is a lot more reliable (no crashes so far).

> *For the curious, yes, I ran the test on the exact same source without any modifications. The results are as accurate as possible.*

#### A list of *possible* improvements;
- ~~Display live progress when the script runs~~ added in #1
- Multithreading (still not sure on this one) - despite GIL, the execution speed can be improved to *some* extent

## Contributions

Contributions are what make the open source community such an amazing place to learn,
inspire, and create. Any contributions made are **extremely appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/new-feature`)
3. Commit your Changes (`git commit -m 'Add amazing new features'`)
4. Push to the Branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License
Distributed under the MIT License. See [`LICENSE`](./LICENSE). for more information.

## Acknowledgements
* [Img Shields](https://shields.io)
* [Google API Python Client](https://github.com/googleapis/google-api-python-client)
* [Coloroma](https://github.com/tartley/colorama)
* [Reprint](https://github.com/Yinzo/reprint)

### Sponsors

`kodi-strm` was made possible with the support of the following organization(s):

<div align="center">
<a href="https://tutanota.com">
  <img src="https://tutanota.com/resources/images/press/tutanota-logo-red-black-font.svg" width="300" height="150"></img>
</a>
<div>
  
[python-dl]: https://www.python.org/downloads
[google-console]: http://console.developers.google.com
[kodi-addon]: https://kodi.tv/addons/matrix/plugin.googledrive
[systemd]: https://man7.org/linux/man-pages/man5/systemd.service.5.html
[enable-api]: https://developers.google.com/drive/api/v3/enable-drive-api
[speed-claim]: https://github.com/cguZZman/plugin.googledrive#:~:text=Extremely%20fast
[code-size]: https://img.shields.io/github/languages/code-size/notsatan/kodi-strm?style=for-the-badge
[language]: https://img.shields.io/github/languages/top/notsatan/kodi-strm?style=for-the-badge
[license]: https://img.shields.io/github/license/notsatan/kodi-strm?style=for-the-badge
[latest-release]: https://img.shields.io/github/v/release/notsatan/kodi-strm?style=for-the-badge
[release-date]: https://img.shields.io/github/release-date/notsatan/kodi-strm?style=for-the-badge
[issues-url]: https://img.shields.io/github/issues-raw/notsatan/kodi-strm?style=for-the-badge
[demo-gif]: https://user-images.githubusercontent.com/22884507/177959717-33ed1a20-c289-4dcf-a9b2-4d497e4eb2c6.gif