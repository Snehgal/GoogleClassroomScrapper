from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import os
import re

# Define scopes for the APIs
SCOPES = ["https://www.googleapis.com/auth/classroom.courses.readonly",
          "https://www.googleapis.com/auth/classroom.topics.readonly",
          "https://www.googleapis.com/auth/classroom.coursework.me",
          "https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly",
          "https://www.googleapis.com/auth/drive.file",
          "https://www.googleapis.com/auth/drive"]


def get_topic_name(topic_id, topics):
    topic_name = None
    for topic in topics['topic']:
        if topic['topicId'] == topic_id:
            topic_name = topic['name']
    sanitize(topic_name)
    return topic_name

# Define paths for credentials and token
CREDENTIALS_PATH = 'credentials/credentials.json'
TOKEN_PATH = 'credentials/token.json'

def authenticate():
    """Authenticate and return the credentials."""
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

def sanitize(name):
    """Sanitize folder and file names by replacing invalid characters."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def download_file(drive_service, file_id, file_path):
    """Download a file from Google Drive using the provided file_id."""
    request = drive_service.files().get_media(fileId=file_id)
    with open(file_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Downloading {os.path.basename(file_path)}: {int(status.progress() * 100)}%")
    print(f"Downloaded file to {file_path}")

def download_assets(drive_service, save_location, material_assets):
    if material_assets.get("driveFile"):
        try:
            file_id = material_assets["driveFile"]["driveFile"]["id"]
            file_name = sanitize(material_assets["driveFile"]["driveFile"]["title"].replace(" ", ""))
            # Sanitize the full path, not just the file name
            file_path = os.path.join(save_location, file_name)
            
            if not os.path.exists(save_location):
                os.makedirs(save_location)

            if not os.path.exists(file_path):
                print(f"Downloading file: {file_name}")
                download_file(drive_service, file_id, file_path)
            else:
                print(f"{os.path.basename(save_location)} already exists")
        except Exception as e:
            print(f"Error while downloading file: {file_name} in {save_location}")
            print("Error details:", e)

def download_materials():
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
        # Create a folder for the course
        os.makedirs(course_folder, exist_ok=True)

        # Fetch coursework materials
        
        topics = classroom_service.courses().topics().list(courseId=course_id).execute()
        course_work_materials = classroom_service.courses().courseWorkMaterials().list(courseId=course_id).execute()
        
        if course_work_materials.get('courseWorkMaterial'):
            for material in course_work_materials['courseWorkMaterial']:
                if 'materials' in material.keys() and 'title' in material.keys():
                    aula_name = material["title"].replace(" ", "")
                    for material_assets in material["materials"]:
                        if material.get("topicId"):
                            topic_name = sanitize(get_topic_name(topic_id=material["topicId"], topics=topics).replace(" ", ""))
                            course_name = course_name.replace(" ", "")
                            #os.getcwd() ou cloud_path
                            save_location = os.path.join(course_folder,sanitize(topic_name),sanitize(aula_name))
                        else:
                            save_location = os.path.join(course_folder,aula_name)
                        download_assets(drive_service,save_location,material_assets)
        else:
            pass

    print("\nDownload complete!")

# Run the script
download_materials()
