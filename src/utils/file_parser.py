"""
File parser for cycling data files (.fit, .tcx, .gpx)
Extracts ride metrics and converts to standard format
"""
import os
from datetime import datetime
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

try:
    from fitparse import FitFile
except ImportError:
    FitFile = None

try:
    import gpxpy
    import gpxpy.gpx
except ImportError:
    gpxpy = None


class RideFileParser:
    """Parse cycling data files and extract metrics"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_extension = os.path.splitext(file_path)[1].lower()
        
    def parse(self) -> Dict:
        """Parse the file and return ride data"""
        if self.file_extension == '.fit':
            return self._parse_fit()
        elif self.file_extension == '.gpx':
            return self._parse_gpx()
        elif self.file_extension == '.tcx':
            return self._parse_tcx()
        else:
            raise ValueError(f"Unsupported file type: {self.file_extension}")
    
    def _parse_fit(self) -> Dict:
        """Parse .fit file"""
        if FitFile is None:
            raise ImportError("fitparse library not installed")
        
        fitfile = FitFile(self.file_path)
        
        # Initialize data structures
        ride_data = {
            'name': os.path.basename(self.file_path).replace('.fit', ''),
            'date': None,
            'distance': 0,
            'duration': 0,
            'elevation_gain': 0,
            'avg_power': 0,
            'avg_heart_rate': 0,
            'avg_cadence': 0,
            'max_speed': 0,
            'calories': 0,
            'tss': 0,
            'data_points': []
        }
        
        # Track metrics for averaging
        power_values = []
        hr_values = []
        cadence_values = []
        speed_values = []
        elevation_points = []
        
        # Parse records
        for record in fitfile.get_messages('record'):
            point = {}
            
            for record_data in record:
                if record_data.name == 'timestamp':
                    point['timestamp'] = record_data.value
                    if ride_data['date'] is None:
                        ride_data['date'] = record_data.value
                elif record_data.name == 'distance':
                    point['distance'] = record_data.value / 1000  # Convert to km
                    ride_data['distance'] = point['distance']
                elif record_data.name == 'power':
                    point['power'] = record_data.value
                    if record_data.value and record_data.value > 0:
                        power_values.append(record_data.value)
                elif record_data.name == 'heart_rate':
                    point['heart_rate'] = record_data.value
                    if record_data.value and record_data.value > 0:
                        hr_values.append(record_data.value)
                elif record_data.name == 'cadence':
                    point['cadence'] = record_data.value
                    if record_data.value and record_data.value > 0:
                        cadence_values.append(record_data.value)
                elif record_data.name == 'speed':
                    point['speed'] = record_data.value * 3.6  # Convert m/s to km/h
                    if record_data.value:
                        speed_values.append(point['speed'])
                elif record_data.name == 'altitude':
                    point['elevation'] = record_data.value
                    elevation_points.append(record_data.value)
            
            if point:
                ride_data['data_points'].append(point)
        
        # Parse session data for summary
        for session in fitfile.get_messages('session'):
            for session_data in session:
                if session_data.name == 'total_elapsed_time':
                    ride_data['duration'] = int(session_data.value / 60)  # Convert to minutes
                elif session_data.name == 'total_calories':
                    ride_data['calories'] = session_data.value
                elif session_data.name == 'total_ascent':
                    ride_data['elevation_gain'] = session_data.value
        
        # Calculate averages
        if power_values:
            ride_data['avg_power'] = int(sum(power_values) / len(power_values))
        if hr_values:
            ride_data['avg_heart_rate'] = int(sum(hr_values) / len(hr_values))
        if cadence_values:
            ride_data['avg_cadence'] = int(sum(cadence_values) / len(cadence_values))
        if speed_values:
            ride_data['max_speed'] = max(speed_values)
        
        # Calculate elevation gain if not in session
        if ride_data['elevation_gain'] == 0 and len(elevation_points) > 1:
            ride_data['elevation_gain'] = self._calculate_elevation_gain(elevation_points)
        
        return ride_data
    
    def _parse_gpx(self) -> Dict:
        """Parse .gpx file"""
        if gpxpy is None:
            raise ImportError("gpxpy library not installed")
        
        with open(self.file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
        
        ride_data = {
            'name': os.path.basename(self.file_path).replace('.gpx', ''),
            'date': None,
            'distance': 0,
            'duration': 0,
            'elevation_gain': 0,
            'avg_power': 0,
            'avg_heart_rate': 0,
            'avg_cadence': 0,
            'max_speed': 0,
            'calories': 0,
            'tss': 0,
            'data_points': []
        }
        
        hr_values = []
        cadence_values = []
        power_values = []
        
        for track in gpx.tracks:
            for segment in track.segments:
                prev_point = None
                
                for point in segment.points:
                    data_point = {
                        'timestamp': point.time,
                        'latitude': point.latitude,
                        'longitude': point.longitude,
                        'elevation': point.elevation
                    }
                    
                    # Extract extensions (heart rate, cadence, power)
                    if point.extensions:
                        for ext in point.extensions:
                            # TrackPointExtension namespace
                            ns = {'ns': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'}
                            
                            hr = ext.find('.//ns:hr', ns)
                            if hr is not None and hr.text:
                                data_point['heart_rate'] = int(hr.text)
                                hr_values.append(int(hr.text))
                            
                            cad = ext.find('.//ns:cad', ns)
                            if cad is not None and cad.text:
                                data_point['cadence'] = int(cad.text)
                                cadence_values.append(int(cad.text))
                            
                            power = ext.find('.//ns:power', ns)
                            if power is not None and power.text:
                                data_point['power'] = int(power.text)
                                power_values.append(int(power.text))
                    
                    ride_data['data_points'].append(data_point)
                    
                    if ride_data['date'] is None and point.time:
                        ride_data['date'] = point.time
                    
                    if prev_point and point.time and prev_point.time:
                        # Calculate speed
                        distance = point.distance_3d(prev_point) or point.distance_2d(prev_point)
                        time_diff = (point.time - prev_point.time).total_seconds()
                        if time_diff > 0:
                            speed = (distance / time_diff) * 3.6  # km/h
                            data_point['speed'] = speed
                    
                    prev_point = point
        
        # Calculate summary metrics
        ride_data['distance'] = gpx.length_3d() / 1000 if gpx.length_3d() else gpx.length_2d() / 1000
        
        uphill, downhill = gpx.get_uphill_downhill()
        ride_data['elevation_gain'] = int(uphill) if uphill else 0
        
        moving_data = gpx.get_moving_data()
        if moving_data:
            ride_data['duration'] = int(moving_data.moving_time / 60)  # minutes
            ride_data['max_speed'] = moving_data.max_speed * 3.6 if moving_data.max_speed else 0
        
        if hr_values:
            ride_data['avg_heart_rate'] = int(sum(hr_values) / len(hr_values))
        if cadence_values:
            ride_data['avg_cadence'] = int(sum(cadence_values) / len(cadence_values))
        if power_values:
            ride_data['avg_power'] = int(sum(power_values) / len(power_values))
        
        return ride_data
    
    def _parse_tcx(self) -> Dict:
        """Parse .tcx file"""
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        
        # TCX namespace
        ns = {'ns': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
        
        ride_data = {
            'name': os.path.basename(self.file_path).replace('.tcx', ''),
            'date': None,
            'distance': 0,
            'duration': 0,
            'elevation_gain': 0,
            'avg_power': 0,
            'avg_heart_rate': 0,
            'avg_cadence': 0,
            'max_speed': 0,
            'calories': 0,
            'tss': 0,
            'data_points': []
        }
        
        hr_values = []
        cadence_values = []
        power_values = []
        elevation_points = []
        
        # Find all activities
        for activity in root.findall('.//ns:Activity', ns):
            for lap in activity.findall('.//ns:Lap', ns):
                # Get lap summary
                total_time = lap.find('ns:TotalTimeSeconds', ns)
                if total_time is not None:
                    ride_data['duration'] += int(float(total_time.text) / 60)
                
                distance = lap.find('ns:DistanceMeters', ns)
                if distance is not None:
                    ride_data['distance'] = float(distance.text) / 1000
                
                calories = lap.find('ns:Calories', ns)
                if calories is not None:
                    ride_data['calories'] += int(calories.text)
                
                # Parse trackpoints
                for trackpoint in lap.findall('.//ns:Trackpoint', ns):
                    point = {}
                    
                    time = trackpoint.find('ns:Time', ns)
                    if time is not None:
                        point['timestamp'] = datetime.fromisoformat(time.text.replace('Z', '+00:00'))
                        if ride_data['date'] is None:
                            ride_data['date'] = point['timestamp']
                    
                    hr = trackpoint.find('.//ns:HeartRateBpm/ns:Value', ns)
                    if hr is not None:
                        point['heart_rate'] = int(hr.text)
                        hr_values.append(int(hr.text))
                    
                    cadence = trackpoint.find('ns:Cadence', ns)
                    if cadence is not None:
                        point['cadence'] = int(cadence.text)
                        cadence_values.append(int(cadence.text))
                    
                    # Power in extensions
                    power = trackpoint.find('.//ns:Watts', ns)
                    if power is not None:
                        point['power'] = int(power.text)
                        power_values.append(int(power.text))
                    
                    altitude = trackpoint.find('ns:AltitudeMeters', ns)
                    if altitude is not None:
                        point['elevation'] = float(altitude.text)
                        elevation_points.append(float(altitude.text))
                    
                    dist = trackpoint.find('ns:DistanceMeters', ns)
                    if dist is not None:
                        point['distance'] = float(dist.text) / 1000
                    
                    ride_data['data_points'].append(point)
        
        # Calculate averages
        if hr_values:
            ride_data['avg_heart_rate'] = int(sum(hr_values) / len(hr_values))
        if cadence_values:
            ride_data['avg_cadence'] = int(sum(cadence_values) / len(cadence_values))
        if power_values:
            ride_data['avg_power'] = int(sum(power_values) / len(power_values))
        
        # Calculate elevation gain
        if elevation_points:
            ride_data['elevation_gain'] = self._calculate_elevation_gain(elevation_points)
        
        return ride_data
    
    def _calculate_elevation_gain(self, elevation_points: List[float]) -> int:
        """Calculate total elevation gain from elevation points"""
        gain = 0
        for i in range(1, len(elevation_points)):
            diff = elevation_points[i] - elevation_points[i-1]
            if diff > 0:
                gain += diff
        return int(gain)
    
    @staticmethod
    def calculate_tss(duration_minutes: int, avg_power: int, ftp: int) -> int:
        """Calculate Training Stress Score"""
        if ftp == 0 or avg_power == 0:
            return 0
        
        intensity_factor = avg_power / ftp
        normalized_power = avg_power  # Simplified, should use NP algorithm
        
        tss = (duration_minutes * 60 * normalized_power * intensity_factor) / (ftp * 3600) * 100
        return int(tss)

