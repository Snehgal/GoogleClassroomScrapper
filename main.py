from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import os

# Define scopes for the APIs
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',         # View course details
    'https://www.googleapis.com/auth/classroom.student-submissions.me.readonly',  # Read coursework
    'https://www.googleapis.com/auth/classroom.announcements.readonly',  # Read announcements
    'https://www.googleapis.com/auth/drive'                     # Read Drive files
]


# Define paths for credentials and token
CREDENTIALS_PATH = 'credentials/credentials.json'
TOKEN_PATH = 'credentials/token.json'

def authenticate():
    # Check if token exists, else perform the OAuth flow
    if os.path.exists(TOKEN_PATH):
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials for future runs
        with open(TOKEN_PATH, 'w') as token_file:
            token_file.write(creds.to_json())
    return creds

def download_materials():
    creds = authenticate()
    classroom_service = build('classroom', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    courses = classroom_service.courses().list().execute().get('courses', [])
    print(courses)
    for course in courses:
        print(f"Processing course: {course['name']}")
        coursework = classroom_service.courses().courseWork().list(courseId=course['id']).execute().get('courseWork', [])
        for work in coursework:
            if 'materials' in work:
                for material in work['materials']:
                    if 'driveFile' in material:
                        file_id = material['driveFile']['driveFile']['id']
                        file_name = material['driveFile']['driveFile']['title']
                        request = drive_service.files().get_media(fileId=file_id)
                        with open(file_name, 'wb') as fh:
                            downloader = MediaIoBaseDownload(fh, request)
                            done = False
                            while not done:
                                status, done = downloader.next_chunk()
                                print(f"Downloading {file_name}: {int(status.progress() * 100)}%")

download_materials()
