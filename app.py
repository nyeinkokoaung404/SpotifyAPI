from flask import Flask, request, jsonify, render_template
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Spotify credentials
CLIENT_ID = '5941bb8af55d4a52a91c5297f616e325'
CLIENT_SECRET = '408f04b237aa4dd2ba1b8bfc5da9eff8'

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

def is_spotify_url(input_string):
    """Check if input is a Spotify track URL."""
    return bool(re.match(r'^https://open\.spotify\.com/track/[a-zA-Z0-9]+', input_string))

def get_spotmate_download(spotify_url):
    """Get download link from spotmate.online."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html',
        }
        response = requests.get('https://spotmate.online', headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('meta', {'name': 'csrf-token'})
        if not csrf_token:
            raise ValueError("CSRF token not found")
        csrf_token = csrf_token['content']
        
        session_cookie = response.cookies.get('spotmateonline_session')
        if not session_cookie:
            raise ValueError("Session cookie not found")
        
        headers.update({
            'Content-Type': 'application/json',
            'x-csrf-token': csrf_token,
            'cookie': f'spotmateonline_session={session_cookie}',
            'referer': 'https://spotmate.online/en',
            'origin': 'https://spotmate.online',
        })
        convert_response = requests.post(
            'https://spotmate.online/convert',
            json={'urls': str(spotify_url)},
            headers=headers,
            timeout=10
        )
        convert_response.raise_for_status()
        data = convert_response.json()
        
        if data.get('error') or not data.get('url'):
            raise ValueError("Failed to get download link")
        
        return data['url']
    except Exception:
        return None

def get_track_metadata(track_id):
    """Get track metadata from Spotify, including cover art."""
    try:
        track = sp.track(track_id)
        # Get the largest available cover art (usually at index 0)
        cover_art = track['album']['images'][0]['url'] if track['album']['images'] else None
        return {
            'id': track['id'],
            'title': track['name'],
            'artists': ", ".join(artist['name'] for artist in track['artists']),
            'album': track['album']['name'],
            'release_date': track['album']['release_date'],
            'duration': f"{track['duration_ms'] // 60000}:{(track['duration_ms'] % 60000) // 1000:02d}",
            'isrc': track['external_ids'].get('isrc', 'N/A'),
            'cover_art': cover_art
        }
    except Exception:
        return None

def search_spotify(query, limit=5):
    """Search Spotify for tracks."""
    try:
        results = sp.search(q=query, type='track', limit=limit)
        return [(track['name'], ", ".join(artist['name'] for artist in track['artists']), track['id']) for track in results['tracks']['items']]
    except Exception:
        return []

@app.route('/')
def home():
    """Render the status.html template."""
    return render_template('status.html')

@app.route('/sp/dl', methods=['GET'])
def download_track():
    """Download track by Spotify URL."""
    spotify_url = request.args.get('url')
    if not spotify_url or not is_spotify_url(spotify_url):
        return jsonify({
            'status': False,
            'message': 'Valid Spotify track URL required ❌',
            'example': '/sp/dl?url=https://open.spotify.com/track/TRACK_ID'
        }), 400

    try:
        track_id = spotify_url.split('/track/')[1].split('?')[0]
        metadata = get_track_metadata(track_id)
        if not metadata:
            return jsonify({
                'status': False,
                'message': 'Failed to fetch metadata ❌'
            }), 500

        download_url = get_spotmate_download(spotify_url)
        if not download_url:
            return jsonify({
                'status': False,
                'message': 'Sorry Song Not Available ❌'
            }), 500

        return jsonify({
            'status': True,
            'title': metadata['title'],
            'artist': metadata['artists'],
            'track_id': track_id,
            'track_url': f"https://open.spotify.com/track/{track_id}",
            'download_url': download_url,
            'album': metadata['album'],
            'release_date': metadata['release_date'],
            'duration': metadata['duration'],
            'isrc': metadata['isrc'],
            'cover_art': metadata['cover_art'],
            'credit': 'Downloaded By @TheSmartDev And API Developer @TheSmartDev Organization github.com/TheSmartDevs'
        })

    except Exception as e:
        return jsonify({
            'status': False,
            'message': f'Error: {str(e)} ❌'
        }), 500

@app.route('/sp/search', methods=['GET'])
def search_tracks():
    """Search tracks by query."""
    query = request.args.get('q')
    if not query:
        return jsonify({
            'status': False,
            'message': 'Search query required ❌',
            'example': '/sp/search?q=Tomake+Chai'
        }), 400

    try:
        tracks = search_spotify(query)
        if not tracks:
            return jsonify({
                'status': False,
                'message': 'No tracks found ❌'
            }), 404

        results = []
        for name, artist, track_id in tracks:
            track_url = f"https://open.spotify.com/track/{track_id}"
            metadata = get_track_metadata(track_id)
            if not metadata:
                continue

            download_url = get_spotmate_download(track_url)
            results.append({
                'title': name,
                'artist': artist,
                'track_id': track_id,
                'track_url': track_url,
                'download_url': download_url if download_url else None,
                'album': metadata['album'],
                'release_date': metadata['release_date'],
                'duration': metadata['duration'],
                'isrc': metadata['isrc'],
                'cover_art': metadata['cover_art'],
                'credit': 'Downloaded By @TheSmartDev And API Developer @TheSmartDev Organization github.com/TheSmartDevs' if download_url else ''
            })

        return jsonify({
            'status': True,
            'results': results
        })

    except Exception as e:
        return jsonify({
            'status': False,
            'message': f'Error: {str(e)} ❌'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
