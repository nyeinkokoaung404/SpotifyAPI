
# SpotifyAPI - Your Gateway to Spotify's Music World 🎶

![GitHub repo size](https://img.shields.io/github/repo-size/TheSmartDevs/SpotifyAPI) 
![GitHub last commit](https://img.shields.io/github/last-commit/TheSmartDevs/SpotifyAPI) 
![GitHub issues](https://img.shields.io/github/issues/TheSmartDevs/SpotifyAPI) 
![GitHub stars](https://img.shields.io/github/stars/TheSmartDevs/SpotifyAPI?style=social)

SpotifyAPI is a robust PHP-based API designed to interact with Spotify's vast music library. With this API, you can search for songs, retrieve detailed track, album, and playlist information, and even download tracks. Host it on your own server, such as via Cpanel, and unlock a world of music possibilities! 💥

## Features 🌟

- 🔍 Search for songs with custom queries
- 🎵 Retrieve detailed track information
- 💿 Fetch comprehensive album details
- 📋 Access playlist data with track listings
- ⬇️ Download tracks directly from Spotify URLs

## Setup Instructions ⚙️

Follow these steps to host SpotifyAPI on your own server using Cpanel:

1. **Clone the Repository:**
   - Clone the project from GitHub: `git clone https://github.com/TheSmartDevs/SpotifyAPI.git`

2. **Upload Files to Server:**
   - Use Cpanel's File Manager or an FTP client to upload `spotify.php` and `spotipy.php` to your server's public directory (e.g., `public_html`).

3. **Configure Spotify API Credentials:**
   - Open both `spotify.php` and `spotipy.php` in a text editor.
   - Replace `$client_id` and `$client_secret` with your own Spotify API credentials. Get these by creating an app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).

4. **Set File Permissions:**
   - Ensure the PHP files have executable permissions (typically 755). In Cpanel, right-click the files, select "Change Permissions," and set accordingly.

5. **Test Your Deployment:**
   - Access the API via your domain, e.g.:
     - Search: `https://yourdomain.com/spotify.php?q=SEARCH_QUERY`
     - Track Download: `https://yourdomain.com/spotipy.php?url=SPOTIFY_TRACK_URL`

## Usage Examples ✅

Here’s how to use the API endpoints with real examples:

- **Search Songs:**
  - **Endpoint:** `/spotify.php?q={SearchQuery}&limit=30&offset=0`
  - **Example:** `https://abirthetech.serv00.net/spotify.php?q=despacito&limit=30&offset=0`
  - **Result:** Returns a JSON array of songs matching "despacito".

- **Track Details & Download:**
  - **Endpoint:** `/spotipy.php?url={SpotifyTrackURL}`
  - **Example:** `https://abirthetech.serv00.net/spotipy.php?url=https://open.spotify.com/track/56zZ48jdyY2oDXHVnwg5Di`
  - **Result:** Returns track metadata and a download link in JSON format.

## API Endpoints 🌐

### 1. Search Songs
- **URL:** `/spotify.php`
- **Method:** GET
- **Parameters:**
  - `q`: Search query (required)
  - `limit`: Results limit (optional, default: 30, max: 50)
  - `offset`: Pagination offset (optional, default: 0)
- **Response:** JSON array of song objects

### 2. Get Track Details
- **URL:** `/spotify.php?url={SpotifyTrackURL}`
- **Method:** GET
- **Parameters:**
  - `url`: Spotify track URL (required)
- **Response:** JSON object with track details

### 3. Get Album Details
- **URL:** `/spotify.php?url={SpotifyAlbumURL}`
- **Method:** GET
- **Parameters:**
  - `url`: Spotify album URL (required)
- **Response:** JSON object with album details

### 4. Get Playlist Details
- **URL:** `/spotify.php?url={SpotifyPlaylistURL}`
- **Method:** GET
- **Parameters:**
  - `url`: Spotify playlist URL (required)
- **Response:** JSON object with playlist details

### 5. Download Track
- **URL:** `/spotipy.php?url={SpotifyTrackURL}`
- **Method:** GET
- **Parameters:**
  - `url`: Spotify track URL (required)
- **Response:** JSON object with track metadata and download link

## Repository 💀

- **GitHub:** [https://github.com/TheSmartDevs/SpotifyAPI](https://github.com/TheSmartDevs/SpotifyAPI)

## Contributing ✨

Feel free to fork the repo, submit pull requests, or report issues. Let’s make this API even better together! ⭐️

## License ❄️

This project is open-source under the MIT License. Check the repo for details.

---

Built with 💫 by TheSmartDevs | 🇧🇩 Proudly hosted and tested on Cpanel servers like abirthetech.serv00.net! 👀
