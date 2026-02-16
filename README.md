# Flight Departure Tracking System + VATSIM Arrivals Manager

A real-time flight departure tracking system with separate interfaces for pilots and ATC, now with integrated VATSIM arrivals manager.

## Features

### Pilot Interface
- File departure times with callsign
- Time-only input (Zulu/UTC) - date is automatically today
- Simple, user-friendly interface
- Accessible at: `http://localhost:5000/`

### ATC Interface (Password Protected)
**Departures Tab:**
- Real-time monitoring of all departures
- Live countdown timer for each flight
- Visual indicators for departing soon / departed flights
- Delete functionality for departures
- Auto-refreshes every second

**Arrivals Manager Tab (VATSIM Integration):**
- Select Ukrainian airports (UKBB, UKKK, UKLL, UKDD, UKHH, UKOO)
- Real-time arrivals from VATSIM network
- Shows aircraft within 200NM of selected airport
- Displays:
  - Callsign, aircraft type, departure airport
  - Altitude, groundspeed, distance to airport
  - ETA (Estimated Time of Arrival)
  - Time separation between consecutive aircraft
  - Distance separation between aircraft
  - Separation status (OK / MONITOR / CONFLICT)
- Auto-refreshes every 10 seconds
- Accessible at: `http://localhost:5000/atc`

## Quick Start (No Installation Required!)

### Linux/Mac:
```bash
./start_server.sh
```

### Windows:
```
start_server.bat
```

The startup script will:
1. Create a temporary virtual environment
2. Install Flask and requests libraries temporarily (won't affect your system)
3. Start the server
4. Clean up everything when you stop the server (Ctrl+C)

### Manual Start (Alternative):
If you prefer to run manually:
```bash
python server.py
```
Note: This requires Flask and requests to be installed on your system.

The server will start on `http://localhost:5000`

## Important: File Structure

Make sure you have this structure:
```
your-folder/
├── server.py
├── start_server.sh (or .bat)
├── check_setup.py
└── templates/
    ├── pilot.html
    ├── atc_login.html
    └── atc.html
```

**⚠️ Common Issue:** If you get "TemplateNotFound" error, it means the `templates` folder is missing or in the wrong location. Make sure:
1. The `templates` folder is in the SAME directory as `server.py`
2. All three HTML files are inside the `templates` folder

### Verify Setup:
Run this to check if all files are present:
```bash
python check_setup.py
```

## Default Credentials

**ATC Password:** `atc2024`

You can change this password by editing the `ATC_PASSWORD` variable in `server.py`

## Usage

### For Pilots:
1. Navigate to `http://localhost:5000/`
2. Enter your callsign (e.g., AAL123)
3. Select your departure time (Zulu/UTC) - today's date is automatic
4. Click "File Departure"

### For ATC:
1. Navigate to `http://localhost:5000/atc`
2. Enter the ATC password
3. **Departures Tab:**
   - Monitor all filed departures in real-time
   - Click "Delete" on any card to remove a departure
4. **Arrivals Manager Tab:**
   - Click on any Ukrainian airport to view arrivals
   - Monitor separation between aircraft
   - Green (✓ OK) = Safe separation
   - Yellow (⚠ MONITOR) = Reduced separation, monitor closely
   - Red (✗ CONFLICT) = Insufficient separation

## VATSIM Integration

The arrivals manager fetches live data from VATSIM every 10 seconds. It shows:
- All aircraft within 200 nautical miles of the selected airport
- Aircraft must have the airport as their filed destination
- Separation standards:
  - Minimum distance: 3.0 NM
  - Minimum time: 2.5 minutes

## Supported Ukrainian Airports

- **UKBB** - Kyiv Boryspil
- **UKKK** - Kyiv Zhuliany
- **UKLL** - Lviv
- **UKDD** - Dnipro
- **UKHH** - Kharkiv
- **UKOO** - Odesa

## File Structure

```
.
├── server.py                 # Flask server with VATSIM integration
├── start_server.sh           # Linux/Mac startup script
├── start_server.bat          # Windows startup script
├── check_setup.py            # Setup verification script
└── templates/
    ├── pilot.html           # Pilot interface
    ├── atc_login.html       # ATC login page
    └── atc.html             # ATC monitoring interface (with arrivals manager)
```

## Notes

- Departure data is stored in memory and will be lost when the server restarts
- The departures tab auto-refreshes every second
- The arrivals manager auto-refreshes every 10 seconds
- Times are displayed in Zulu/UTC
- VATSIM data requires internet connection
- Arrivals are sorted by ETA (closest aircraft first)
