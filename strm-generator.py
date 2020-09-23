# The main script responsible for generating .strm files as needed.

from os.path import exists
from pickle import dump as dump_pickle
from pickle import load as load_pickle
from typing import List, Optional

from re import match
from colorama import Fore, Style
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build


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
            pageToken=nextPageToken).execute()

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
            id = input('teamdrive > ')

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
