from flask import Blueprint, request, jsonify, session, redirect
import requests
import os
from datetime import datetime
from src.models.user import db, User
from src.models.strava_token import StravaToken
from src.models.ride import Ride

strava_bp = Blueprint('strava', __name__)

STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

@strava_bp.route('/connect', methods=['GET'])
def connect_strava():
    """Initiate Strava OAuth flow"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Build authorization URL
    redirect_uri = request.host_url.rstrip('/') + '/api/strava/callback'
    scope = 'activity:read_all,profile:read_all'
    
    auth_url = (
        f"https://www.strava.com/oauth/authorize?"
        f"client_id={STRAVA_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={scope}&"
        f"state={session['user_id']}"
    )
    
    return jsonify({'auth_url': auth_url})

@strava_bp.route('/callback', methods=['GET'])
def strava_callback():
    """Handle Strava OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')  # user_id
    error = request.args.get('error')
    
    if error:
        return redirect(f"{FRONTEND_URL}?strava_error={error}")
    
    if not code or not state:
        return redirect(f"{FRONTEND_URL}?strava_error=missing_params")
    
    try:
        # Exchange authorization code for tokens
        redirect_uri = request.host_url.rstrip('/') + '/api/strava/callback'
        
        token_response = requests.post(
            'https://www.strava.com/oauth/token',
            data={
                'client_id': STRAVA_CLIENT_ID,
                'client_secret': STRAVA_CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code'
            }
        )
        
        if token_response.status_code != 200:
            return redirect(f"{FRONTEND_URL}?strava_error=token_exchange_failed")
        
        token_data = token_response.json()
        
        # Save or update Strava token
        user_id = int(state)
        strava_token = StravaToken.query.filter_by(user_id=user_id).first()
        
        if strava_token:
            # Update existing token
            strava_token.access_token = token_data['access_token']
            strava_token.refresh_token = token_data['refresh_token']
            strava_token.expires_at = token_data['expires_at']
            strava_token.athlete_id = token_data['athlete']['id']
            strava_token.athlete_username = token_data['athlete'].get('username')
            strava_token.athlete_firstname = token_data['athlete'].get('firstname')
            strava_token.athlete_lastname = token_data['athlete'].get('lastname')
            strava_token.updated_at = datetime.utcnow()
        else:
            # Create new token
            strava_token = StravaToken(
                user_id=user_id,
                access_token=token_data['access_token'],
                refresh_token=token_data['refresh_token'],
                expires_at=token_data['expires_at'],
                athlete_id=token_data['athlete']['id'],
                athlete_username=token_data['athlete'].get('username'),
                athlete_firstname=token_data['athlete'].get('firstname'),
                athlete_lastname=token_data['athlete'].get('lastname')
            )
            db.session.add(strava_token)
        
        db.session.commit()
        
        # Redirect back to frontend with success
        return redirect(f"{FRONTEND_URL}?strava_connected=true")
        
    except Exception as e:
        print(f"Strava callback error: {str(e)}")
        return redirect(f"{FRONTEND_URL}?strava_error=server_error")

@strava_bp.route('/status', methods=['GET'])
def strava_status():
    """Check if user has connected Strava"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    strava_token = StravaToken.query.filter_by(user_id=session['user_id']).first()
    
    if strava_token:
        return jsonify({
            'connected': True,
            'athlete': strava_token.to_dict(),
            'last_sync': strava_token.last_sync.isoformat() if strava_token.last_sync else None
        })
    else:
        return jsonify({'connected': False})

@strava_bp.route('/disconnect', methods=['POST'])
def disconnect_strava():
    """Disconnect Strava account"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    strava_token = StravaToken.query.filter_by(user_id=session['user_id']).first()
    
    if strava_token:
        # Deauthorize on Strava's end
        try:
            requests.post(
                'https://www.strava.com/oauth/deauthorize',
                data={'access_token': strava_token.access_token}
            )
        except:
            pass  # Continue even if deauthorization fails
        
        db.session.delete(strava_token)
        db.session.commit()
    
    return jsonify({'success': True, 'message': 'Strava disconnected'})

@strava_bp.route('/sync', methods=['POST'])
def sync_activities():
    """Manually trigger activity sync from Strava"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user_id']
    strava_token = StravaToken.query.filter_by(user_id=user_id).first()
    
    if not strava_token:
        return jsonify({'error': 'Strava not connected'}), 400
    
    try:
        # Refresh token if expired
        if strava_token.is_expired():
            refresh_response = requests.post(
                'https://www.strava.com/oauth/token',
                data={
                    'client_id': STRAVA_CLIENT_ID,
                    'client_secret': STRAVA_CLIENT_SECRET,
                    'refresh_token': strava_token.refresh_token,
                    'grant_type': 'refresh_token'
                }
            )
            
            if refresh_response.status_code == 200:
                refresh_data = refresh_response.json()
                strava_token.access_token = refresh_data['access_token']
                strava_token.refresh_token = refresh_data['refresh_token']
                strava_token.expires_at = refresh_data['expires_at']
                db.session.commit()
            else:
                return jsonify({'error': 'Failed to refresh token'}), 400
        
        # Fetch activities from Strava
        activities_response = requests.get(
            'https://www.strava.com/api/v3/athlete/activities',
            headers={'Authorization': f'Bearer {strava_token.access_token}'},
            params={'per_page': 200}
        )
        
        if activities_response.status_code != 200:
            return jsonify({'error': 'Failed to fetch activities'}), 400
        
        activities = activities_response.json()
        imported_count = 0
        
        for activity in activities:
            # Only import rides (cycling activities)
            if activity['type'] not in ['Ride', 'VirtualRide', 'EBikeRide']:
                continue
            
            # Check if activity already exists
            existing_ride = Ride.query.filter_by(
                user_id=user_id,
                name=activity['name'],
                date=datetime.fromisoformat(activity['start_date'].replace('Z', '+00:00'))
            ).first()
            
            if existing_ride:
                continue  # Skip if already imported
            
            # Create new ride
            ride = Ride(
                user_id=user_id,
                name=activity['name'],
                date=datetime.fromisoformat(activity['start_date'].replace('Z', '+00:00')),
                duration=activity.get('moving_time', 0),
                distance=activity.get('distance', 0) / 1000,  # Convert meters to km
                avg_power=activity.get('average_watts'),
                max_power=activity.get('max_watts'),
                avg_heart_rate=int(activity.get('average_heartrate', 0)) if activity.get('average_heartrate') else None,
                max_heart_rate=int(activity.get('max_heartrate', 0)) if activity.get('max_heartrate') else None,
                avg_speed=activity.get('average_speed', 0) * 3.6 if activity.get('average_speed') else None,  # m/s to km/h
                max_speed=activity.get('max_speed', 0) * 3.6 if activity.get('max_speed') else None,
                avg_cadence=int(activity.get('average_cadence', 0)) if activity.get('average_cadence') else None,
                elevation_gain=int(activity.get('total_elevation_gain', 0)),
                training_stress_score=activity.get('suffer_score')
            )
            
            db.session.add(ride)
            imported_count += 1
        
        # Update last sync time
        strava_token.last_sync = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'imported': imported_count,
            'total_activities': len(activities),
            'last_sync': strava_token.last_sync.isoformat()
        })
        
    except Exception as e:
        print(f"Sync error: {str(e)}")
        return jsonify({'error': f'Sync failed: {str(e)}'}), 500

