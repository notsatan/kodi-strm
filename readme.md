![Release][latest-release]
![Release Date][release-date]
![Language][language]
![License][license]
![Issues][issues-url]

<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/demon-rem/kodi-strm/">
    <img src="./images/kodi-logo.png" alt="Logo" width="320" height="160">
  </a>

  <h3 align="center">kodi-strm</h3>

  <p align="center">
    A small project to complement the Google Drive AddOn for Kodi
    <br><br>
    <a href="https://github.com/demon-rem/kodi-strm/"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    ·
    <a href="https://github.com/demon-rem/kodi-strm/issues">Bug Report</a>
    ·
    <a href="https://github.com/demon-rem/kodi-strm/issues">Request Feature</a>
    ·
    <a href="https://github.com/demon-rem/kodi-strm/fork">Fork Repo</a>
    ·
  </p>
</p>
<br>

---
<br>
<!-- TABLE OF CONTENTS -->

## Table of Contents
- [Table of Contents](#table-of-contents)
- [About The Project](#about-the-project)
  - [What is a `.strm` file?](#what-is-a-strm-file)
- [Pre-Requisites](#pre-requisites)
- [Setup](#setup)
- [Usage](#usage)
  - [Generating strm files](#generating-strm-files)
  - [Where are the strm files stored?](#where-are-the-strm-files-stored)
- [Custom Arguments](#custom-arguments)
  - [Scanning a particular folder](#scanning-a-particular-folder)
  - [Modifying the directory where strm files are generated](#modifying-the-directory-where-strm-files-are-generated)
    - [Getting Folder ID's](#getting-folder-ids)
  - [How is this script better than the existing add-on?](#how-is-this-script-better-than-the-existing-add-on)
- [How does this script work](#how-does-this-script-work)
- [Advanced Setup](#advanced-setup)
- [Roadmap](#roadmap)
    - [A list of *possible* improvements;](#a-list-of-possible-improvements)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)



<!-- ABOUT THE PROJECT -->
## About The Project

A simple python script to to complement the functionality of [Google Drive AddOn](https://kodi.tv/addon/music-add-ons-picture-add-ons-plugins-video-add-ons/google-drive) for Kodi.

For an add-on that [claims to be "*extremely fast*"](https://github.com/cguZZman/plugin.googledrive), I found the add-on to be quite slow (*and unreliable*). It crashes way too frequently, is slow, and gets stuck way too often (this happened frequently enough, to the point I decided to make this project just to solve this problem).

The main purpose of this project is to generate `.strm` files for media file(s) present in a directory on Google Drive - and achieve this more reliably than the Kodi AddOn.

### What is a `.strm` file?

In simple terms, *strm* files are usually created and used by multimedia applications (Kodi and Plex being the main examples). They are used to store URL(s), which is then used by the application to stream the actual media file using the URL.

<br>

---
## Pre-Requisites
* Python 3.5+

## Setup
1. Create a [Google Project](http://console.developers.google.com/) and [enable Google Drive API](https://developers.google.com/drive/api/v3/enable-drive-api).
2. Once you enable the Drive API for your project, setup the cerdentials required to use the API.
3. Download the credentials as a JSON file and rename them it as `credentials.json`.
4. Move the credentials into the same directory containing the python script.
5. Install the python dependencies.
    <br> `pip install -r requirements.txt`
6. Install [Kodi AddOn for Google Drive](https://kodi.tv/addon/music-add-ons-picture-add-ons-plugins-video-add-ons/google-drive) in your Kodi installation.
7. Login to the add-on. Make sure that you use the same Google account while logging into this script and the Google add-on.

Alternatively, for the fourth step, you can directly use the `setup.sh` or `setup.bat` scripts to get an efficient setup.

> #### What do the setup scripts do?
>
> The setup script will;
> * Update `pip`
> * Install `virtualenv`
> * Create a virtual environment as a directory named `.venv`
> * Install required packages inside this virtual environment.

While anyone is free to use them, do note that the setup scripts are primarily for my use (to quickly setup a system for usage/testing/debugging) - and so are not guranteed to work with every OS/system/distro.

## Usage

Executing the python script directly (without custom arguments) will fetch a list of all teamdrives to which the account has access - allowing you to select a teamdrive from this list which will then be scanned, and strm files for all media files found in this source will be created.

Alternatively, you can pass [custom arguments](#custom-arguments) to the script to scan a particular folder, or to modify the directory where the strm files are stored after being generated.

Once the script finishes generating the strm files after a scan, you can add this [directory as a source](https://kodi.wiki/view/Adding_video_sources) in your Kodi installation. For most practical purposes, Kodi will treat these `.strm` files as actual media files.

Note; Once you're comfortable with the usage of this script, you might want to take a look at the [advanced setup](#advanced-setup) section.

### Generating strm files

Running the script without any custom arguments will fetch a list of all team-drives that are connected to the account, selecting a teamdrive from this list will make the script scan the contents of the particular teamdrive.

### Where are the strm files stored?

By default, the `.strm` files generated after a scan are stored in the **working directory**.

In case a complete teamdrive is scanned, the generated strm files will be stored inside a directory named `Drive`. Alternatively, after scanning a particular folder on Google Drive, the generated files will be stored in a directory of the same name as the folder scanned.

Use `pwd` in Unix-based systems, or `dir` in Windows get the location of current working directory 

## Custom Arguments

Using custom arguments, you can control the folder that is being scanned, and/or modify the directory in which the strm files are being placed after a scan.

This enables scanning a particular folder in a teamdrive instead of scanning the entire teamdrive, or to scan the contents of the *My Drive* section.

Note: These flags can only be passed if you execute the script from the terminal. 

### Scanning a particular folder

Add the `--source=<folder-id>` flag while executing the python script to force it to scan a particular directory.

> Note: Check [Getting the Folder ID](#getting-folder-ids) section to get the folder id for a particular folder in Google Drive.


### Modifying the directory where strm files are generated

Add the `--dest=<destination>` flag while executing the python script to store the generated strm files in a particular directory.

If the destination contains a space, wrap it inside the double quotes before adding it as a flag.

#### Getting Folder ID's

You can get the id for a particular folder by opening the folder and copying the id from the url.

For example, in the URL `https://drive.google.com/drive/folders/0AOC6NXsE2KJMUk9PTA`, the folder-id is `0AOC6NXsE2KJMUk9PTA`.

This method can also be used to get the ID of a particular TeamDrive and use it as a [custom argument](#scanning-a-particular-folder) to directly scan the teamdrive.

> #### Example - Using Custom Arguments
> 
> Running the following command will scan a particular folder on Google Drive, and place the store the generated strm files inside the directory `/home/kodi-libraries` instead of resorting to the defaults
>
> `python strm-generator.py --source=0AOC6NXsE2KJMUk9PVA --dest="/home/kodi libraries"`

---

### How is this script better than the existing add-on?

To be honest, I'm not completely sure of this myself. While the add-on is open source, I'm too lazy to take a look at the code and determine why exactly this happens.

What I do know is, this script is as simple as it can be. There is no clever hack, or trick to make this script more robust. Yet, all the tests I ran seem to deny this, while the add-on crashes frequently, this script works perfectly fine (and no, this is **definitely not** because of hardware limitation at my end).

The only cause I can draw for this difference is that this has got something to do with Kodi (or the integration between the add-on and Kodi). Regardless, I noticed a flaw, and wrote a simple script to overcome it effectively.

## How does this script work

The basic functioning of this script revolves around traversing a directory on Google Drive, iterating through each file present in this dirctory and generating strm files for any media file. An important part of this is to be able to recognize media files.

The most important step while creating a strm file is to ensure that the contents of the file are stored in such a manner that they can be parsed by the Google Drive add-on.

The last step above ensures that this script does not need to handle the part of using these strm files to stream the video. Once this script generates the strm files, everything else is being handled by the Kodi add-on, this includes parsing the strm file to get the actual URL, streaming contents from the URL and everything else.

## Advanced Setup

This section contains ideas and suggestions to how you can use this script to get a seamless experience with you Kodi setup.

With a little help of [custom arguments](#custom-arguments) supported by the script, you can set up the script to be run on fixed intervals (with pre-fixed parameters).

For example, I'm on Linux, I've setup a [systemd.service](https://man7.org/linux/man-pages/man5/systemd.service.5.html) to run this script once every couple of days. At every run, the script scans a fixed folder from Google Drive, and places it inside an existing Kodi library.

Whenever I open up Kodi, it automatically scrapes the new files, and adds them to my library. And so, my system automatically fetches any updates on Google Drive, syncs them, and adds them to Kodi without requiring any input from me. 

If needed, the systemd service can be modified to run the script multiple times, scanning different sources each time to be able to scale my current setup to span across multiple teamdrives/folders, all this without requiring any sort of input.

Windows users can achieve the same functionality as systemd.service using [Windows Task Scheduler](https://en.wikipedia.org/wiki/Windows_Task_Scheduler).

In case someone wants to replicate a similar setup as mine, here are some useful links to help you get started.

- [Creating a systemd.service](https://medium.com/@benmorel/creating-a-linux-service-with-systemd-611b5c8b91d6)
- [Using Windows Task Scheduler](https://windowsreport.com/schedule-tasks-windows-10)
- [Setting up Kodi for auto-scan](https://www.howtogeek.com/196025/ask-htg-how-do-you-set-your-xbmc-library-to-automatically-update/)


<!-- ROADMAP -->
## Roadmap

The main aim for this project isn't to replace the exising Google Drive AddOn, but to build upon it and fix the flaws. As such, a large part of what I found missing in the add-on has already been fixed - namely, speed and reliablitly.

Based on the tests I've run at my end, this script is ~20% faster than the Google Drive Add-On, and is a lot more reliable (no crashes so far).

> *For the curious, yes, I ran the test on the exact same source without any modifications. The results are as accurate as possible.*

#### A list of *possible* improvements;
- Improvement(s) on the GUI - updating progress on the terminal while the script is running.
- Multithreading (still not sure on this one) - despite GIL, the execution speed can be improved to some extent.

## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **extremely appreciated**.

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
 

[code-size]: https://img.shields.io/github/languages/code-size/demon-rem/kodi-strm?style=for-the-badge
[language]: https://img.shields.io/github/languages/top/demon-rem/kodi-strm?style=for-the-badge
[license]: https://img.shields.io/github/license/demon-rem/kodi-strm?style=for-the-badge
[latest-release]: https://img.shields.io/github/v/release/demon-rem/kodi-strm?style=for-the-badge
[release-date]: https://img.shields.io/github/release-date/demon-rem/kodi-strm?style=for-the-badge
[issues-url]: https://img.shields.io/github/issues-raw/demon-rem/kodi-strm?style=for-the-badge