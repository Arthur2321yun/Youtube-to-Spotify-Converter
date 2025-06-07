import os
import json
import re
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from typing import List, Tuple, Optional

# YouTube API setup
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

# Spotify API setup
SPOTIFY_SCOPE = 'user-library-modify user-library-read playlist-modify-private playlist-modify-public'

class YouTubeToSpotifyTransfer:
    def __init__(self, youtube_client_secrets_path: str, spotify_client_id: str, 
                 spotify_client_secret: str, spotify_redirect_uri: str = 'http://127.0.0.1:8080'):
        self.youtube_client_secrets_path = youtube_client_secrets_path
        self.spotify_client_id = spotify_client_id
        self.spotify_client_secret = spotify_client_secret
        self.spotify_redirect_uri = spotify_redirect_uri
        
        self.youtube_client = None
        self.spotify_client = None
    
    def authenticate_youtube(self):
        """Authenticate with YouTube Data API"""
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # For local testing only
        
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            self.youtube_client_secrets_path, YOUTUBE_SCOPES)
        credentials = flow.run_local_server(port=8080)
        
        self.youtube_client = googleapiclient.discovery.build(
            "youtube", "v3", credentials=credentials)
        print("✅ YouTube authentication successful!")
    
    def authenticate_spotify(self):
        """Authenticate with Spotify Web API"""
        auth_manager = SpotifyOAuth(
            client_id=self.spotify_client_id,
            client_secret=self.spotify_client_secret,
            redirect_uri=self.spotify_redirect_uri,
            scope=SPOTIFY_SCOPE,
            open_browser=True
        )
        
        self.spotify_client = spotipy.Spotify(auth_manager=auth_manager)
        print("✅ Spotify authentication successful!")
    
    def get_liked_videos(self) -> List[dict]:
        """Fetch all liked videos from YouTube"""
        if not self.youtube_client:
            raise Exception("YouTube client not authenticated")
        
        # Get the liked videos playlist ID
        channels_response = self.youtube_client.channels().list(
            part="contentDetails", mine=True).execute()
        
        liked_playlist_id = channels_response["items"][0]["contentDetails"]["relatedPlaylists"]["likes"]
        
        videos = []
        next_page_token = None
        
        print("🔍 Fetching liked videos from YouTube...")
        
        while True:
            request = self.youtube_client.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=liked_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            videos.extend(response["items"])
            next_page_token = response.get("nextPageToken")
            
            if not next_page_token:
                break
        
        print(f"📹 Found {len(videos)} liked videos")
        return videos
    
    def extract_song_info(self, video: dict) -> Tuple[Optional[str], Optional[str]]:
        """Extract song and artist information from video title and description"""
        title = video["snippet"]["title"]
        description = video["snippet"].get("description", "")
        
        # Common patterns for music videos - Fixed regex patterns
        patterns = [
            r"(.+?)\s*[-–—]\s*(.+?)(?:\s*\(.*\))?(?:\s*\[.*\])?$",  # Artist - Song
            r"(.+?)\s*[:|]\s*(.+?)(?:\s*\(.*\))?(?:\s*\[.*\])?$",   # Artist : Song
            r'(.+?)\s*[""]\s*(.+?)\s*["""]',                        # Artist "Song"
            r"(.+?)\s*by\s*(.+?)(?:\s*\(.*\))?(?:\s*\[.*\])?$",     # Song by Artist
        ]
        
        # Try to extract from title
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                if "by" in pattern:
                    return match.group(1).strip(), match.group(2).strip()  # Song, Artist
                else:
                    return match.group(2).strip(), match.group(1).strip()  # Song, Artist
        
        # If no pattern matches, try to identify if it's likely a music video
        music_keywords = ["official", "music", "video", "audio", "lyric", "ft.", "feat.", "remix"]
        if any(keyword in title.lower() for keyword in music_keywords):
            # Split by common separators and take first two parts
            separators = [" - ", " – ", " — ", " | ", ": "]
            for sep in separators:
                if sep in title:
                    parts = title.split(sep, 1)
                    if len(parts) == 2:
                        return parts[1].strip(), parts[0].strip()  # Song, Artist
        
        return None, None
    
    def search_spotify_track(self, song: str, artist: str) -> Optional[str]:
        """Search for a track on Spotify and return its ID"""
        if not self.spotify_client:
            raise Exception("Spotify client not authenticated")
        
        # Try different search queries for better matching
        search_queries = [
            f'track:"{song}" artist:"{artist}"',
            f'"{song}" "{artist}"',
            f'{song} {artist}',
            f'"{song}" artist:{artist}',
            f'track:{song} artist:{artist}'
        ]
        
        for query in search_queries:
            try:
                results = self.spotify_client.search(q=query, type='track', limit=5)
                tracks = results.get('tracks', {}).get('items', [])
                
                if tracks:
                    # Return the first result (usually most relevant)
                    return tracks[0]['id']
            except Exception as e:
                print(f"⚠️ Search error for '{query}': {e}")
                continue
        
        return None
    
    def create_spotify_playlist(self, playlist_name: str) -> Optional[str]:
        """Create a new Spotify playlist and return its ID"""
        if not self.spotify_client:
            raise Exception("Spotify client not authenticated")
        
        user_id = self.spotify_client.current_user()['id']
        try:
            playlist = self.spotify_client.user_playlist_create(
                user=user_id, 
                name=playlist_name, 
                public=False,
                description=f"Playlist created from YouTube liked videos - {len(self.spotify_track_ids) if hasattr(self, 'spotify_track_ids') else 0} songs"
            )
            print(f"✅ Created playlist '{playlist_name}'")
            return playlist['id']
        except Exception as e:
            print(f"❌ Error creating playlist: {e}")
            return None
    
    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]):
        """Add tracks to a Spotify playlist in batches"""
        if not self.spotify_client:
            raise Exception("Spotify client not authenticated")
        
        if not track_ids:
            print("❌ No tracks to add")
            return
        
        # Spotify API allows max 100 tracks per request for playlists
        batch_size = 100
        added_count = 0
        
        for i in range(0, len(track_ids), batch_size):
            batch = track_ids[i:i + batch_size]
            try:
                self.spotify_client.playlist_add_items(playlist_id, batch)
                added_count += len(batch)
                print(f"✅ Added batch of {len(batch)} songs to playlist")
            except Exception as e:
                print(f"❌ Error adding batch to playlist: {e}")
        
        print(f"🎵 Successfully added {added_count} songs to the playlist!")
    
    def add_tracks_to_liked_songs(self, track_ids: List[str]):
        """Add tracks to Spotify liked songs in batches"""
        if not self.spotify_client:
            raise Exception("Spotify client not authenticated")
        
        if not track_ids:
            print("❌ No tracks to add")
            return
        
        # Spotify API allows max 50 tracks per request
        batch_size = 50
        added_count = 0
        
        for i in range(0, len(track_ids), batch_size):
            batch = track_ids[i:i + batch_size]
            try:
                self.spotify_client.current_user_saved_tracks_add(tracks=batch)
                added_count += len(batch)
                print(f"✅ Added batch of {len(batch)} songs to liked songs")
            except Exception as e:
                print(f"❌ Error adding batch: {e}")
        
        print(f"🎵 Successfully added {added_count} songs to your Spotify liked songs!")
    
    def transfer_likes(self):
        """Main method to transfer YouTube likes to Spotify with user choice"""
        print("🚀 Starting YouTube to Spotify transfer...")
        
        # Authenticate with both services
        self.authenticate_youtube()
        self.authenticate_spotify()
        
        # Get liked videos from YouTube
        liked_videos = self.get_liked_videos()
        
        # Process videos and find matching Spotify tracks
        spotify_track_ids = []
        successful_matches = []
        failed_matches = []
        
        print("🔍 Searching for songs on Spotify...")
        
        for i, video in enumerate(liked_videos):
            print(f"Processing video {i+1}/{len(liked_videos)}: {video['snippet']['title']}")
            
            song, artist = self.extract_song_info(video)
            
            if song and artist:
                track_id = self.search_spotify_track(song, artist)
                if track_id:
                    spotify_track_ids.append(track_id)
                    successful_matches.append(f"{artist} - {song}")
                    print(f"  ✅ Found: {artist} - {song}")
                else:
                    failed_matches.append(f"{artist} - {song}")
                    print(f"  ❌ Not found: {artist} - {song}")
            else:
                failed_matches.append(video['snippet']['title'])
                print(f"  ⚠️ Could not extract song info from: {video['snippet']['title']}")
        
        if not spotify_track_ids:
            print("❌ No songs found to add.")
            return
        
        # Ask user for choice
        print(f"\n🎵 Found {len(spotify_track_ids)} songs on Spotify!")
        print("\nChoose how to add the songs to Spotify:")
        print("1. Add to Liked Songs")
        print("2. Create a new Playlist")
        
        while True:
            choice = input("Enter 1 or 2: ").strip()
            if choice == '1':
                self.add_tracks_to_liked_songs(spotify_track_ids)
                break
            elif choice == '2':
                while True:
                    playlist_name = input("Enter the name for the new playlist: ").strip()
                    if playlist_name:
                        playlist_id = self.create_spotify_playlist(playlist_name)
                        if playlist_id:
                            self.add_tracks_to_playlist(playlist_id, spotify_track_ids)
                        break
                    else:
                        print("❌ Playlist name cannot be empty. Please try again.")
                break
            else:
                print("❌ Invalid choice. Please enter 1 or 2.")
        
        # Print summary
        print("\n" + "="*60)
        print("📊 TRANSFER SUMMARY")
        print("="*60)
        print(f"Total YouTube liked videos: {len(liked_videos)}")
        print(f"Successfully matched and added: {len(successful_matches)}")
        print(f"Failed to match: {len(failed_matches)}")
        print(f"Success rate: {len(successful_matches)/len(liked_videos)*100:.1f}%")
        
        if successful_matches:
            print(f"\n✅ Successfully added {len(successful_matches)} songs:")
            for match in successful_matches[:10]:  # Show first 10
                print(f"  • {match}")
            if len(successful_matches) > 10:
                print(f"  ... and {len(successful_matches)-10} more")
        
        if failed_matches:
            print(f"\n❌ Could not match {len(failed_matches)} items:")
            for match in failed_matches[:5]:  # Show first 5
                print(f"  • {match}")
            if len(failed_matches) > 5:
                print(f"  ... and {len(failed_matches)-5} more")


def main():
    """Main function to run the transfer"""
    
    # Configuration - Replace with your actual credentials
    YOUTUBE_CLIENT_SECRETS_FILE = "youtube_client_secrets.json"
    SPOTIFY_CLIENT_ID = "your_spotify_client_id"
    SPOTIFY_CLIENT_SECRET = "your_spotify_client_secret"
    SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8080"
    
    # Validate configuration
    if not os.path.exists(YOUTUBE_CLIENT_SECRETS_FILE):
        print(f"❌ YouTube client secrets file not found: {YOUTUBE_CLIENT_SECRETS_FILE}")
        print("Please download your OAuth 2.0 credentials from Google Cloud Console")
        return
    
    if SPOTIFY_CLIENT_ID == "your_spotify_client_id" or SPOTIFY_CLIENT_SECRET == "your_spotify_client_secret":
        print("❌ Please update the Spotify credentials in the script")
        print("Get them from: https://developer.spotify.com/dashboard/applications")
        return
    
    # Create and run the transfer
    transfer = YouTubeToSpotifyTransfer(
        youtube_client_secrets_path=YOUTUBE_CLIENT_SECRETS_FILE,
        spotify_client_id=SPOTIFY_CLIENT_ID,
        spotify_client_secret=SPOTIFY_CLIENT_SECRET,
        spotify_redirect_uri=SPOTIFY_REDIRECT_URI
    )
    
    try:
        transfer.transfer_likes()
    except Exception as e:
        print(f"❌ Error during transfer: {e}")


if __name__ == "__main__":
    main()
