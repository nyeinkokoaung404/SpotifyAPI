from flask import Flask, request, jsonify
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import re
from urllib.parse import quote
from bs4 import BeautifulSoup

app = Flask(__name__)

# JSON pretty print configuration
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Spotify credentials
CLIENT_ID = '06244788759943e8a2f577d43c6fede1'
CLIENT_SECRET = '9e5b154bb43945b0880c36594bea4ad3'

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

def is_spotify_url(url):
    """Validate if the input is a proper Spotify track URL."""
    pattern = r'^https://open\.spotify\.com/track/[a-zA-Z0-9]+'
    return bool(re.match(pattern, url))

def get_track_info(track_id):
    """Fetch track metadata from Spotify official API."""
    try:
        track = sp.track(track_id)
        return {
            'title': track['name'],
            'artist': ", ".join(artist['name'] for artist in track['artists']),
            'album': track['album']['name'],
            'release_date': track['album']['release_date'],
            'duration': f"{track['duration_ms'] // 60000}:{(track['duration_ms'] % 60000) // 1000:02d}",
            'cover_art': track['album']['images'][0]['url'] if track['album']['images'] else None,
            'spotify_link': f"https://open.spotify.com/track/{track_id}"
        }
    except Exception as e:
        print(f"Metadata Error: {e}")
        return None

def get_spotmate_download(spotify_url):
    """Get download link from spotmate.online."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html',
        }
        # Step 1: Get CSRF and Session
        response = requests.get('https://spotmate.online', headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('meta', {'name': 'csrf-token'})
        if not csrf_token:
            return None
        csrf_token = csrf_token['content']
        
        session_cookie = response.cookies.get('spotmateonline_session')
        if not session_cookie:
            return None
        
        # Step 2: Post to Convert
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
            return None
        
        return data['url']
    except Exception:
        return None

@app.route('/')
def index():
    return jsonify({
        'api_status': 'Online',
        'endpoints': ['/sp/dl?url={spotify_url}', '/sp/search?q={query}']
    })

@app.route('/sp/dl', methods=['GET'])
def download():
    url = request.args.get('url')
    
    if not url or not is_spotify_url(url):
        return jsonify({'success': False, 'error': 'Invalid or missing Spotify URL'}), 400

    try:
        track_id = url.split('/track/')[1].split('?')[0]
        metadata = get_track_info(track_id)
        
        if not metadata:
            return jsonify({'success': False, 'error': 'Could not retrieve metadata'}), 404

        # Using Spotmate script for download link
        dl_link = get_spotmate_download(url)

        return jsonify({
            'success': True,
            'track_details': {
                'title': metadata['title'],
                'artist': metadata['artist'],
                'album': metadata['album'],
                'release_year': metadata['release_date'],
                'duration': metadata['duration']
            },
            'assets': {
                'cover_image': metadata['cover_art'],
                'download_link': dl_link
            },
            'source': {
                'platform': 'Spotify',
                'original_url': metadata['spotify_link']
            },
            'developer_notice': 'Direct download link provided by Spotmate Engine'
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/sp/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter "q" is required'}), 400

    try:
        results = sp.search(q=query, type='track', limit=5)
        formatted_results = []

        for item in results['tracks']['items']:
            s_url = item['external_urls']['spotify']
            track_id = item['id']
            
            # Using basic metadata from search result for speed
            metadata = {
                'title': item['name'],
                'artist': ", ".join(a['name'] for a in item['artists']),
                'album': item['album']['name'],
                'release_date': item['album']['release_date'],
                'duration': f"{item['duration_ms'] // 60000}:{(item['duration_ms'] % 60000) // 1000:02d}",
                'cover_art': item['album']['images'][0]['url'] if item['album']['images'] else None
            }

            formatted_results.append({
                'success': True,
                'track_details': {
                    'title': metadata['title'],
                    'artist': metadata['artist'],
                    'album': metadata['album'],
                    'release_year': metadata['release_date'].split('-')[0],
                    'duration': metadata['duration']
                },
                'assets': {
                    'cover_image': metadata['cover_art'],
                    'download_link': get_spotmate_download(s_url)
                },
                'source': {
                    'platform': 'Spotify',
                    'original_url': s_url
                },
                'developer_notice': 'Direct download link provided by Spotmate Engine'
            })

        return jsonify({
            'success': True,
            'total_found': len(formatted_results),
            'results': formatted_results
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
