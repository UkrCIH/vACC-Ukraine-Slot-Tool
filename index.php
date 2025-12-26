<?php
/**
 * SINGLE FILE VATSIM SLOT MANAGER
 * -------------------------------
 * This file handles:
 * 1. Configuration
 * 2. Login/Logout Logic
 * 3. API Logic (Serving/Saving Flight Data)
 * 4. Frontend Interface (HTML/CSS/JS)
 */

session_start();

// ==========================================
// 1. CONFIGURATION
// ==========================================
$sso_config = [
    'client_id'     => 'YOUR_CLIENT_ID_HERE',       // <--- PUT YOUR ID HERE
    'client_secret' => 'YOUR_CLIENT_SECRET_HERE',   // <--- PUT YOUR SECRET HERE
    'redirect_uri'  => 'http://your-website.com/index.php', // Must point to THIS file
    'base_url'      => 'https://auth.vatsim.net'    // Use auth-dev for testing
];

$databaseFile = 'flights.json';

// Ensure database file exists
if (!file_exists($databaseFile)) {
    file_put_contents($databaseFile, json_encode([]));
}

// ==========================================
// 2. ROUTING LOGIC
// ==========================================
$action = $_GET['action'] ?? '';

// --- LOGOUT HANDLER ---
if ($action === 'logout') {
    $_SESSION = array();
    session_destroy();
    header("Location: index.php");
    exit;
}

// --- LOGIN CALLBACK HANDLER ---
if (isset($_GET['code'])) {
    // Exchange Code for Token
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

    if (isset($tokenData['access_token'])) {
        // Get User Details (CID)
        curl_setopt_array($curl, [
            CURLOPT_URL => $sso_config['base_url'] . "/api/user",
            CURLOPT_HTTPHEADER => ["Authorization: Bearer " . $tokenData['access_token']],
            CURLOPT_POST => false
        ]);
        $userResponse = curl_exec($curl);
        $userData = json_decode($userResponse, true);
        $cid = $userData['data']['cid'];

        // Find Pilot in Live Datafeed
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

        curl_close($curl);

        if ($foundCallsign) {
            header("Location: index.php?callsign=" . $foundCallsign);
        } else {
            die("<h1>Login Successful, but flight not found.</h1><p>Welcome, " . $userData['data']['personal']['name_first'] . ". Please ensure you are connected to VATSIM and flying.</p><a href='index.php'>Go Back</a>");
        }
    } else {
        die("Error logging in: " . ($tokenData['message'] ?? 'Unknown error'));
    }
    exit;
}

// --- LOGIN INITIATOR ---
if ($action === 'login') {
    $authUrl = $sso_config['base_url'] . "/oauth/authorize" .
               "?client_id=" . $sso_config['client_id'] .
               "&redirect_uri=" . urlencode($sso_config['redirect_uri']) .
               "&response_type=code" .
               "&scope=full_name+vatsim_details";
    header("Location: $authUrl");
    exit;
}

// --- API: UPDATE TOBT (POST) ---
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);

    // 1. Handle Euroscope Data Push (Array)
    if (isset($input[0])) {
        $currentData = json_decode(file_get_contents($databaseFile), true);
        $mergedData = [];
        foreach ($input as $esFlight) {
            $callsign = strtoupper($esFlight['callsign']);
            $existing = null;
            foreach ($currentData as $row) {
                if ($row['callsign'] === $callsign) {
                    $existing = $row;
                    break;
                }
            }
            if ($existing && isset($existing['manual_tobt'])) {
                $esFlight['manual_tobt'] = $existing['manual_tobt'];
            }
            $mergedData[] = $esFlight;
        }
        file_put_contents($databaseFile, json_encode($mergedData, JSON_PRETTY_PRINT));
        echo json_encode(["status" => "synced"]);
        exit;
    }

    // 2. Handle Pilot TOBT Update
    if (isset($input['action']) && $input['action'] === 'update_tobt') {
        $targetCallsign = strtoupper($input['callsign']);
        $newTobt = $input['tobt'];
        $allFlights = json_decode(file_get_contents($databaseFile), true);
        $found = false;

        foreach ($allFlights as &$flight) {
            if ($flight['callsign'] === $targetCallsign) {
                $flight['manual_tobt'] = $newTobt;
                $found = true;
                break;
            }
        }

        if ($found) {
            file_put_contents($databaseFile, json_encode($allFlights, JSON_PRETTY_PRINT));
            echo json_encode(["status" => "success"]);
        } else {
            echo json_encode(["status" => "error", "message" => "Flight not found"]);
        }
        exit;
    }
}

// --- API: FETCH FLIGHT (GET AJAX) ---
if (isset($_GET['fetch_api']) && isset($_GET['callsign'])) {
    $requestedCallsign = strtoupper($_GET['callsign']);
    $allFlights = json_decode(file_get_contents($databaseFile), true);
    $foundFlight = null;

    foreach ($allFlights as $flight) {
        if ($flight['callsign'] === $requestedCallsign) {
            $foundFlight = $flight;
            break;
        }
    }

    if ($foundFlight) {
        $displayTobt = isset($foundFlight['manual_tobt']) ? $foundFlight['manual_tobt'] : ($foundFlight['eobt'] ?? "----");
        echo json_encode([
            "found" => true,
            "callsign" => $foundFlight['callsign'],
            "tobt" => $displayTobt,
            "tsat" => $foundFlight['tsat'] ?? "----",
            "ctot" => $foundFlight['ctot'] ?? "----"
        ]);
    } else {
        echo json_encode(["found" => false]);
    }
    exit;
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VATSIM VDGS Pilot Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        /* RESET & BASE */
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', sans-serif;
            background: #f4f6f9;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            color: #333;
        }

        /* --- TOP TOOLBAR --- */
        .top-bar {
            width: 100%;
            background-color: #1f2937;
            color: #fff;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            position: fixed;
            top: 0; left: 0; z-index: 1000;
        }
        .brand {
            font-weight: 700;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .atc-icon {
            width: 24px; height: 24px;
            stroke: #38bdf8; stroke-width: 2; fill: none;
            stroke-linecap: round; stroke-linejoin: round;
        }
        .nav-actions { display: flex; align-items: center; gap: 15px; }
        .nav-btn {
            text-decoration: none; padding: 8px 16px; border-radius: 6px;
            font-size: 0.9rem; font-weight: 600; transition: all 0.2s;
            display: inline-flex; align-items: center; gap: 8px;
        }
        .nav-btn.login { background-color: #29a745; color: white; }
        .nav-btn.login:hover { background-color: #218838; }
        .nav-btn.logout { background-color: #dc3545; color: white; }
        .nav-btn.logout:hover { background-color: #c82333; }
        .user-display {
            font-family: 'Share Tech Mono', monospace;
            color: #facc15; font-size: 1.1rem;
        }

        /* CARD CONTAINER */
        .panel-container {
            display: flex; background: #fff; width: 900px; max-width: 95%;
            border-radius: 12px; box-shadow: 0 15px 40px rgba(0,0,0,0.1);
            overflow: hidden; min-height: 350px; margin-top: 100px; 
        }

        /* LEFT SIDE: LED DISPLAY */
        .led-panel {
            flex: 1; background-color: #1a1a1a;
            display: flex; align-items: center; justify-content: center;
            padding: 40px; position: relative;
        }
        .led-text {
            font-family: 'Share Tech Mono', monospace; font-size: 3.5rem;
            line-height: 1.2; text-align: center; text-transform: uppercase;
            font-weight: 900; 
            background-image: radial-gradient(#ffae00 55%, transparent 60%);
            background-size: 4px 4px;
            -webkit-background-clip: text; background-clip: text;
            -webkit-text-fill-color: transparent; color: transparent;
            filter: drop-shadow(0 0 2px rgba(255, 174, 0, 0.8));
            text-shadow: 0 0 15px rgba(255, 174, 0, 0.4);
        }

        /* RIGHT SIDE: CONTROLS */
        .control-panel {
            flex: 1; padding: 40px; display: flex;
            flex-direction: column; justify-content: center;
        }
        .utc-clock {
            font-size: 2.2rem; color: #4b5563; font-weight: 300; margin-bottom: 30px;
        }
        label {
            display: block; font-weight: 700; font-size: 0.9rem;
            color: #374151; margin-bottom: 12px;
        }
        .input-group { display: flex; gap: 10px; margin-bottom: 20px; }
        input[type="text"] {
            border: 2px solid #e5e7eb; border-radius: 6px; padding: 12px 16px;
            font-size: 1rem; width: 120px; text-align: center;
            font-family: 'Inter', sans-serif; transition: border-color 0.2s;
        }
        input[type="text"]:focus { outline: none; border-color: #3b82f6; }
        button.action-btn {
            background-color: #8ab4f8; color: #fff; border: none;
            border-radius: 6px; padding: 12px 24px; font-size: 1rem;
            font-weight: 700; cursor: pointer; transition: background 0.2s;
        }
        button.action-btn:hover { background-color: #6a9df5; }
        .info-text {
            font-size: 0.9rem; line-height: 1.5; color: #6b7280;
            border-top: 1px solid #e5e7eb; padding-top: 20px;
        }

        /* RESPONSIVE */
        @media (max-width: 768px) {
            .panel-container { flex-direction: column; margin-top: 120px; }
            .led-panel { padding: 30px 20px; min-height: 200px; }
            .led-text { font-size: 2.5rem; }
            .top-bar { flex-direction: column; gap: 10px; padding: 15px; }
        }
    </style>
</head>
<body>

    <nav class="top-bar">
        <div class="brand">
            <svg class="atc-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M7 8 L17 8 L16 3 L8 3 Z" />
                <path d="M10 8 L10 21" />
                <path d="M14 8 L14 21" />
                <path d="M6 21 L18 21" />
                <line x1="12" y1="8" x2="12" y2="21" stroke-dasharray="2 2" stroke-opacity="0.5" />
            </svg>
            vCDM Portal
        </div>
        <div class="nav-actions">
            <div id="logged-in-menu" style="display: none; align-items: center; gap: 15px;">
                <span class="user-display">Flight: <span id="nav-callsign">---</span></span>
                <a href="?action=logout" class="nav-btn logout">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </a>
            </div>

            <a id="login-btn" href="?action=login" class="nav-btn login">
                <i class="fas fa-plane"></i> Login with VATSIM
            </a>
        </div>
    </nav>

    <div class="panel-container">
        <div class="led-panel">
            <div class="led-text" id="vdgs-display">
                PLEASE<br>LOGIN
            </div>
        </div>

        <div class="control-panel">
            <div class="utc-clock" id="utc-clock">00:00:00 UTC</div>

            <div id="manual-controls" style="display:none;">
                <label>Set TOBT (UTC-Time when ready for pushback)</label>
                <div class="input-group">
                    <input type="text" id="tobt-input" placeholder="HHMM" maxlength="4">
                    <button class="action-btn" onclick="submitTOBT()">Submit TOBT</button>
                </div>
            </div>

            <p class="info-text">
                <strong>Info:</strong> Your TOBT (Target Off-Block Time) is the time you are fully ready for pushback. 
                Login above to load your flight data directly from the network.
            </p>
        </div>
    </div>

<script>
    const params = new URLSearchParams(window.location.search);
    const myCallsign = params.get('callsign'); 

    // UI State Management
    if (myCallsign) {
        document.getElementById('login-btn').style.display = 'none';
        document.getElementById('logged-in-menu').style.display = 'flex';
        document.getElementById('nav-callsign').innerText = myCallsign;
        document.getElementById('manual-controls').style.display = 'block';
        document.getElementById('vdgs-display').innerHTML = "LOADING...";
    } else {
        document.getElementById('login-btn').style.display = 'inline-flex';
        document.getElementById('logged-in-menu').style.display = 'none';
        document.getElementById('manual-controls').style.display = 'none'; 
        document.getElementById('vdgs-display').innerHTML = "PLEASE<br>LOGIN";
    }

    // Clock
    function updateClock() {
        const now = new Date();
        const h = String(now.getUTCHours()).padStart(2, '0');
        const m = String(now.getUTCMinutes()).padStart(2, '0');
        const s = String(now.getUTCSeconds()).padStart(2, '0');
        document.getElementById('utc-clock').innerText = `${h}:${m}:${s} UTC`;
    }
    setInterval(updateClock, 1000);
    updateClock();

    // Fetch Data
    async function fetchData() {
        if(!myCallsign) return; 

        try {
            // Note: We now fetch from THIS same file using ?fetch_api=1
            const response = await fetch(`index.php?fetch_api=1&callsign=${myCallsign}`);
            const data = await response.json();

            const display = document.getElementById('vdgs-display');
            const input = document.getElementById('tobt-input');

            if (data.found) {
                let html = `CS: ${data.callsign}<br>`;
                
                if (data.tsat && data.tsat !== "----") {
                    html += `TSAT: ${data.tsat}<br>`;
                    if(data.ctot && data.ctot !== "----") html += `CTOT: ${data.ctot}`;
                } else {
                    html += `TOBT: ${data.tobt}`;
                }
                display.innerHTML = html;

                if(input.value === "" && data.tobt !== "----") {
                    input.placeholder = data.tobt;
                }
            } else {
                display.innerHTML = `FLIGHT PLAN<br>NOT FOUND`;
            }
        } catch (err) {
            console.error(err);
        }
    }

    // Submit TOBT
    async function submitTOBT() {
        const val = document.getElementById('tobt-input').value;
        if (!/^\d{4}$/.test(val)) {
            alert("Please enter time in HHMM format (e.g. 1430)");
            return;
        }

        const btn = document.querySelector('button.action-btn');
        const originalText = btn.innerText;
        btn.innerText = "Sending...";
        btn.disabled = true;

        try {
            const res = await fetch('index.php', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    action: 'update_tobt',
                    callsign: myCallsign,
                    tobt: val
                })
            });
            const result = await res.json();
            
            if(result.status === "success") {
                alert("TOBT Updated!");
                fetchData(); 
            } else {
                alert("Error: " + result.message);
            }
        } catch (e) {
            alert("Connection Failed");
        }
        btn.innerText = originalText;
        btn.disabled = false;
    }

    if(myCallsign) {
        fetchData();
        setInterval(fetchData, 10000); 
    }
</script>
</body>
</html>