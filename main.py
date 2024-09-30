import os
import json
import schedule
import time
import logging
import re
from datetime import datetime, timedelta, UTC
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from youtube_transcript_api import YouTubeTranscriptApi
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from threading import Thread

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define scopes for YouTube, Drive, and Docs APIs
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl',
          'https://www.googleapis.com/auth/drive.file',
          'https://www.googleapis.com/auth/documents']

def load_config():
    if not os.path.exists('config.json'):
        return {"channels": {}}
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Migrate old format to new format if necessary
    if 'youtube_channels' in config:
        new_config = {"channels": {}}
        for channel_id in config['youtube_channels']:
            new_config['channels'][channel_id] = {
                "check_interval": config.get('check_times', {}).get(channel_id, 60),
                "folder_id": config.get('google_drive_folder_id', ""),
                "folder_name": config.get('folder_name', ""),
                "channel_name": "",
                "videos": []
            }
        config = new_config
        save_config(config)
    
    return config

def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

config = load_config()

def get_authenticated_service(api_name, api_version):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                logging.error("Failed to refresh the token. Please re-authenticate.")
                if os.path.exists('token.json'):
                    os.remove('token.json')
                creds = None
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                logging.error(f"Error during authentication: {str(e)}")
                logging.error("Please check your credentials.json file and ensure it's correctly set up.")
                raise
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        return build(api_name, api_version, credentials=creds)
    except Exception as e:
        logging.error(f"Error building {api_name} service: {str(e)}")
        raise

def get_channel_info(youtube, channel_input):
    logging.info(f"Attempting to get channel info for input: {channel_input}")
    try:
        if channel_input.startswith(('UC', 'HC')):
            logging.info("Input recognized as a channel ID")
            channel_id = channel_input
        else:
            # Try to extract channel ID or handle from URL
            patterns = [
                r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/channel\/([a-zA-Z0-9_-]+)',
                r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/user\/([a-zA-Z0-9_-]+)',
                r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/@([a-zA-Z0-9_-]+)'
            ]
            for pattern in patterns:
                match = re.search(pattern, channel_input)
                if match:
                    channel_id_or_handle = match.group(1)
                    logging.info(f"Channel ID or handle extracted from URL: {channel_id_or_handle}")
                    break
            else:
                channel_id_or_handle = channel_input
                if channel_id_or_handle.startswith('@'):
                    channel_id_or_handle = channel_id_or_handle[1:]
                logging.info(f"Using input as channel handle: {channel_id_or_handle}")

            # Search for the channel to get the actual channel ID
            logging.info(f"Searching for channel: {channel_id_or_handle}")
            response = youtube.search().list(
                part="snippet",
                q=channel_id_or_handle,
                type="channel"
            ).execute()
            
            if 'items' in response and len(response['items']) > 0:
                channel_id = response['items'][0]['id']['channelId']
                logging.info(f"Channel ID found from search: {channel_id}")
            else:
                logging.error("No channel found in search results")
                return None

        # Now that we have the channel ID, fetch the channel details
        logging.info(f"Fetching details for channel ID: {channel_id}")
        response = youtube.channels().list(part="snippet", id=channel_id).execute()
        
        if 'items' in response and len(response['items']) > 0:
            channel = response['items'][0]
            result = {
                'id': channel['id'],
                'name': channel['snippet']['title']
            }
            logging.info(f"Channel info retrieved successfully: {result}")
            return result
        else:
            logging.error("No channel details found for the given ID")
            return None
    except Exception as e:
        logging.error(f"Error getting channel info: {str(e)}")
        return None

def get_latest_video(youtube, channel_id):
    try:
        request = youtube.search().list(
            part="id,snippet",
            channelId=channel_id,
            type="video",
            order="date",
            maxResults=1
        )
        response = request.execute()
        
        if 'items' in response and len(response['items']) > 0:
            video = response['items'][0]
            return {
                'id': video['id']['videoId'],
                'title': video['snippet']['title'],
                'published_at': video['snippet']['publishedAt']
            }
        else:
            return None
    except Exception as e:
        logging.error(f"Error getting latest video: {str(e)}")
        return None

def check_for_new_videos(youtube, channel_id, last_check_time):
    try:
        # Format the date correctly for the YouTube API
        published_after = last_check_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        request = youtube.search().list(
            part="id,snippet",
            channelId=channel_id,
            type="video",
            order="date",
            publishedAfter=published_after
        )
        response = request.execute()
        
        new_videos = []
        for item in response.get('items', []):
            new_videos.append({
                'id': item['id']['videoId'],
                'title': item['snippet']['title'],
                'published_at': item['snippet']['publishedAt']
            })
        
        return new_videos
    except Exception as e:
        logging.error(f"Error checking for new videos: {str(e)}")
        return []

def get_video_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return ' '.join([entry['text'] for entry in transcript])
    except Exception as e:
        logging.error(f"Error getting transcript for video {video_id}: {str(e)}")
        return None

def create_google_doc(docs_service, drive_service, title, content, folder_id):
    try:
        doc = docs_service.documents().create(body={'title': title}).execute()
        doc_id = doc.get('documentId')

        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1,
                    },
                    'text': content
                }
            }
        ]

        docs_service.documents().batchUpdate(
            documentId=doc_id, body={'requests': requests}).execute()

        # Move the document to the specified folder
        file = drive_service.files().get(fileId=doc_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents'))
        file = drive_service.files().update(
            fileId=doc_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()

        logging.info(f"Google Doc created with ID: {doc_id}")
        return doc_id
    except Exception as e:
        logging.error(f"Error creating Google Doc: {str(e)}")
        return None

def process_video(youtube, drive_service, docs_service, channel_id, video, folder_id):
    transcript = get_video_transcript(video['id'])
    if transcript:
        # Create a filename with channel name, video title, and upload time
        channel_name = config['channels'][channel_id]['channel_name']
        upload_time = datetime.fromisoformat(video['published_at'].replace('Z', '+00:00')).strftime('%Y%m%d_%H%M%S')
        safe_title = re.sub(r'[^\w\-_\. ]', '_', video['title'])
        doc_title = f"{channel_name}_{safe_title}_{upload_time}_{video['id']}_transcript"
        
        doc_id = create_google_doc(docs_service, drive_service, doc_title, transcript, folder_id)
        if doc_id:
            video_info = {
                "id": video['id'],
                "title": video['title'],
                "published_at": video['published_at'],
                "transcript_doc_id": doc_id
            }
            config['channels'][channel_id]['videos'].append(video_info)
            save_config(config)
            logging.info(f"Processed and created Google Doc for video {video['id']}")
            return True
    return False

def job(channel_id):
    youtube = get_authenticated_service('youtube', 'v3')
    drive_service = get_authenticated_service('drive', 'v3')
    docs_service = get_authenticated_service('docs', 'v1')
    
    last_check_time = datetime.now(UTC) - timedelta(minutes=config['channels'][channel_id]['check_interval'])
    new_videos = check_for_new_videos(youtube, channel_id, last_check_time)
    
    for video in new_videos:
        process_video(youtube, drive_service, docs_service, channel_id, video, config['channels'][channel_id]['folder_id'])

def check_all_channels():
    youtube = get_authenticated_service('youtube', 'v3')
    drive_service = get_authenticated_service('drive', 'v3')
    docs_service = get_authenticated_service('docs', 'v1')
    
    new_videos_found = False
    for channel_id, channel_info in config['channels'].items():
        last_video = channel_info['videos'][-1] if channel_info['videos'] else None
        last_check_time = datetime.fromisoformat(last_video['published_at'].replace('Z', '+00:00')) if last_video else datetime.now(UTC) - timedelta(days=7)
        new_videos = check_for_new_videos(youtube, channel_id, last_check_time)
        
        for video in new_videos:
            # Check if the video has already been processed
            if not any(v['id'] == video['id'] for v in channel_info['videos']):
                if process_video(youtube, drive_service, docs_service, channel_id, video, channel_info['folder_id']):
                    new_videos_found = True
            else:
                logging.info(f"Video {video['id']} has already been processed. Skipping.")
    
    if new_videos_found:
        logging.info("Finished checking all channels. New videos found and processed.")
        return "Found new videos"
    else:
        logging.info("Finished checking all channels. No new videos found.")
        return "No new videos found"

def schedule_jobs():
    schedule.clear()
    for channel_id, channel_info in config['channels'].items():
        interval = channel_info['check_interval']
        schedule.every(interval).minutes.do(job, channel_id)
        logging.info(f"Scheduled check for channel {channel_id} every {interval} minutes")

def validate_folder_id(folder_id):
    try:
        drive_service = get_authenticated_service('drive', 'v3')
        folder = drive_service.files().get(fileId=folder_id, fields='name').execute()
        return True, folder['name']
    except Exception as e:
        logging.error(f"Error validating folder ID: {str(e)}")
        return False, str(e)

def get_drive_folders():
    try:
        drive_service = get_authenticated_service('drive', 'v3')
        results = drive_service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and 'root' in parents",
            fields="nextPageToken, files(id, name)",
            pageSize=1000
        ).execute()
        folders = results.get('files', [])
        logging.info(f"Retrieved {len(folders)} folders from Google Drive")
        return [{'id': folder['id'], 'name': folder['name']} for folder in folders]
    except Exception as e:
        logging.error(f"Error fetching Google Drive folders: {str(e)}")
        return []

@app.route('/')
def index():
    folders = get_drive_folders()
    return render_template('index.html', config=config, folders=folders)

@app.route('/add_channel', methods=['POST'])
def add_channel():
    channel_input = request.form['channel_id']
    check_interval = int(request.form['check_interval'])
    folder_id = request.form['folder_id']
    
    logging.info(f"Attempting to add channel with input: {channel_input}")
    youtube = get_authenticated_service('youtube', 'v3')
    channel_info = get_channel_info(youtube, channel_input)
    
    if not channel_info:
        logging.error(f"Failed to get channel info for input: {channel_input}")
        return jsonify({"success": False, "message": 'Invalid YouTube channel URL or ID'})
    
    logging.info(f"Channel info retrieved: {channel_info}")
    
    is_valid, folder_name = validate_folder_id(folder_id)
    if not is_valid:
        logging.error(f"Invalid folder ID: {folder_id}")
        return jsonify({"success": False, "message": f'Invalid folder ID: {folder_name}'})
    
    drive_service = get_authenticated_service('drive', 'v3')
    docs_service = get_authenticated_service('docs', 'v1')
    
    latest_video = get_latest_video(youtube, channel_info['id'])
    if latest_video:
        transcript = get_video_transcript(latest_video['id'])
        if transcript:
            channel_name = channel_info['name']
            upload_time = datetime.fromisoformat(latest_video['published_at'].replace('Z', '+00:00')).strftime('%Y%m%d_%H%M%S')
            safe_title = re.sub(r'[^\w\-_\. ]', '_', latest_video['title'])
            doc_title = f"{channel_name}_{safe_title}_{upload_time}_{latest_video['id']}_transcript"
            
            doc_id = create_google_doc(docs_service, drive_service, doc_title, transcript, folder_id)
            if doc_id:
                config['channels'][channel_info['id']] = {
                    "check_interval": check_interval,
                    "folder_id": folder_id,
                    "folder_name": folder_name,
                    "channel_name": channel_info['name'],
                    "videos": [{
                        "id": latest_video['id'],
                        "title": latest_video['title'],
                        "published_at": latest_video['published_at'],
                        "transcript_doc_id": doc_id
                    }]
                }
                save_config(config)
                schedule_jobs()
                logging.info(f"Channel {channel_info['name']} added successfully")
                return jsonify({"success": True, "message": f'Channel {channel_info["name"]} added successfully. Latest video transcript uploaded as Google Doc.'})
            else:
                logging.warning(f"Failed to create Google Doc for channel {channel_info['name']}")
                return jsonify({"success": False, "message": f'Channel added but failed to create Google Doc for the transcript.'})
        else:
            logging.warning(f"Failed to get transcript for the latest video of channel {channel_info['name']}")
            return jsonify({"success": False, "message": f'Channel added but failed to get transcript for the latest video.'})
    else:
        logging.warning(f"No videos found or failed to get latest video for channel {channel_info['name']}")
        return jsonify({"success": False, "message": f'Channel added but no videos found or failed to get latest video.'})

@app.route('/remove_channel/<channel_id>')
def remove_channel(channel_id):
    if channel_id in config['channels']:
        del config['channels'][channel_id]
        save_config(config)
        schedule_jobs()
        flash(f'Channel {channel_id} removed successfully', 'success')
    return redirect(url_for('index'))

@app.route('/update_channel', methods=['POST'])
def update_channel():
    channel_id = request.form['channel_id']
    check_interval = int(request.form['check_interval'])
    folder_id = request.form['folder_id']
    
    is_valid, folder_name = validate_folder_id(folder_id)
    if not is_valid:
        flash(f'Invalid folder ID: {folder_name}', 'error')
        return redirect(url_for('index'))
    
    config['channels'][channel_id].update({
        "check_interval": check_interval,
        "folder_id": folder_id,
        "folder_name": folder_name
    })
    save_config(config)
    schedule_jobs()
    flash(f'Channel {channel_id} updated successfully', 'success')
    return redirect(url_for('index'))

@app.route('/check_now')
def check_now():
    result = check_all_channels()
    flash(result, 'info')
    return redirect(url_for('index'))

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# if __name__ == "__main__":
#     schedule_jobs()
#     schedule_thread = Thread(target=run_schedule)
#     schedule_thread.start()
#     app.run(debug=True, use_reloader=False)

if __name__ == "__main__":
    schedule_jobs()
    schedule_thread = Thread(target=run_schedule)
    schedule_thread.start()
    port = int(os.environ.get('PORT', 8888))
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode, use_reloader=False)