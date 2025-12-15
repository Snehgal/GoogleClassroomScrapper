# Classroom Scraper
The program helps the user to download all materials from their Google Classroom locally, sorted in folders \
YouTube video support is yet to be added, but all pdfs and ppts can easily be downloaded using this program

## Installation
- Go to [Google Cloud](https://console.cloud.google.com) from the email ID that the classrooms are on
- Select `Enabled APIs & services` and create a new project
- Select this new project and go to `Enable APIs and Services` and search for "Google Classroom  API" and "Google Drive API" and enable them
-  Go back to  [Google Cloud](https://console.cloud.google.com) and select `OAuth consent screen`, and proceed with setup
- Select 'Internal' if you are using an organisation account (School or College), otherwise select `External`
- Give the App a name and select your email address as the support email and as Developer Contact Info
- Click `Save and Continue`
- In the Data Access screen, click `Add or Remove Scopes` and paste the following in the `Manually add scopes` text box (may have to scroll down to find this text box)
```txt
https://www.googleapis.com/auth/classroom.courses.readonly, https://www.googleapis.com/auth/classroom.topics.readonly, https://www.googleapis.com/auth/classroom.coursework.me, https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly, https://www.googleapis.com/auth/drive.file, https://www.googleapis.com/auth/drive
```
- Click `Add to Table` and `Update`
- Save and Continue
- In the `Audience` Section, under `Test Users` , click `Add Users` and enter your email ID and click `Save`
- Now select the `Clients` tab from the right menu, select `Create Client`
- Select application type `Web Application` and give it a name
- This will create credentials
- Download this file and save it as `credentials.json` in the credentials folder

# Running 
- Open the terminal and navigate to the root directory of the repository
- Run the following command 
```python
pip install -r install.txt
```
- If the above DOES NOT work, run
```python
py -m pip install -r install.txt
```

- To run the scraper, run 
```python
python main.py
```
- All downloaded materials will appear in the `downloads` folder
