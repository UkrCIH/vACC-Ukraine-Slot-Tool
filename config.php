<?php
// config.php
$sso_config = [
    'client_id'     => 'YOUR_CLIENT_ID_HERE',
    'client_secret' => 'YOUR_CLIENT_SECRET_HERE',
    'redirect_uri'  => 'http://your-website.com/login.php', // Must match VATSIM setting exactly
    'base_url'      => 'https://auth.vatsim.net' // Use https://auth-dev.vatsim.net for testing if needed
];
?>