# The main script responsible for generating .strm files as needed.

import sys
from os import getcwd, mkdir, system
from shutil import rmtree
from os.path import exists, isdir, join
from pickle import dump as dump_pickle
from pickle import load as load_pickle
from re import match, sub
from time import sleep
from typing import Dict, List, Optional

from colorama import Fore, Style
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

files = 0
directories = 0


def authenticate() -> Resource:
    """
        A simple method to authenticate a user with Google Drive API. For the first
        run (or if script does not have the required permissions), this method will
        ask the user to login with a browser window, and then save a pickle file with
        the credentials obtained.

        For subsequent runs, this pickle file will be used directly, ensuring that the
        user does not have to login for every run of this script.

        Returns
        --------
        An instance of `Resource` that can be used to interact with the Google Drive API.
    """

    # Simple declartion, will be populated if credentials are present.
    creds: Optional[Credentials] = None

    # The scope that is to be requested.
    SCOPES = ['https://www.googleapis.com/auth/drive']

    if exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds: Credentials = load_pickle(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            dump_pickle(creds, token)

    service: Resource = build('drive', 'v3', credentials=creds)
    return service


def select_teamdrive(service: Resource) -> str:
    """
        Allows the user to select the teamdrive for which strm files are to be generated.
        Will be used to let the user select a source incase a direct id is not supplied.

        Remarks
        --------
        Will internally handle any error/unexpected input. The only value returned by
        this method will be the id of the teamdrive that is to be used.

        Returns
        --------
        String containing the ID of the teamdrive selected by the user.
    """

    # Initializing as non-zero integer to ensure that the loop runs once.
    nextPageToken: str = None

    # Creating a list with the first element filled. Since the numbers being displayed
    # on the screen start from 1, filling the first element of the list with trash
    # ensures that the input from the user can used directly.
    teamdrives: List[str] = ['']

    counter: int = 1
    while True:
        result = service.drives().list(
            pageSize=100,
            pageToken=nextPageToken
        ).execute()

        for item in result['drives']:
            output = f'  {counter} ' + ('/' if counter % 2 else '\\')
            output += f'\t{item["name"]}{Style.RESET_ALL}'

            print(f'{Fore.GREEN if counter % 2 else Fore.CYAN}{output}')

            # Adding the id for this teamdrive to the list of teamdrives.
            teamdrives.append(item['id'])

            # Finally, incrementing the counter
            counter += 1

        try:
            nextPageToken = result['nextPageToken']
            if not nextPageToken:
                break
        except KeyError:
            # Key error will occur if there is no nextpage token -- breaking out of
            # the loop in such scenario.
            break

    # Adding an extra line.
    print()

    while True:
        print('Select a teamdrive from the list above.')
        try:
            id = input('teamdrive> ')

            if not match(r'^[0-9]+$', id):
                # Handling the scenario if the input is not an integer. Using regex
                # since direct type-cast to float will also accept floating-point,
                # which would be incorrect.
                raise ValueError

            id = int(id)
            if id <= 0 or id > len(teamdrives):
                # Handling the scenario if the input is not within the accepted range.
                # The zero-eth element of this list is garbage value, thus discarding
                # the input even at zero.
                raise ValueError

            # If the flow-of-control reaches here, the returning the id of the teamdrive
            # located at this position.
            return teamdrives[id]
        except ValueError:
            # Will reach here if the user enters a non-integer input
            print(f'\t{Fore.RED}Incorrect input detected. {Style.RESET_ALL}\n')


def walk(origin_id: str, service: Resource, cur_path: str, item_details: Dict[str, str]):
    """
        Traverses directories in Google Drive and replicates the file/folder structure similar to
        Google Drive.

        This method will create an equvivalent `.strm` file for every video file found inside a
        particular directory. The end result will be the complete replication of the entire directory
        structure with just the video files with each file being an strm file pointing to the original
        file on the network.

        Parameters
        -----------
        origin_id: String containing the id of the original directory that is to be treated as the source.
        Every directory present inside this directory will be traversed, and a `.strm` file will be generated
        for every video file present inside this directory. \n
        service: Instance of `Resource` object used to interact with Google Drive API. \n
    """

    global files, directories

    if not isinstance(origin_id, str) or not isinstance(service, Resource):
        raise TypeError('Unexpected argument type')

    # print(item_details)
    if item_details['mimeType'] != 'application/vnd.google-apps.folder':
        raise TypeError('Expected the id for a directory')

    # Updating the current path to be inside the path where this directory is to be created.
    cur_path = join(cur_path, item_details['name'])

    # Creating the root directory for this search.
    try:
        mkdir(cur_path)
    except:
        pass

    page_token = None

    while True:
        result = service.files().list(
            pageSize=1000,
            pageToken=page_token,
            fields='files(name, id, mimeType, teamDriveId)',
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            q=f"'{origin_id}' in parents"
        ).execute()

        # print(f'Found {len(result["files"])}')
        for item in result['files']:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # If the current object is a folder, recursively calling the same method.
                directories += 1
                walk(item['id'], service, cur_path, item)
            elif 'video' in item['mimeType'] or match(r'.*\.(mkv|mp4)$', item['name']):
                try:
                    file_content = f'plugin://plugin.googledrive/?action=play&item_id={item["id"]}'
                    if 'teamDriveId' in item:
                        # Adding this part only for items present in a teamdrive.
                        file_content += f'&item_driveid={item["teamDriveId"]}&teamDriveId={item["teamDriveId"]}'

                    file_content += f'&content_type=video'
                    with open(join(cur_path, item['name']+'.strm'), 'w+') as f:
                        f.write(file_content)
                    files += 1
                except:
                    pass

        if 'nextPageToken' not in result:
            break


if __name__ == '__main__':
    # Starting by authenticating the connection.
    service = authenticate()

    destination = getcwd()
    source = None

    # Pattern(s) that are to be used to match against the source argument. The group is important since
    # this pattern is also being used to extract the value from argument.
    pattern_source = r'^--source=(.*)'
    patter_dest = r'^--dest="?(.*)"?'

    # Looping over all arguments that are passed to the script. The first (zeroe-th) value shall be the
    # name of the python script.
    for i in range(len(sys.argv)):
        if i == 0:
            # Skipping the first arguemnt, this would be the name of the python script file.
            continue

        if match(pattern_source, sys.argv[i]) and not source:
            # Pattern matching to select the source if the source is null. A better pattern match
            # can be obtained by ensuring that the only accepted value for the source is
            # alpha-numeric charater or hypen/underscores. Skipping this implementation for now as it
            # requires a testing.

            # Extracting id from the argument using substitution. Substituting everything from the
            # argument string except for the value :p
            source = sub(pattern_source, r'\1', sys.argv[i])
        elif match(patter_dest, sys.argv[i]):
            # Again, extracting the value using regex substitution.
            destination = sub(patter_dest, r'\1', sys.argv[i])

            if not isdir(destination):
                print(f'Error: `{sys.argv[i]}` is not a directory.\n')
                exit(10)  # Force quit.

        else:
            print(f'Unknown argument detected `{sys.argv[i]}`')
            exit(10)  # Non-zero exit code to indicate error.

    if not isinstance(source, str):
        # If a source has not been set, asking the user to select a teamdrive as root.
        source = select_teamdrive(service)

    # Attempting to get the details on the folder/teamdrive being used as the source.
    item_details = service.files().get(
        fileId=source,
        supportsAllDrives=True
    ).execute()

    if 'teamDriveId' in item_details and item_details['id'] == item_details['teamDriveId']:
        # If the source is a teamdrive, attempting to fetch details for the teamdrive instead.
        item_details = service.drives().get(
            teamDriveId=item_details['teamDriveId']
        ).execute()

    # Clearing the destination directory (if it exists).
    final_path=join(destination, item_details['name'])
    if isdir(final_path):
        rmtree(final_path)

    print(f'\n\tSaving the output at `{destination}`')

    # Calling the method to walk through the drive directory.
    walk(source, service, destination, item_details)

    print(f'Completed. Traversed through {directories} directories and {files} files.')
