# YouTube Transcript Downloader

This application automatically checks specified YouTube channels for new videos, retrieves their transcripts, and uploads them to Google Drive as Google Docs. It features a web interface for easy management of channels, schedules, and Google Drive folder selection.

## Features

- Add multiple YouTube channels for monitoring
- Set custom check intervals for each channel
- Select different Google Drive folders for each channel's transcripts
- Web interface for easy management of channels and settings
- Automatic checking for new videos and transcript uploading
- Manual "Check All Channels Now" functionality

## Project Structure

The main components of this project are:

1. `main.py`: This file contains the backend logic, including:
   - Flask application setup
   - YouTube and Google Drive API interactions
   - Data processing and storage logic
   - Scheduling logic for periodic checks

2. `templates/index.html`: This file contains the frontend code, including:
   - HTML structure for the web interface
   - CSS styles for formatting (embedded in the HTML)
   - JavaScript for client-side interactivity (embedded in the HTML)

3. `requirements.txt`: Lists all Python dependencies for the project.

4. `config.json`: Stores the configuration for the application (automatically generated).

5. `.gitignore`: Specifies files and directories that should not be tracked by Git.

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
   - Download the credentials and save them as `credentials.json` in the project root directory

5. Run the application:
   ```
   python main.py
   ```

6. Open a web browser and go to `http://localhost:5000` to access the web interface.

## Usage

Through the web interface, you can:

1. Add YouTube channels:
   - Enter a YouTube channel URL, ID, or handle
   - Set a custom check interval
   - Select a Google Drive folder for storing transcripts

2. Update existing channels:
   - Modify the check interval
   - Change the Google Drive folder for transcript storage

3. Remove channels

4. View information about processed videos for each channel

5. Manually trigger a check for all channels

The application will run continuously, checking for new videos at the specified intervals for each channel. When a new video is found, it will download the transcript and upload it as a Google Doc to the selected Google Drive folder for that channel.

## Notes

- On first run, you'll be prompted to authorize the application to access your Google account. Follow the provided URL and grant the necessary permissions.
- The application stores an access token in `token.json`. Do not share this file as it grants access to your Google account.
- Ensure your Google account has sufficient Drive storage for the transcripts.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## Acknowledgments

- YouTube Data API
- Google Drive API
- Flask
- youtube-transcript-api
