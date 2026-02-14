from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

departures = []

ATC_PASSWORD = "atc2024"

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

if __name__ == '__main__':
    print("=" * 50)
    print("Flight Departure Tracking System")
    print("=" * 50)
    print(f"ATC Password: {ATC_PASSWORD}")
    print("Pilot Interface: http://localhost:5000/")
    print("ATC Interface: http://localhost:5000/atc")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
