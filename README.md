# YouTube to Spotify Liked Songs Transfer

This Python script transfers your liked videos from YouTube to Spotify by adding the songs to your Spotify liked songs or a new playlist based on your choice.

---

## 🎵 Features

- **OAuth 2.0 Authentication**: Secure authentication with both YouTube Data API and Spotify Web API
- **Complete Video Retrieval**: Fetches all liked videos from your YouTube account
- **Smart Song Detection**: Extracts song and artist information from video titles using advanced regex patterns
- **Intelligent Spotify Search**: Uses multiple search query formats to maximize track matching accuracy
- **User Choice**: Choose between adding songs to your liked songs or creating a custom playlist
- **Batch Processing**: Efficiently handles large numbers of songs with API-compliant batch operations
- **Comprehensive Reporting**: Detailed progress updates and final transfer summary
- **Error Handling**: Robust error handling for API rate limits and network issues

---

## 📋 Prerequisites

- **Python 3.7 or higher**
- **Google Cloud project** with YouTube Data API enabled
- **Spotify Developer account** with an app created
- **Active internet connection** for API calls

---

## 🚀 Setup Instructions

### 1. Google Cloud Console Setup

#### Step 1.1: Create a Google Cloud Project
1. Navigate to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click **"New Project"**
4. Enter a project name (e.g., "YouTube to Spotify Transfer")
5. Click **"Create"**

#### Step 1.2: Enable YouTube Data API v3
1. In your project dashboard, go to **"APIs & Services"** → **"Library"**
2. Search for **"YouTube Data API v3"**
3. Click on it and press **"Enable"**

#### Step 1.3: Configure OAuth Consent Screen
1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Choose **"External"** user type
3. Fill in the required information:
   - **App name**: "YouTube to Spotify Transfer"
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
4. Click **"Save and Continue"**
5. On the **"Scopes"** page, click **"Save and Continue"** (no additional scopes needed)
6. On the **"Test users"** page:
   - Click **"Add users"**
   - Enter your email address
   - Click **"Save and Continue"**

#### Step 1.4: Create OAuth 2.0 Credentials
1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. Choose **"Desktop application"**
4. Enter a name (e.g., "YouTube to Spotify Desktop App")
5. Click **"Create"**
6. **Download the JSON file** and save it as `youtube_client_secrets.json` in your project directory

### 2. Spotify Developer Dashboard Setup

#### Step 2.1: Create a Spotify App
1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Log in with your Spotify account
3. Click **"Create an App"**
4. Fill in the details:
   - **App name**: "YouTube to Spotify Transfer"
   - **App description**: "Transfer liked videos from YouTube to Spotify"
   - Check the boxes for terms of service
5. Click **"Create"**

#### Step 2.2: Configure App Settings
1. In your newly created app, click **"Settings"**
2. In the **"Redirect URIs"** section:
   - Click **"Edit"**
   - Add: `http://127.0.0.1:8080`
   - Click **"Add"**
   - Click **"Save"**
3. Copy your **Client ID** and **Client Secret** (you'll need these for the script)

### 3. Python Environment Setup

#### Step 3.1: Install Required Packages
```
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client spotipy requests
```


#### Step 3.2: Configure the Script
1. Open the Python script in your preferred editor
2. Update the following variables in the `main()` function:

```
YOUTUBE_CLIENT_SECRETS_FILE = "youtube_client_secrets.json" # Path to your downloaded JSON file
SPOTIFY_CLIENT_ID = "your_actual_spotify_client_id" # Replace with your Spotify Client ID
SPOTIFY_CLIENT_SECRET = "your_actual_spotify_client_secret" # Replace with your Spotify Client Secret
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8080" # Keep this as is
```

---

## 🔧 How It Works

### **Authentication Process**
1. **YouTube Authentication**: Opens a browser window for Google OAuth 2.0 login
2. **Spotify Authentication**: Opens a browser window for Spotify OAuth 2.0 login
3. **Token Management**: Automatically handles access tokens and refresh tokens

### **Data Processing Pipeline**
1. **Fetch Liked Videos**: Retrieves all videos from your YouTube "Liked Videos" playlist
2. **Song Extraction**: Analyzes video titles using multiple regex patterns:
- `Artist - Song`
- `Artist: Song`
- `Artist "Song"`
- `Song by Artist`
3. **Spotify Search**: Uses multiple search strategies for better matching:
- Exact track and artist search
- Quoted search terms
- General keyword search
- Track-specific and artist-specific searches

### **User Interaction**
1. **Choice Prompt**: After processing, you choose between:
- Adding songs to your Spotify liked songs
- Creating a new playlist with a custom name
2. **Batch Processing**: Songs are added in optimal batch sizes (50 for liked songs, 100 for playlists)

### **Results Summary**
- Total videos processed
- Successfully matched songs
- Failed matches with reasons
- Overall success rate percentage

---

## 📊 Usage

1. **Run the script**:
```
python youtube_to_spotify.py
```


3. **Follow the authentication prompts**:
- Browser windows will open for YouTube and Spotify login
- Grant the requested permissions

3. **Wait for processing**:
- The script will fetch and analyze your liked videos
- Progress updates will be displayed in real-time

4. **Make your choice**:
- Choose option 1 to add songs to your liked songs
- Choose option 2 to create a new playlist and enter a name

5. **Review the summary**:
- Check the final report for successful transfers and any issues

---

## ⚠️ Important Notes

- **API Quotas**: YouTube Data API has daily quotas; the script handles rate limiting automatically
- **Playlist Privacy**: Created playlists are set to private by default
- **Test User Requirement**: You must add your email as a test user in Google Cloud Console if the app is in testing mode
- **Redirect URI**: The redirect URI must exactly match between your script and Spotify app settings
- **Song Matching**: Not all YouTube videos can be matched to Spotify tracks due to:
- Different song titles or artist names
- Songs not available on Spotify
- Videos that aren't actually music

---

## 🔍 Troubleshooting

### **Common Issues and Solutions**

#### **"Access blocked: testinglist has not completed the Google verification process"**
- **Solution**: Add your email address as a test user in Google Cloud Console OAuth consent screen

#### **"INVALID_CLIENT: Insecure redirect URI"**
- **Solution**: Ensure the redirect URI in Spotify Developer Dashboard is exactly `http://127.0.0.1:8080`

#### **"YouTube client secrets file not found"**
- **Solution**: Make sure the `youtube_client_secrets.json` file is in the same directory as your script

#### **"Please update the Spotify credentials in the script"**
- **Solution**: Replace the placeholder values with your actual Spotify Client ID and Client Secret

#### **Low success rate for song matching**
- **Possible causes**: 
- Many non-music videos in your liked videos
- Songs with unusual titles or formatting
- Regional availability differences between YouTube and Spotify

### **Debug Mode**
To see more detailed error messages, you can modify the script to include more verbose logging.

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📞 Support

For issues, questions, or feature requests:
- Create an issue on the GitHub repository
- Check the troubleshooting section above
- Ensure all setup steps have been completed correctly

---

## 🔒 Privacy & Security

- **Data Handling**: The script only accesses your liked videos list and does not store any personal data
- **Credentials**: Your API credentials are used only for authentication and are not transmitted anywhere except to Google and Spotify
- **Permissions**: The script requests minimal necessary permissions for YouTube (read-only) and Spotify (playlist modification)

