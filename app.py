from flask import Flask, request, jsonify, render_template
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
from bs4 import BeautifulSoup
import re
import os

app = Flask(__name__)

# Spotify credentials (use environment variables in production)
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '06244788759943e8a2f577d43c6fede1')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '9e5b154bb43945b0880c36594bea4ad3')

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

def is_spotify_url(input_string):
    """Check if input is a valid Spotify track URL."""
    return bool(re.match(r'^https://open\.spotify\.com/track/[a-zA-Z0-9]+', input_string))

def get_spotmate_download(spotify_url):
    """Fetch download link from spotmate.online with error handling."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Get session and CSRF token
        session = requests.Session()
        home_response = session.get('https://spotidown.app', headers=headers, timeout=10)
        home_response.raise_for_status()
        
        soup = BeautifulSoup(home_response.text, 'html.parser')
        csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']
        
        # Prepare conversion request
        headers.update({
            'X-CSRF-TOKEN': csrf_token,
            'Referer': 'https://spotidown.app',
            'Content-Type': 'application/json'
        })
        
        convert_response = session.post(
            'https://spotidown.app/convert',
            json={'urls': spotify_url},
            headers=headers,
            timeout=15
        )
        convert_response.raise_for_status()
        
        data = convert_response.json()
        return data.get('url')
        
    except Exception as e:
        print(f"[Spotmate Error] {str(e)}")
        return None

def get_track_metadata(track_id):
    """Fetch comprehensive track metadata from Spotify."""
    try:
        track = sp.track(track_id)
        album = track['album']
        
        # Get best quality cover art (last image is usually highest resolution)
        cover_url = album['images'][0]['url'] if album.get('images') else None
        
        return {
            'id': track['id'],
            'title': track['name'],
            'artists': ", ".join(artist['name'] for artist in track['artists']),
            'album': album['name'],
            'release_date': album['release_date'],
            'duration_ms': track['duration_ms'],
            'duration_formatted': f"{track['duration_ms'] // 60000}:{(track['duration_ms'] % 60000) // 1000:02d}",
            'isrc': track['external_ids'].get('isrc', 'N/A'),
            'cover_url': cover_url,
            'popularity': track['popularity'],
            'preview_url': track.get('preview_url')
        }
    except Exception as e:
        print(f"[Metadata Error] {str(e)}")
        return None

def search_spotify(query, limit=5):
    """Search Spotify with enhanced results."""
    try:
        results = sp.search(q=query, type='track', limit=limit)
        return [
            {
                'name': track['name'],
                'artists': ", ".join(artist['name'] for artist in track['artists']),
                'id': track['id'],
                'url': track['external_urls']['spotify'],
                'cover_url': track['album']['images'][0]['url'] if track['album']['images'] else None
            }
            for track in results['tracks']['items']
        ]
    except Exception as e:
        print(f"[Search Error] {str(e)}")
        return []

@app.route('/')
def home():
    """Render homepage."""
    return render_template('status.html')

@app.route('/sp/dl', methods=['GET'])
def download_track():
    """Download endpoint with full metadata."""
    spotify_url = request.args.get('url')
    
    if not spotify_url or not is_spotify_url(spotify_url):
        return jsonify({
            'status': False,
            'message': 'Valid Spotify URL required (e.g. /sp/dl?url=https://open.spotify.com/track/11dFgh...)',
            'example_track': 'https://open.spotify.com/track/11dFghVXANMlKmJXsNCbNl'
        }), 400

    try:
        track_id = spotify_url.split('/track/')[1].split('?')[0]
        metadata = get_track_metadata(track_id)
        
        if not metadata:
            return jsonify({
                'status': False,
                'message': 'Failed to fetch track metadata'
            }), 500

        download_url = get_spotmate_download(spotify_url)
        
        return jsonify({
            'status': True,
            'metadata': {
                'title': metadata['title'],
                'artists': metadata['artists'],
                'album': metadata['album'],
                'release_date': metadata['release_date'],
                'duration': metadata['duration_formatted'],
                'isrc': metadata['isrc'],
                'cover_url': metadata['cover_url'],
                'spotify_url': f"https://open.spotify.com/track/{track_id}",
                'preview_url': metadata['preview_url']
            },
            'download': {
                'url': download_url,
                'available': bool(download_url)
            },
            'credit': 'API by @TheSmartDev | github.com/TheSmartDevs'
        })

    except Exception as e:
        return jsonify({
            'status': False,
            'message': f'Processing error: {str(e)}'
        }), 500

@app.route('/sp/search', methods=['GET'])
def search_tracks():
    """Enhanced search endpoint."""
    query = request.args.get('q')
    limit = min(int(request.args.get('limit', 5)), 10)  # Max 10 results
    
    if not query:
        return jsonify({
            'status': False,
            'message': 'Search query required (e.g. /sp/search?q=radwimps)',
            'example': '/sp/search?q=Radwimps+Nandemonaiya&limit=3'
        }), 400

    try:
        results = search_spotify(query, limit)
        
        if not results:
            return jsonify({
                'status': False,
                'message': 'No tracks found'
            }), 404

        # Add download links
        for item in results:
            item['download_url'] = get_spotmate_download(item['url'])
        
        return jsonify({
            'status': True,
            'count': len(results),
            'results': results,
            'credit': 'API by @TheSmartDev | github.com/TheSmartDevs'
        })

    except Exception as e:
        return jsonify({
            'status': False,
            'message': f'Search error: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
