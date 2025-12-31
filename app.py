from flask import Flask, request, jsonify, render_template
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import re
import os
from urllib.parse import quote

app = Flask(__name__)

# JSON pretty print configuration
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Spotify credentials (environment variables recommended for security)
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '06244788759943e8a2f577d43c6fede1')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '9e5b154bb43945b0880c36594bea4ad3')

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

def is_spotify_url(url):
    """Validate if the input is a proper Spotify track URL."""
    pattern = r'^https://open\.spotify\.com/track/[a-zA-Z0-9]+'
    return bool(re.match(pattern, url))

def generate_direct_link(spotify_url):
    """Generate the direct MP3 download link using the provided API."""
    try:
        encoded_url = quote(spotify_url)
        return f"https://spotmp3.app/api/direct-download?url={encoded_url}"
    except:
        return None

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

@app.route('/')
def index():
    """Status page."""
    return jsonify({
        'api_status': 'Online',
        'endpoints': ['/sp/dl?url={spotify_url}', '/sp/search?q={query}']
    })

@app.route('/sp/dl', methods=['GET'])
def download():
    """Main download endpoint with structured JSON output."""
    url = request.args.get('url')
    
    if not url or not is_spotify_url(url):
        return jsonify({
            'success': False,
            'error': 'Invalid or missing Spotify URL'
        }), 400

    try:
        # Extract ID and fetch data
        track_id = url.split('/track/')[1].split('?')[0]
        metadata = get_track_info(track_id)
        
        if not metadata:
            return jsonify({'success': False, 'error': 'Could not retrieve metadata'}), 404

        # Final structured response
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
                'download_link': generate_direct_link(url)
            },
            'source': {
                'platform': 'Spotify',
                'original_url': metadata['spotify_link']
            },
            'developer_notice': 'Direct download link provided by SpotMP3 API'
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/sp/search', methods=['GET'])
def search():
    """Search endpoint returning multiple results with download links."""
    query = request.args.get('q')
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter "q" is required'}), 400

    try:
        results = sp.search(q=query, type='track', limit=5)
        formatted_results = []

        for item in results['tracks']['items']:
            track_id = item['id']
            s_url = item['external_urls']['spotify']
            
            # Use existing get_track_info function
            metadata = get_track_info(track_id)
            
            if metadata:
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
                        'download_link': generate_direct_link(s_url)
                    },
                    'source': {
                        'platform': 'Spotify',
                        'original_url': s_url
                    },
                    'developer_notice': 'Direct download link provided by SpotMP3 API'
                })

        return jsonify({
            'success': True,
            'total_found': len(formatted_results),
            'results': formatted_results
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Running on port 5000 with debug mode enabled
    app.run(host='0.0.0.0', port=5000, debug=True)
