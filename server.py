from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
import secrets
import os
import sys
import requests
from math import radians, cos, sin, asin, sqrt

# Check if templates folder exists
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
if not os.path.exists(template_dir):
    print("=" * 60)
    print("ERROR: 'templates' folder not found!")
    print("=" * 60)
    print(f"Expected location: {template_dir}")
    print("\nPlease ensure you have the following structure:")
    print("  your-folder/")
    print("  ├── server.py")
    print("  └── templates/")
    print("      ├── pilot.html")
    print("      ├── atc_login.html")
    print("      └── atc.html")
    print("=" * 60)
    sys.exit(1)

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# In-memory storage for departures
departures = []

# ATC password (change this to your desired password)
ATC_PASSWORD = "atc2024"

# Ukrainian airports configuration
UKRAINE_AIRPORTS = {
    'UKBB': {'name': 'Kyiv Boryspil', 'lat': 50.345, 'lon': 30.894722},
    'UKKK': {'name': 'Kyiv Zhuliany', 'lat': 50.401694, 'lon': 30.449697},
    'UKLL': {'name': 'Lviv', 'lat': 49.8125, 'lon': 23.956111},
    'UKDD': {'name': 'Dnipro', 'lat': 48.357222, 'lon': 35.100556},
    'UKHH': {'name': 'Kharkiv', 'lat': 49.924786, 'lon': 36.290003},
    'UKOO': {'name': 'Odesa', 'lat': 46.426767, 'lon': 30.676464},
}

# Frankfurt airport for testing only (not in main list)
FRANKFURT_AIRPORT = {
    'EDDF': {'name': 'Frankfurt', 'lat': 50.0379, 'lon': 8.5622}
}

# All airports (includes Frankfurt for API endpoints)
ALL_AIRPORTS = {**UKRAINE_AIRPORTS, **FRANKFURT_AIRPORT}

# Minimum separation standards (distance only)
SEPARATION_STANDARDS = {
    'conflict_nm': 3.0,    # Less than 3 NM = CONFLICT
    'monitor_nm': 5.0,     # 3-5 NM = MONITOR
    # More than 5 NM = OK
}

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points in nautical miles"""
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in kilometers is 6371
    # Convert to nautical miles (1 km = 0.539957 nm)
    nm = 6371 * c * 0.539957
    return nm

def fetch_vatsim_data():
    """Fetch live data from VATSIM"""
    try:
        response = requests.get('https://data.vatsim.net/v3/vatsim-data.json', timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching VATSIM data: {e}")
        return None

@app.route('/')
def pilot_interface():
    """Pilot interface for filing departure times"""
    return render_template('pilot.html')

@app.route('/atc')
def atc_interface():
    """ATC interface - password protected"""
    if not session.get('atc_authenticated'):
        return redirect(url_for('atc_login'))
    return render_template('atc.html')

@app.route('/atc/login', methods=['GET', 'POST'])
def atc_login():
    """ATC login page"""
    if request.method == 'POST':
        password = request.json.get('password')
        if password == ATC_PASSWORD:
            session['atc_authenticated'] = True
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid password'})
    return render_template('atc_login.html')

@app.route('/atc/logout')
def atc_logout():
    """ATC logout"""
    session.pop('atc_authenticated', None)
    return redirect(url_for('atc_login'))

@app.route('/frankfurt-test')
def frankfurt_test():
    """Frankfurt test interface - password protected"""
    if not session.get('atc_authenticated'):
        return redirect(url_for('atc_login'))
    return render_template('frankfurt_test.html')

@app.route('/api/departures', methods=['GET'])
def get_departures():
    """Get all departures with time remaining"""
    current_time = datetime.now()
    updated_departures = []
    
    for dep in departures:
        departure_time = datetime.fromisoformat(dep['departure_time'])
        time_remaining = (departure_time - current_time).total_seconds()
        
        updated_departures.append({
            'id': dep['id'],
            'callsign': dep['callsign'],
            'departure_time': dep['departure_time'],
            'time_remaining': max(0, time_remaining),
            'filed_at': dep['filed_at']
        })
    
    return jsonify(updated_departures)

@app.route('/api/departures', methods=['POST'])
def add_departure():
    """Add a new departure"""
    data = request.json
    callsign = data.get('callsign', '').strip().upper()
    departure_time = data.get('departure_time')
    
    if not callsign or not departure_time:
        return jsonify({'success': False, 'message': 'Callsign and departure time are required'}), 400
    
    # Validate datetime format
    try:
        datetime.fromisoformat(departure_time)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid datetime format'}), 400
    
    departure_id = len(departures) + 1
    new_departure = {
        'id': departure_id,
        'callsign': callsign,
        'departure_time': departure_time,
        'filed_at': datetime.now().isoformat()
    }
    
    departures.append(new_departure)
    return jsonify({'success': True, 'departure': new_departure})

@app.route('/api/departures/<int:departure_id>', methods=['DELETE'])
def delete_departure(departure_id):
    """Delete a departure - requires ATC authentication"""
    if not session.get('atc_authenticated'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    global departures
    departures = [d for d in departures if d['id'] != departure_id]
    return jsonify({'success': True})

@app.route('/api/airports', methods=['GET'])
def get_airports():
    """Get list of Ukrainian airports (excludes Frankfurt)"""
    airports_list = [
        {'icao': icao, 'name': data['name']} 
        for icao, data in UKRAINE_AIRPORTS.items()
    ]
    return jsonify(airports_list)

@app.route('/api/arrivals/<airport_icao>', methods=['GET'])
def get_arrivals(airport_icao):
    """Get arrivals for a specific airport from VATSIM"""
    if airport_icao not in ALL_AIRPORTS:
        return jsonify({'error': 'Airport not found'}), 404
    
    vatsim_data = fetch_vatsim_data()
    if not vatsim_data:
        return jsonify({'error': 'Failed to fetch VATSIM data'}), 500
    
    airport = ALL_AIRPORTS[airport_icao]
    arrivals = []
    
    # Filter pilots heading to this airport
    for pilot in vatsim_data.get('pilots', []):
        # Check if destination matches
        flight_plan = pilot.get('flight_plan')
        if not flight_plan or flight_plan.get('arrival') != airport_icao:
            continue
        
        # Calculate distance to airport
        distance = haversine_distance(
            pilot['latitude'], 
            pilot['longitude'],
            airport['lat'],
            airport['lon']
        )
        
        # Only include aircraft within 200nm
        if distance > 200:
            continue
        
        # Calculate ETA (estimated time of arrival)
        groundspeed = pilot.get('groundspeed', 0)
        if groundspeed > 0:
            eta_minutes = (distance / groundspeed) * 60
        else:
            eta_minutes = 999
        
        arrivals.append({
            'callsign': pilot['callsign'],
            'aircraft_type': flight_plan.get('aircraft_short', 'ZZZZ'),
            'departure': flight_plan.get('departure', ''),
            'altitude': pilot.get('altitude', 0),
            'groundspeed': groundspeed,
            'distance': round(distance, 1),
            'eta_minutes': round(eta_minutes, 1),
            'latitude': pilot['latitude'],
            'longitude': pilot['longitude']
        })
    
    # Sort by ETA
    arrivals.sort(key=lambda x: x['eta_minutes'])
    
    # Calculate separation between consecutive aircraft
    for i in range(len(arrivals)):
        if i > 0:
            # Distance separation (nautical miles between aircraft)
            distance_sep = arrivals[i]['distance'] - arrivals[i-1]['distance']
            arrivals[i]['distance_separation'] = round(abs(distance_sep), 1)
            
            # Determine separation status based on distance only
            if abs(distance_sep) < SEPARATION_STANDARDS['conflict_nm']:
                arrivals[i]['separation_status'] = 'conflict'
            elif abs(distance_sep) < SEPARATION_STANDARDS['monitor_nm']:
                arrivals[i]['separation_status'] = 'monitor'
            else:
                arrivals[i]['separation_status'] = 'ok'
        else:
            arrivals[i]['distance_separation'] = None
            arrivals[i]['separation_status'] = 'ok'
    
    return jsonify({
        'airport': airport_icao,
        'airport_name': airport['name'],
        'arrivals': arrivals,
        'total_count': len(arrivals)
    })

@app.route('/api/vatsim-departures/<airport_icao>', methods=['GET'])
def get_vatsim_departures(airport_icao):
    """Get VATSIM preplanned departures for a specific airport"""
    if airport_icao not in ALL_AIRPORTS:
        return jsonify({'error': 'Airport not found'}), 404
    
    vatsim_data = fetch_vatsim_data()
    if not vatsim_data:
        return jsonify({'error': 'Failed to fetch VATSIM data'}), 500
    
    airport = ALL_AIRPORTS[airport_icao]
    vatsim_departures = []
    
    # Filter preplanned flights departing from this airport
    for prefiled in vatsim_data.get('prefiles', []):
        flight_plan = prefiled.get('flight_plan')
        if not flight_plan or flight_plan.get('departure') != airport_icao:
            continue
        
        vatsim_departures.append({
            'callsign': prefiled['callsign'],
            'aircraft_type': flight_plan.get('aircraft_short', 'ZZZZ'),
            'destination': flight_plan.get('arrival', ''),
            'route': flight_plan.get('route', ''),
            'altitude': flight_plan.get('altitude', ''),
            'remarks': flight_plan.get('remarks', ''),
            'source': 'vatsim_prefile'
        })
    
    # Filter pilots on ground at this airport
    for pilot in vatsim_data.get('pilots', []):
        flight_plan = pilot.get('flight_plan')
        if not flight_plan or flight_plan.get('departure') != airport_icao:
            continue
        
        # Check if on ground (altitude < 500ft and groundspeed < 50kts)
        if pilot.get('altitude', 1000) > 500 or pilot.get('groundspeed', 100) > 50:
            continue
        
        # Calculate distance from airport
        distance = haversine_distance(
            pilot['latitude'], 
            pilot['longitude'],
            airport['lat'],
            airport['lon']
        )
        
        # Only include if within 5nm of airport
        if distance > 5:
            continue
        
        vatsim_departures.append({
            'callsign': pilot['callsign'],
            'aircraft_type': flight_plan.get('aircraft_short', 'ZZZZ'),
            'destination': flight_plan.get('arrival', ''),
            'route': flight_plan.get('route', ''),
            'altitude': flight_plan.get('altitude', ''),
            'remarks': flight_plan.get('remarks', ''),
            'source': 'vatsim_ground'
        })
    
    # Sort by callsign
    vatsim_departures.sort(key=lambda x: x['callsign'])
    
    return jsonify({
        'airport': airport_icao,
        'airport_name': airport['name'],
        'departures': vatsim_departures,
        'total_count': len(vatsim_departures)
    })

@app.route('/api/all-departures/<airport_icao>', methods=['GET'])
def get_all_departures(airport_icao):
    """Get combined departures: manually filed + VATSIM preplanned"""
    if airport_icao not in ALL_AIRPORTS:
        return jsonify({'error': 'Airport not found'}), 404
    
    # Get manually filed departures
    manual_deps = []
    current_time = datetime.now()
    
    for dep in departures:
        departure_time = datetime.fromisoformat(dep['departure_time'])
        time_remaining = (departure_time - current_time).total_seconds()
        
        manual_deps.append({
            'id': dep['id'],
            'callsign': dep['callsign'],
            'departure_time': dep['departure_time'],
            'time_remaining': max(0, time_remaining),
            'filed_at': dep['filed_at'],
            'source': 'manual',
            'aircraft_type': 'N/A',
            'destination': 'N/A'
        })
    
    # Get VATSIM departures
    vatsim_data = fetch_vatsim_data()
    vatsim_deps = []
    
    if vatsim_data:
        # Preplanned flights
        for prefiled in vatsim_data.get('prefiles', []):
            flight_plan = prefiled.get('flight_plan')
            if not flight_plan or flight_plan.get('departure') != airport_icao:
                continue
            
            vatsim_deps.append({
                'callsign': prefiled['callsign'],
                'aircraft_type': flight_plan.get('aircraft_short', 'ZZZZ'),
                'destination': flight_plan.get('arrival', ''),
                'route': flight_plan.get('route', ''),
                'altitude': flight_plan.get('altitude', ''),
                'source': 'vatsim_prefile'
            })
        
        # Ground aircraft
        for pilot in vatsim_data.get('pilots', []):
            flight_plan = pilot.get('flight_plan')
            if not flight_plan or flight_plan.get('departure') != airport_icao:
                continue
            
            if pilot.get('altitude', 1000) > 500 or pilot.get('groundspeed', 100) > 50:
                continue
            
            airport_data = ALL_AIRPORTS[airport_icao]
            distance = haversine_distance(
                pilot['latitude'], 
                pilot['longitude'],
                airport_data['lat'],
                airport_data['lon']
            )
            
            if distance > 5:
                continue
            
            vatsim_deps.append({
                'callsign': pilot['callsign'],
                'aircraft_type': flight_plan.get('aircraft_short', 'ZZZZ'),
                'destination': flight_plan.get('arrival', ''),
                'route': flight_plan.get('route', ''),
                'altitude': flight_plan.get('altitude', ''),
                'source': 'vatsim_ground'
            })
    
    return jsonify({
        'airport': airport_icao,
        'airport_name': ALL_AIRPORTS[airport_icao]['name'],
        'manual_departures': manual_deps,
        'vatsim_departures': vatsim_deps,
        'manual_count': len(manual_deps),
        'vatsim_count': len(vatsim_deps),
        'total_count': len(manual_deps) + len(vatsim_deps)
    })

if __name__ == '__main__':
    print("=" * 50)
    print("Flight Departure Tracking System")
    print("=" * 50)
    print(f"ATC Password: {ATC_PASSWORD}")
    print("Pilot Interface: http://localhost:5000/")
    print("ATC Interface: http://localhost:5000/atc")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
