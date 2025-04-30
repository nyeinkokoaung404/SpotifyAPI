<?php
header('Content-Type: application/json');

$client_id = '5941bb8af55d4a52a91c5297f616e325';
$client_secret = '408f04b237aa4dd2ba1b8bfc5da9eff8';

function getSpotifyAccessToken() {
    global $client_id, $client_secret;
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, 'https://accounts.spotify.com/api/token');
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, 'grant_type=client_credentials');
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/x-www-form-urlencoded',
        'Authorization: Basic ' . base64_encode($client_id . ':' . $client_secret)
    ]);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    
    $response = curl_exec($ch);
    curl_close($ch);
    
    $data = json_decode($response, true);
    return $data['access_token'] ?? null;
}

function getSpotifyTrackDetails($url) {
    $apiUrl = 'https://api.fabdl.com/spotify/get?url=' . urlencode($url);
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $apiUrl);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    
    $response = curl_exec($ch);
    curl_close($ch);
    
    return json_decode($response, true);
}

function getDownloadLink($gid, $track_id) {
    $apiUrl = 'https://api.fabdl.com/spotify/mp3-convert-task/' . urlencode($gid) . '/' . urlencode($track_id);
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $apiUrl);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    
    $response = curl_exec($ch);
    curl_close($ch);
    
    return json_decode($response, true);
}

function getTrackMetadata($trackId, $accessToken) {
    $apiUrl = 'https://api.spotify.com/v1/tracks/' . urlencode($trackId);
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $apiUrl);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Authorization: Bearer ' . $accessToken
    ]);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    
    $response = curl_exec($ch);
    curl_close($ch);
    
    $track = json_decode($response, true);
    
    // ISRC ကိုရယူခြင်း
    $isrc = 'N/A';
    if (isset($track['external_ids']['isrc'])) {
        $isrc = $track['external_ids']['isrc'];
    }
    
    return [
        'id' => $track['id'] ?? '',
        'title' => $track['name'] ?? '',
        'artists' => implode(", ", array_map(function($artist) { return $artist['name']; }, $track['artists'] ?? [])),
        'album' => $track['album']['name'] ?? '',
        'releaseDate' => $track['album']['release_date'] ?? '',
        'duration' => isset($track['duration_ms']) ? gmdate("i:s", $track['duration_ms'] / 1000) : '',
        'duration_ms' => $track['duration_ms'] ?? 0,
        'image' => $track['album']['images'][0]['url'] ?? '',
        'spotify_url' => $track['external_urls']['spotify'] ?? '',
        'popularity' => $track['popularity'] ?? 0,
        'isrc' => $isrc,
        'preview_url' => $track['preview_url'] ?? '', // သီချင်းအစမ်းနားထောင်ရန် link
        'external_ids' => $track['external_ids'] ?? [] // အခြားသော external IDs များ
    ];
}

// Main endpoint
if (isset($_GET['url'])) {
    $spotifyUrl = $_GET['url'];
    
    try {
        $trackDetails = getSpotifyTrackDetails($spotifyUrl);
        
        if (!isset($trackDetails['result'])) {
            throw new Exception('Invalid track details response');
        }
        
        $result = $trackDetails['result'];
        $gid = $result['gid'] ?? '';
        $id = $result['id'] ?? '';
        $name = $result['name'] ?? '';
        $image = $result['image'] ?? '';
        $artists = $result['artists'] ?? '';
        $duration_ms = $result['duration_ms'] ?? 0;
        
        $downloadTask = getDownloadLink($gid, $id);
        
        if (!isset($downloadTask['result']['download_url'])) {
            throw new Exception('Failed to retrieve download link');
        }
        
        $accessToken = getSpotifyAccessToken();
        $trackMetadata = getTrackMetadata($id, $accessToken);
        
        $finalResult = [
            'status' => true,
            'id' => $id,
            'title' => $name,
            'image' => $image,
            'artist' => $artists,
            'duration' => gmdate("i:s", $duration_ms / 1000),
            'duration_ms' => $duration_ms,
            'download_link' => 'https://api.fabdl.com' . $downloadTask['result']['download_url'],
            'album' => $trackMetadata['album'],
            'cover' => $trackMetadata['image'],
            'isrc' => $trackMetadata['isrc'], // ISRC ကိုထည့်သွင်း
            'releaseDate' => $trackMetadata['releaseDate'],
            'spotify_url' => 'https://open.spotify.com/track/' . $id,
            'preview_url' => $trackMetadata['preview_url'], // အသံဖိုင်အစမ်း
            'external_ids' => $trackMetadata['external_ids'] // အခြားသော ID များ
        ];
        
        echo json_encode($finalResult);
        
    } catch (Exception $e) {
        http_response_code(500);
        echo json_encode([
            'status' => false,
            'message' => $e->getMessage()
        ]);
    }
} else {
    http_response_code(400);
    echo json_encode([
        'status' => false,
        'message' => 'Spotify URL is required',
        'example' => '/spotify.php?url=https://open.spotify.com/track/TRACK_ID',
        'new_features' => [
            'isrc_support' => true,
            'preview_audio' => true,
            'extended_metadata' => true
        ]
    ]);
}
?>