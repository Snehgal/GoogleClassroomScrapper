from __future__ import print_function
import os
import re
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

# Define scopes for the APIs
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.announcements.readonly',
    'https://www.googleapis.com/auth/classroom.topics.readonly',
    'https://www.googleapis.com/auth/classroom.coursework.me',
    'https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive'
]

# Define paths for credentials and token
CREDENTIALS_PATH = 'credentials/credentials.json'
TOKEN_PATH = 'credentials/token.json'

def authenticate():
    """Authenticate and return the credentials."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception as e:
            print(f"Error loading token: {e}")
            creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Token refresh failed ({e}). Re-authenticating...")
                creds = None
        
        if not creds:
            # Delete old token if it exists and causes issues
            if os.path.exists(TOKEN_PATH):
                os.remove(TOKEN_PATH)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    
    return creds

def sanitize(name):
    """Sanitize folder and file names by replacing invalid characters."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def get_topic_name(topic_id, topics):
    """Get topic name from topic ID."""
    if not topics or 'topic' not in topics:
        return None
    
    for topic in topics['topic']:
        if topic['topicId'] == topic_id:
            return sanitize(topic['name'])
    return None

def download_file(drive_service, file_id, file_path):
    """Download a file from Google Drive using the provided file_id."""
    try:
        request = drive_service.files().get_media(fileId=file_id)
        with open(file_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Downloading {os.path.basename(file_path)}: {int(status.progress() * 100)}%")
        print(f"Downloaded file to {file_path}")
    except HttpError as error:
        print(f'An error occurred: {error}')

def download_assets(drive_service, save_location, material_assets):
    """Download assets from materials."""
    file_name = "unknown_file"
    if material_assets.get("driveFile"):
        try:
            file_id = material_assets["driveFile"]["driveFile"]["id"]
            file_name = sanitize(material_assets["driveFile"]["driveFile"].get("title", "Other"))
            file_path = os.path.join(save_location, file_name)
            
            if not os.path.exists(save_location):
                os.makedirs(save_location)

            if not os.path.exists(file_path):
                print(f"Downloading file: {file_name}")
                download_file(drive_service, file_id, file_path)
            else:
                print(f"{os.path.basename(file_path)} already exists")
        except Exception as e:
            print(f"Error while downloading file: {file_name} in {save_location}")
            print("Error details:", e)

def download_announcement_files(classroom_service, drive_service, course_id, course_folder):
    """Download announcement files to Misc folder."""
    misc_folder = os.path.join(course_folder, "Misc")
    os.makedirs(misc_folder, exist_ok=True)
    
    try:
        announcements = classroom_service.courses().announcements().list(courseId=course_id).execute()
        
        if announcements.get('announcements'):
            for announcement in announcements['announcements']:
                if 'materials' in announcement:
                    for material_assets in announcement['materials']:
                        download_assets(drive_service, misc_folder, material_assets)
    except HttpError as error:
        print(f'An error occurred while fetching announcements: {error}')

def download_coursework_files(classroom_service, drive_service, course_id, course_folder, topics):
    """Download coursework (assignments) files."""
    try:
        coursework = classroom_service.courses().courseWork().list(courseId=course_id).execute()
        
        if coursework.get('courseWork'):
            for work in coursework['courseWork']:
                if 'materials' in work:
                    work_title = sanitize(work.get('title', 'Untitled'))
                    
                    for material_assets in work['materials']:
                        if work.get("topicId"):
                            topic_name = get_topic_name(topic_id=work["topicId"], topics=topics)
                            if topic_name:
                                save_location = os.path.join(course_folder, topic_name, work_title)
                            else:
                                save_location = os.path.join(course_folder, work_title)
                        else:
                            save_location = os.path.join(course_folder, work_title)
                        download_assets(drive_service, save_location, material_assets)
    except HttpError as error:
        print(f'An error occurred while fetching coursework: {error}')

def main():
    """Main function to download materials from Google Classroom."""
    creds = authenticate()
    classroom_service = build('classroom', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # Fetch and display all courses
    courses = classroom_service.courses().list().execute().get('courses', [])
    if not courses:
        print("No courses found.")
        return

    print("Available courses:")
    for index, course in enumerate(courses):
        print(f"{index + 1}. {course['name']}")

    # Prompt user to select courses by index
    selected_courses = input("Enter the numbers of the courses you wish to download (comma-separated): ")
    selected_indices = [int(num.strip()) - 1 for num in selected_courses.split(",") if num.strip().isdigit()]

    # Validate selected indices
    for index in selected_indices:
        if index < 0 or index >= len(courses):
            print(f"Invalid selection: {index + 1}")
            return

    for index in selected_indices:
        course = courses[index]
        course_id = course['id']
        course_name = sanitize(course['name'])
        course_folder = os.path.join("downloads", course_name)
        print(f"\nCreating directory {course_folder}")
        os.makedirs(course_folder, exist_ok=True)

        # Fetch topics
        topics = classroom_service.courses().topics().list(courseId=course_id).execute()
        
        # Fetch coursework materials
        course_work_materials = classroom_service.courses().courseWorkMaterials().list(courseId=course_id).execute()
        
        if course_work_materials.get('courseWorkMaterial'):
            for material in course_work_materials['courseWorkMaterial']:
                if 'materials' in material.keys() and 'title' in material.keys():
                    aula_name = sanitize(material["title"])
                    for material_assets in material["materials"]:
                        if material.get("topicId"):
                            topic_name = get_topic_name(topic_id=material["topicId"], topics=topics)
                            if topic_name:
                                save_location = os.path.join(course_folder, topic_name, aula_name)
                            else:
                                save_location = os.path.join(course_folder, aula_name)
                        else:
                            save_location = os.path.join(course_folder, aula_name)
                        download_assets(drive_service, save_location, material_assets)
        
        # Download coursework (assignments) files
        print(f"\nDownloading coursework/assignments for {course_name}...")
        download_coursework_files(classroom_service, drive_service, course_id, course_folder, topics)
        
        # Download announcement files to Misc folder
        print(f"\nDownloading announcements for {course_name}...")
        download_announcement_files(classroom_service, drive_service, course_id, course_folder)

    print("\nDownload complete!")

if __name__ == '__main__':
    main()
