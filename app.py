from flask import Flask, request, jsonify, render_template
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import re
import os
from urllib.parse import quote

app = Flask(__name__)

# Spotify credentials
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '06244788759943e8a2f577d43c6fede1')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '9e5b154bb43945b0880c36594bea4ad3')

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

def is_spotify_url(input_string):
    """Spotify Track URL ဟုတ်မဟုတ် စစ်ဆေးခြင်း"""
    return bool(re.match(r'^https://open\.spotify\.com/track/[a-zA-Z0-9]+', input_string))

def get_direct_download_link(spotify_url):
    """သင်ပေးထားသော Direct API ကို အသုံးပြု၍ Download Link ထုတ်ပေးခြင်း"""
    try:
        # URL ကို encode လုပ်ပြီး direct link ပြန်ပေးခြင်း
        encoded_url = quote(spotify_url)
        direct_link = f"https://spotmp3.app/api/direct-download?url={encoded_url}"
        return direct_link
    except Exception as e:
        print(f"[Link Generation Error] {str(e)}")
        return None

def get_track_metadata(track_id):
    """Spotify မှ သီချင်းအချက်အလက်များ ရယူခြင်း"""
    try:
        track = sp.track(track_id)
        album = track['album']
        cover_url = album['images'][0]['url'] if album.get('images') else None
        
        return {
            'id': track['id'],
            'title': track['name'],
            'artists': ", ".join(artist['name'] for artist in track['artists']),
            'album': album['name'],
            'release_date': album['release_date'],
            'duration_formatted': f"{track['duration_ms'] // 60000}:{(track['duration_ms'] % 60000) // 1000:02d}",
            'isrc': track['external_ids'].get('isrc', 'N/A'),
            'cover_url': cover_url,
            'preview_url': track.get('preview_url')
        }
    except Exception as e:
        print(f"[Metadata Error] {str(e)}")
        return None

@app.route('/')
def home():
    return render_template('status.html')

@app.route('/sp/dl', methods=['GET'])
def download_track():
    spotify_url = request.args.get('url')
    
    if not spotify_url or not is_spotify_url(spotify_url):
        return jsonify({
            'status': False,
            'message': 'Valid Spotify URL required'
        }), 400

    try:
        track_id = spotify_url.split('/track/')[1].split('?')[0]
        metadata = get_track_metadata(track_id)
        
        if not metadata:
            return jsonify({'status': False, 'message': 'Metadata fetch failed'}), 500

        # Direct Download Link ကို ရယူခြင်း
        download_url = get_direct_download_link(spotify_url)
        
        return jsonify({
            'status': True,
            'metadata': metadata,
            'download': {
                'url': download_url,
                'available': True,
                'note': 'Clicking this link will start the download directly.'
            },
            'credit': 'API by @nkka404'
        })

    except Exception as e:
        return jsonify({'status': False, 'message': str(e)}), 500

@app.route('/sp/search', methods=['GET'])
def search_tracks():
    query = request.args.get('q')
    limit = min(int(request.args.get('limit', 5)), 10)
    
    if not query:
        return jsonify({'status': False, 'message': 'Query required'}), 400

    try:
        results = sp.search(q=query, type='track', limit=limit)
        tracks = []
        for track in results['tracks']['items']:
            s_url = track['external_urls']['spotify']
            tracks.append({
                'name': track['name'],
                'artists': ", ".join(artist['name'] for artist in track['artists']),
                'id': track['id'],
                'url': s_url,
                'cover_url': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'download_url': get_direct_download_link(s_url) # Direct link ထည့်ပေးထားသည်
            })
        
        return jsonify({
            'status': True,
            'count': len(tracks),
            'results': tracks
        })

    except Exception as e:
        return jsonify({'status': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
