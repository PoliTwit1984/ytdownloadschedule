# YouTube Transcript Downloader

This application automatically checks specified YouTube channels for new videos, retrieves their transcripts, and uploads them to Google Drive. It features a web interface for easy management of channels, schedules, and Google Drive folder selection.

## Features

- Add multiple YouTube channels for monitoring
- Set custom check intervals for each channel (more frequent than daily checks now supported)
- Select different Google Drive folders for each channel's transcripts
- Web interface for easy management of channels and settings
- Self-testing mechanism: downloads and uploads the latest video's transcript when adding a channel
- Improved channel ID extraction and validation
- Displays publication date for each video
- Shows multiple videos per channel with their transcripts
- "Check All Channels Now" button for immediate checking of all channels

## Setup

1. Clone this repository:
   ```
   git clone <repository_url>
   cd ytdownloadschedule
   ```

2. Create and activate a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up Google Cloud Project and enable YouTube Data API v3 and Google Drive API:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the YouTube Data API v3 and Google Drive API for your project
   - Create credentials (OAuth 2.0 Client ID) for a desktop application
   - In the OAuth consent screen, add the following scopes:
     * https://www.googleapis.com/auth/youtube.force-ssl
     * https://www.googleapis.com/auth/drive.file
     * https://www.googleapis.com/auth/drive.metadata.readonly
   - Download the credentials and save them as `credentials.json` in the project root directory

   **Important:** The `credentials.json` file is crucial for the application to authenticate with Google's APIs. Make sure it's placed in the same directory as `main.py`.

5. Run the application:
   ```
   python main.py
   ```

6. Open a web browser and go to `http://localhost:5000` to access the web interface.

## Usage

Through the web interface, you can:

1. Add YouTube channels:
   - Enter one of the following:
     * Full YouTube channel URL (e.g., https://www.youtube.com/@ChannelName)
     * Channel ID (e.g., UCxxxxxxxxxxxxxxxx)
     * Channel handle (e.g., @ChannelName)
     * Channel name (the application will search for the channel)
   - Set a custom check interval for each channel (in HH:MM format, e.g., 01:00 for hourly checks)
   - Select a Google Drive folder for storing transcripts for each channel
   - The application will automatically download and upload the transcript of the latest video as a test

2. Update existing channels:
   - Modify the check interval
   - Change the Google Drive folder for transcript storage

3. Remove channels

4. View information about processed videos for each channel:
   - Video title and ID
   - Publication date
   - Link to the transcript file on Google Drive

5. Check all channels immediately:
   - Click the "Check All Channels Now" button at the top of the page
   - This will initiate an immediate check for new videos on all added channels
   - The process runs in the background, and you'll see a notification when it starts

The application will run continuously, checking for new videos at the specified intervals for each channel. When a new video is found, it will download the transcript, upload it to the selected Google Drive folder for that channel, and update the web interface with the new video information.

## Notes

- On first run, you'll be prompted to authorize the application to access your Google account. Follow the provided URL and grant the necessary permissions.
- The application stores an access token in `token.json`. Do not share this file as it grants access to your Google account.
- Ensure your Google account has sufficient Drive storage for the transcripts.
- The web interface now displays multiple videos per channel, each with its publication date and transcript link.
- The "Check All Channels Now" feature is useful for immediate updates or if you suspect the regular checks might have missed something.

## Troubleshooting

1. **Authentication Issues**:
   - If you encounter authentication errors or "insufficient permission" messages, delete the `token.json` file (if it exists) and run the application again.
   - Ensure your `credentials.json` file is up to date and correctly configured in the Google Cloud Console.
   - Make sure you've added all the required API scopes in the OAuth consent screen.

2. **API Quota or Rate Limit Issues**:
   - If you encounter quota or rate limit errors, consider adjusting the check intervals to be less frequent.
   - Be cautious when using the "Check All Channels Now" feature, as it may consume a significant portion of your daily API quota if you have many channels.
   - You may need to request higher quotas in the Google Cloud Console for your project.

3. **Invalid Channel URL or ID**:
   - If you receive an error when adding a channel, double-check the URL, ID, or name you've entered.
   - Try using different formats (full URL, channel ID, handle, or name) if one doesn't work.

4. **Google Drive Folder Selection**:
   - If you don't see any folders in the dropdown, ensure that you have folders in your Google Drive root directory.
   - If folders are not loading, try refreshing the page or restarting the application.

5. **Check Interval Format**:
   - Ensure you're entering the check interval in the correct format (HH:MM).
   - The minimum interval is 1 minute (00:01), but it's recommended to use longer intervals to avoid API quota issues.

6. **Self-Test Failures**:
   - If the application fails to download or upload the latest video's transcript when adding a channel, check the console for error messages.
   - Ensure the channel has public videos and that transcripts are available.

7. **Missing Video Information**:
   - If you don't see video information for a channel, it may be because no videos have been processed yet. Wait for the next scheduled check, use the "Check All Channels Now" button, or try removing and re-adding the channel.

8. **"Check All Channels Now" Not Updating**:
   - The check runs in the background and may take some time, especially if you have many channels.
   - Refresh the page after a few minutes to see updated results.
   - Check the console for any error messages if no updates appear after a significant wait.

For any other issues, please check the application logs or open an issue in the repository.

## Security Note

Always keep your `credentials.json` and `token.json` files secure. Do not share them or commit them to version control, as they contain sensitive information that grants access to your Google account.