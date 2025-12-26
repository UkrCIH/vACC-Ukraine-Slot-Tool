<?php
// login.php - VATSIM OAuth & Flight Lookup
require 'config.php';
session_start();

// 1. START LOGIN: If no code, redirect to VATSIM
if (!isset($_GET['code'])) {
    $authUrl = $sso_config['base_url'] . "/oauth/authorize" .
               "?client_id=" . $sso_config['client_id'] .
               "&redirect_uri=" . urlencode($sso_config['redirect_uri']) .
               "&response_type=code" .
               "&scope=full_name+vatsim_details";
    header("Location: $authUrl");
    exit;
}

// 2. CALLBACK: Exchange Code for Token
$curl = curl_init();
curl_setopt_array($curl, [
    CURLOPT_URL => $sso_config['base_url'] . "/oauth/token",
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => http_build_query([
        'grant_type'    => 'authorization_code',
        'client_id'     => $sso_config['client_id'],
        'client_secret' => $sso_config['client_secret'],
        'redirect_uri'  => $sso_config['redirect_uri'],
        'code'          => $_GET['code']
    ])
]);
$response = curl_exec($curl);
$tokenData = json_decode($response, true);

if (!isset($tokenData['access_token'])) {
    die("Error logging in: " . ($tokenData['message'] ?? 'Unknown error'));
}

// 3. GET USER DETAILS (We need the CID)
curl_setopt_array($curl, [
    CURLOPT_URL => $sso_config['base_url'] . "/api/user",
    CURLOPT_HTTPHEADER => ["Authorization: Bearer " . $tokenData['access_token']],
    CURLOPT_POST => false
]);
$userResponse = curl_exec($curl);
curl_close($curl);

$userData = json_decode($userResponse, true);
$cid = $userData['data']['cid']; // The pilot's VATSIM ID

// 4. FIND PILOT ON NETWORK (Map CID -> Callsign)
// We fetch the live datafeed to see what they are flying right now
$datafeed = json_decode(file_get_contents('https://data.vatsim.net/v3/vatsim-data.json'), true);

$foundCallsign = null;

if (isset($datafeed['pilots'])) {
    foreach ($datafeed['pilots'] as $pilot) {
        if ($pilot['cid'] == $cid) {
            $foundCallsign = $pilot['callsign'];
            break;
        }
    }
}

// 5. REDIRECT USER
if ($foundCallsign) {
    // Found them! Send them to the panel with their callsign
    header("Location: index.html?callsign=" . $foundCallsign);
} else {
    // Login worked, but they aren't online flying right now
    echo "<h1>Login Successful</h1>";
    echo "<p>Welcome, " . $userData['data']['personal']['name_first'] . " ($cid).</p>";
    echo "<p style='color:red'>However, we could not find a live flight for your CID on the network.</p>";
    echo "<p>Please ensure you are connected to VATSIM and try again.</p>";
    echo "<a href='index.html'>Go Back</a>";
}
?>