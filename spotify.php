<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

// Configuration - should move to environment variables in production
$client_id = '5941bb8af55d4a52a91c5297f616e325';
$client_secret = '408f04b237aa4dd2ba1b8bfc5da9eff8';

// Rate limiting - simple implementation
$rate_limit = 100; // requests per 15 minutes
$rate_limit_window = 15 * 60; // 15 minutes in seconds
session_start();
if (!isset($_SESSION['api_requests'])) {
    $_SESSION['api_requests'] = [];
}
$current_time = time();
$_SESSION['api_requests'] = array_filter($_SESSION['api_requests'], function($time) use ($current_time, $rate_limit_window) {
    return $time > ($current_time - $rate_limit_window);
});
if (count($_SESSION['api_requests']) >= $rate_limit) {
    http_response_code(429);
    die(json_encode(['error' => 'Rate limit exceeded', 'developerCredit' => 'https://t.me/ISmartDevs']));
}
$_SESSION['api_requests'][] = $current_time;

// Get Spotify Access Token
function getAccessToken() {
    global $client_id, $client_secret;
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, 'https://accounts.spotify.com/api/token');
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, 'grant_type=client_credentials');
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Authorization: Basic ' . base64_encode($client_id . ':' . $client_secret),
        'Content-Type: application/x-www-form-urlencoded'
    ]);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($http_code != 200) {
        throw new Exception('Failed to get access token');
    }
    
    $data = json_decode($response, true);
    return $data['access_token'];
}

// Search Spotify Tracks
function searchSongs($accessToken, $query, $limit = 30, $offset = 0) {
    $query = urlencode($query);
    $url = "https://api.spotify.com/v1/search?q=$query&type=track&limit=$limit&offset=$offset";
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Authorization: Bearer ' . $accessToken
    ]);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($http_code != 200) {
        throw new Exception('Failed to search songs');
    }
    
    $data = json_decode($response, true);
    $tracks = $data['tracks']['items'];
    
    $results = [];
    foreach ($tracks as $track) {
        $results[] = [
            'id' => $track['id'],
            'name' => $track['name'],
            'artists' => array_map(function($artist) {
                return [
                    'name' => $artist['name'],
                    'id' => $artist['id'],
                    'url' => $artist['external_urls']['spotify']
                ];
            }, $track['artists']),
            'album' => [
                'name' => $track['album']['name'],
                'id' => $track['album']['id'],
                'url' => $track['album']['external_urls']['spotify'],
                'image' => $track['album']['images'][0]['url'] ?? null
            ],
            'duration_ms' => $track['duration_ms'],
            'duration' => gmdate("i:s", $track['duration_ms'] / 1000),
            'explicit' => $track['explicit'],
            'popularity' => $track['popularity'],
            'preview_url' => $track['preview_url'],
            'external_urls' => $track['external_urls'],
            'isrc' => $track['external_ids']['isrc'] ?? null,
            'uri' => $track['uri']
        ];
    }
    
    return $results;
}

// Get Track Details with ISRC
function getTrackDetails($accessToken, $trackId) {
    $url = "https://api.spotify.com/v1/tracks/$trackId";
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Authorization: Bearer ' . $accessToken
    ]);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($http_code != 200) {
        throw new Exception('Failed to get track details');
    }
    
    $track = json_decode($response, true);
    
    return [
        'id' => $track['id'],
        'name' => $track['name'],
        'artists' => array_map(function($artist) {
            return [
                'name' => $artist['name'],
                'id' => $artist['id'],
                'url' => $artist['external_urls']['spotify']
            ];
        }, $track['artists']),
        'album' => [
            'name' => $track['album']['name'],
            'id' => $track['album']['id'],
            'url' => $track['album']['external_urls']['spotify'],
            'images' => $track['album']['images'],
            'release_date' => $track['album']['release_date'],
            'total_tracks' => $track['album']['total_tracks']
        ],
        'duration_ms' => $track['duration_ms'],
        'duration' => gmdate("i:s", $track['duration_ms'] / 1000),
        'explicit' => $track['explicit'],
        'popularity' => $track['popularity'],
        'preview_url' => $track['preview_url'],
        'external_urls' => $track['external_urls'],
        'external_ids' => $track['external_ids'] ?? [],
        'isrc' => $track['external_ids']['isrc'] ?? null,
        'uri' => $track['uri']
    ];
}

// Get Album Details with ISRC for each track
function getAlbumDetails($accessToken, $albumId) {
    $url = "https://api.spotify.com/v1/albums/$albumId";
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Authorization: Bearer ' . $accessToken
    ]);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($http_code != 200) {
        throw new Exception('Failed to get album details');
    }
    
    $album = json_decode($response, true);
    
    $tracks = [];
    foreach ($album['tracks']['items'] as $track) {
        $tracks[] = [
            'id' => $track['id'],
            'name' => $track['name'],
            'artists' => array_map(function($artist) {
                return ['name' => $artist['name'], 'id' => $artist['id']];
            }, $track['artists']),
            'duration_ms' => $track['duration_ms'],
            'duration' => gmdate("i:s", $track['duration_ms'] / 1000),
            'track_number' => $track['track_number'],
            'preview_url' => $track['preview_url'],
            'external_urls' => $track['external_urls'],
            'isrc' => $track['external_ids']['isrc'] ?? null,
            'uri' => $track['uri']
        ];
    }
    
    return [
        'id' => $album['id'],
        'name' => $album['name'],
        'artists' => array_map(function($artist) {
            return [
                'name' => $artist['name'],
                'id' => $artist['id'],
                'url' => $artist['external_urls']['spotify']
            ];
        }, $album['artists']),
        'images' => $album['images'],
        'release_date' => $album['release_date'],
        'total_tracks' => $album['total_tracks'],
        'tracks' => $tracks,
        'external_urls' => $album['external_urls']
    ];
}

// Get Playlist Details with ISRC for each track
function getPlaylistDetails($accessToken, $playlistId) {
    $url = "https://api.spotify.com/v1/playlists/$playlistId";
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Authorization: Bearer ' . $accessToken
    ]);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($http_code != 200) {
        throw new Exception('Failed to get playlist details');
    }
    
    $playlist = json_decode($response, true);
    
    $tracks = [];
    foreach ($playlist['tracks']['items'] as $item) {
        $track = $item['track'];
        $tracks[] = [
            'id' => $track['id'],
            'name' => $track['name'],
            'artists' => array_map(function($artist) {
                return ['name' => $artist['name'], 'id' => $artist['id']];
            }, $track['artists']),
            'album' => [
                'name' => $track['album']['name'],
                'id' => $track['album']['id']
            ],
            'duration_ms' => $track['duration_ms'],
            'duration' => gmdate("i:s", $track['duration_ms'] / 1000),
            'preview_url' => $track['preview_url'],
            'external_urls' => $track['external_urls'],
            'isrc' => $track['external_ids']['isrc'] ?? null,
            'uri' => $track['uri']
        ];
    }
    
    return [
        'id' => $playlist['id'],
        'name' => $playlist['name'],
        'description' => $playlist['description'],
        'owner' => [
            'display_name' => $playlist['owner']['display_name'],
            'id' => $playlist['owner']['id']
        ],
        'images' => $playlist['images'],
        'tracks' => [
            'total' => $playlist['tracks']['total'],
            'items' => $tracks
        ],
        'external_urls' => $playlist['external_urls']
    ];
}

// Main API Endpoint
try {
    $query = $_GET['q'] ?? null;
    $url = $_GET['url'] ?? null;
    $limit = min(intval($_GET['limit'] ?? 30), 50); // Max 50 items
    $offset = intval($_GET['offset'] ?? 0);
    
    $accessToken = getAccessToken();
    
    if ($url) {
        // Handle Spotify URLs
        $urlParts = explode('/', parse_url($url, PHP_URL_PATH));
        $contentId = end($urlParts);
        
        if (strpos($url, '/track/') !== false) {
            $trackDetails = getTrackDetails($accessToken, $contentId);
            echo json_encode([
                'type' => 'track',
                'data' => $trackDetails,
                'developer' => 'https://t.me/ISmartDevs'
            ]);
        } elseif (strpos($url, '/album/') !== false) {
            $albumDetails = getAlbumDetails($accessToken, $contentId);
            echo json_encode([
                'type' => 'album',
                'data' => $albumDetails,
                'developerCredit' => 'https://t.me/ISmartDevs'
            ]);
        } elseif (strpos($url, '/playlist/') !== false) {
            $playlistDetails = getPlaylistDetails($accessToken, $contentId);
            echo json_encode([
                'type' => 'playlist',
                'data' => $playlistDetails,
                'developerCredit' => 'https://t.me/ISmartDevs'
            ]);
        } else {
            http_response_code(400);
            echo json_encode([
                'error' => 'Unsupported Spotify URL type',
                'developerCredit' => 'https://t.me/ISmartDevs'
            ]);
        }
    } elseif ($query) {
        // Handle search queries
        $searchResults = searchSongs($accessToken, $query, $limit, $offset);
        echo json_encode([
            'type' => 'search',
            'data' => $searchResults,
            'developer' => 'https://t.me/ISmartDevs'
        ]);
    } else {
        http_response_code(400);
        echo json_encode([
            'error' => 'Missing query parameter (q) or Spotify URL (url)',
            'developerCredit' => 'https://t.me/ISmartDevs',
            'usage' => [
                'Search' => '/spotify.php?q=SEARCH_QUERY&limit=30&offset=0',
                'Track' => '/spotify.php?url=https://open.spotify.com/track/TRACK_ID',
                'Album' => '/spotify.php?url=https://open.spotify.com/album/ALBUM_ID',
                'Playlist' => '/spotify.php?url=https://open.spotify.com/playlist/PLAYLIST_ID'
            ]
        ]);
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'error' => $e->getMessage(),
        'developer' => 'https://t.me/ISmartDevs'
    ]);
}
?>