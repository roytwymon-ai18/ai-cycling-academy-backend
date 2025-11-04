"""
Workout File Import/Export for AI Cycling Academy
Supports .mrc, .erg, and .zwo formats
"""

import xml.etree.ElementTree as ET
import json
from typing import Dict, List, Any


class WorkoutFileParser:
    """Parse workout files in various formats"""
    
    @staticmethod
    def parse_mrc(file_content: str, user_ftp: int = None) -> Dict[str, Any]:
        """
        Parse MRC format workout file
        
        MRC format:
        [COURSE HEADER]
        [END COURSE HEADER]
        [COURSE DATA]
        58 5.0
        71 10.0
        [END COURSE DATA]
        
        Returns workout dict with intervals
        """
        lines = file_content.strip().split('\n')
        intervals = []
        in_data_section = False
        
        for line in lines:
            line = line.strip()
            
            if '[COURSE DATA]' in line:
                in_data_section = True
                continue
            elif '[END COURSE DATA]' in line:
                break
            
            if in_data_section and line:
                try:
                    parts = line.split()
                    if len(parts) >= 2:
                        power_percent = float(parts[0])
                        duration_minutes = float(parts[1])
                        
                        intervals.append({
                            'type': 'steady',
                            'duration': int(duration_minutes * 60),
                            'power': power_percent / 100.0
                        })
                except ValueError:
                    continue
        
        if not intervals:
            raise ValueError("No valid workout data found in MRC file")
        
        # Calculate total duration and estimated TSS
        total_duration = sum(i['duration'] for i in intervals)
        avg_power = sum(i['power'] * i['duration'] for i in intervals) / total_duration
        estimated_tss = (total_duration / 3600) * avg_power * avg_power * 100
        
        return {
            'name': 'Imported MRC Workout',
            'description': 'Workout imported from MRC file',
            'primary_zone': WorkoutFileParser._determine_zone(avg_power),
            'workout_type': 'intervals',
            'duration': total_duration,
            'estimated_tss': round(estimated_tss, 1),
            'intensity_factor': round(avg_power, 2),
            'intervals': intervals,
            'tags': ['imported', 'mrc']
        }
    
    @staticmethod
    def parse_erg(file_content: str, user_ftp: int) -> Dict[str, Any]:
        """
        Parse ERG format workout file
        
        ERG format:
        [COURSE HEADER]
        FTP=280
        [END COURSE HEADER]
        [COURSE DATA]
        162 5.0
        200 10.0
        [END COURSE DATA]
        
        Converts absolute watts to % FTP
        """
        lines = file_content.strip().split('\n')
        intervals = []
        in_data_section = False
        file_ftp = user_ftp
        
        # Extract FTP from file if present
        for line in lines:
            if 'FTP=' in line:
                try:
                    file_ftp = int(line.split('=')[1].strip())
                except:
                    pass
        
        if not user_ftp:
            user_ftp = file_ftp
        
        # Parse workout data
        for line in lines:
            line = line.strip()
            
            if '[COURSE DATA]' in line:
                in_data_section = True
                continue
            elif '[END COURSE DATA]' in line:
                break
            
            if in_data_section and line:
                try:
                    parts = line.split()
                    if len(parts) >= 2:
                        power_watts = float(parts[0])
                        duration_minutes = float(parts[1])
                        
                        # Convert to % FTP
                        power_percent = power_watts / user_ftp
                        
                        intervals.append({
                            'type': 'steady',
                            'duration': int(duration_minutes * 60),
                            'power': round(power_percent, 2)
                        })
                except ValueError:
                    continue
        
        if not intervals:
            raise ValueError("No valid workout data found in ERG file")
        
        # Calculate total duration and estimated TSS
        total_duration = sum(i['duration'] for i in intervals)
        avg_power = sum(i['power'] * i['duration'] for i in intervals) / total_duration
        estimated_tss = (total_duration / 3600) * avg_power * avg_power * 100
        
        return {
            'name': 'Imported ERG Workout',
            'description': f'Workout imported from ERG file (FTP: {file_ftp}W)',
            'primary_zone': WorkoutFileParser._determine_zone(avg_power),
            'workout_type': 'intervals',
            'duration': total_duration,
            'estimated_tss': round(estimated_tss, 1),
            'intensity_factor': round(avg_power, 2),
            'intervals': intervals,
            'tags': ['imported', 'erg']
        }
    
    @staticmethod
    def parse_zwo(file_content: str) -> Dict[str, Any]:
        """
        Parse ZWO (Zwift) format workout file
        
        ZWO is XML format with elements like:
        <Warmup Duration="300" PowerLow="0.50" PowerHigh="0.70"/>
        <SteadyState Duration="600" Power="0.90"/>
        <IntervalsT Repeat="3" OnDuration="300" OffDuration="180" OnPower="1.05" OffPower="0.50"/>
        """
        try:
            root = ET.fromstring(file_content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid ZWO XML format: {e}")
        
        # Extract metadata
        name = root.findtext('name', 'Imported ZWO Workout')
        description = root.findtext('description', 'Workout imported from ZWO file')
        author = root.findtext('author', '')
        
        # Parse workout elements
        workout_elem = root.find('workout')
        if workout_elem is None:
            raise ValueError("No workout element found in ZWO file")
        
        intervals = []
        
        for elem in workout_elem:
            if elem.tag == 'Warmup':
                duration = int(elem.get('Duration', 0))
                power_low = float(elem.get('PowerLow', 0.5))
                power_high = float(elem.get('PowerHigh', 0.7))
                intervals.append({
                    'type': 'warmup',
                    'duration': duration,
                    'power_low': power_low,
                    'power_high': power_high,
                    'power': (power_low + power_high) / 2  # Average for TSS calc
                })
            
            elif elem.tag == 'Cooldown':
                duration = int(elem.get('Duration', 0))
                power_low = float(elem.get('PowerLow', 0.5))
                power_high = float(elem.get('PowerHigh', 0.7))
                intervals.append({
                    'type': 'cooldown',
                    'duration': duration,
                    'power_low': power_low,
                    'power_high': power_high,
                    'power': (power_low + power_high) / 2
                })
            
            elif elem.tag == 'SteadyState':
                duration = int(elem.get('Duration', 0))
                power = float(elem.get('Power', 0.7))
                intervals.append({
                    'type': 'steady',
                    'duration': duration,
                    'power': power
                })
            
            elif elem.tag == 'IntervalsT':
                repeat = int(elem.get('Repeat', 1))
                on_duration = int(elem.get('OnDuration', 0))
                off_duration = int(elem.get('OffDuration', 0))
                on_power = float(elem.get('OnPower', 1.0))
                off_power = float(elem.get('OffPower', 0.5))
                
                for _ in range(repeat):
                    intervals.append({
                        'type': 'work',
                        'duration': on_duration,
                        'power': on_power
                    })
                    intervals.append({
                        'type': 'recovery',
                        'duration': off_duration,
                        'power': off_power
                    })
            
            elif elem.tag == 'Ramp':
                duration = int(elem.get('Duration', 0))
                power_low = float(elem.get('PowerLow', 0.5))
                power_high = float(elem.get('PowerHigh', 1.0))
                intervals.append({
                    'type': 'ramp',
                    'duration': duration,
                    'power_low': power_low,
                    'power_high': power_high,
                    'power': (power_low + power_high) / 2
                })
            
            elif elem.tag == 'FreeRide':
                duration = int(elem.get('Duration', 0))
                intervals.append({
                    'type': 'free',
                    'duration': duration,
                    'power': 0.65  # Assume moderate effort
                })
        
        if not intervals:
            raise ValueError("No valid workout intervals found in ZWO file")
        
        # Calculate total duration and estimated TSS
        total_duration = sum(i['duration'] for i in intervals)
        avg_power = sum(i['power'] * i['duration'] for i in intervals) / total_duration
        estimated_tss = (total_duration / 3600) * avg_power * avg_power * 100
        
        # Extract tags
        tags = ['imported', 'zwo']
        tag_elems = root.findall('.//tag')
        for tag_elem in tag_elems:
            tag_name = tag_elem.get('name', '').lower()
            if tag_name:
                tags.append(tag_name)
        
        return {
            'name': name,
            'description': description,
            'author': author,
            'primary_zone': WorkoutFileParser._determine_zone(avg_power),
            'workout_type': 'intervals',
            'duration': total_duration,
            'estimated_tss': round(estimated_tss, 1),
            'intensity_factor': round(avg_power, 2),
            'intervals': intervals,
            'tags': tags
        }
    
    @staticmethod
    def _determine_zone(avg_power_percent: float) -> str:
        """Determine training zone from average power"""
        if avg_power_percent < 0.55:
            return 'recovery'
        elif avg_power_percent < 0.75:
            return 'endurance'
        elif avg_power_percent < 0.87:
            return 'tempo'
        elif avg_power_percent < 0.95:
            return 'sweet_spot'
        elif avg_power_percent < 1.05:
            return 'threshold'
        elif avg_power_percent < 1.20:
            return 'vo2max'
        else:
            return 'anaerobic'


class WorkoutFileExporter:
    """Export workouts to various file formats"""
    
    @staticmethod
    def export_to_mrc(workout: Dict[str, Any]) -> str:
        """Export workout to MRC format"""
        lines = []
        lines.append('[COURSE HEADER]')
        lines.append(f'VERSION = 2')
        lines.append(f'UNITS = ENGLISH')
        lines.append(f'DESCRIPTION = {workout.get("name", "Workout")}')
        lines.append(f'FILE NAME = {workout.get("short_name", "workout").replace(" ", "_")}.mrc')
        lines.append('[END COURSE HEADER]')
        lines.append('[COURSE DATA]')
        
        for interval in workout['intervals']:
            power_percent = interval['power'] * 100
            duration_minutes = interval['duration'] / 60
            lines.append(f'{power_percent:.1f}\t{duration_minutes:.2f}')
        
        lines.append('[END COURSE DATA]')
        
        return '\n'.join(lines)
    
    @staticmethod
    def export_to_erg(workout: Dict[str, Any], user_ftp: int) -> str:
        """Export workout to ERG format"""
        lines = []
        lines.append('[COURSE HEADER]')
        lines.append(f'VERSION = 2')
        lines.append(f'UNITS = ENGLISH')
        lines.append(f'DESCRIPTION = {workout.get("name", "Workout")}')
        lines.append(f'FILE NAME = {workout.get("short_name", "workout").replace(" ", "_")}.erg')
        lines.append(f'FTP = {user_ftp}')
        lines.append('[END COURSE HEADER]')
        lines.append('[COURSE DATA]')
        
        for interval in workout['intervals']:
            power_watts = int(interval['power'] * user_ftp)
            duration_minutes = interval['duration'] / 60
            lines.append(f'{power_watts}\t{duration_minutes:.2f}')
        
        lines.append('[END COURSE DATA]')
        
        return '\n'.join(lines)
    
    @staticmethod
    def export_to_zwo(workout: Dict[str, Any]) -> str:
        """Export workout to ZWO (Zwift) format"""
        root = ET.Element('workout_file')
        
        # Metadata
        ET.SubElement(root, 'author').text = 'AI Cycling Academy'
        ET.SubElement(root, 'name').text = workout.get('name', 'Workout')
        ET.SubElement(root, 'description').text = workout.get('description', '')
        ET.SubElement(root, 'sportType').text = 'bike'
        
        # Tags
        tags_elem = ET.SubElement(root, 'tags')
        for tag in workout.get('tags', []):
            ET.SubElement(tags_elem, 'tag', name=tag.title())
        
        # Workout intervals
        workout_elem = ET.SubElement(root, 'workout')
        
        for interval in workout['intervals']:
            interval_type = interval.get('type', 'steady')
            duration = interval['duration']
            
            if interval_type == 'warmup':
                ET.SubElement(workout_elem, 'Warmup', 
                            Duration=str(duration),
                            PowerLow=str(interval.get('power_low', interval['power'] * 0.7)),
                            PowerHigh=str(interval.get('power_high', interval['power'])))
            
            elif interval_type == 'cooldown':
                ET.SubElement(workout_elem, 'Cooldown',
                            Duration=str(duration),
                            PowerLow=str(interval.get('power_high', interval['power'])),
                            PowerHigh=str(interval.get('power_low', interval['power'] * 0.7)))
            
            elif interval_type in ['steady', 'work']:
                repeats = interval.get('repeats', 1)
                if repeats > 1:
                    # This is a simplified representation - ZWO doesn't have direct repeats for SteadyState
                    for _ in range(repeats):
                        ET.SubElement(workout_elem, 'SteadyState',
                                    Duration=str(duration),
                                    Power=str(interval['power']))
                else:
                    ET.SubElement(workout_elem, 'SteadyState',
                                Duration=str(duration),
                                Power=str(interval['power']))
            
            elif interval_type == 'recovery':
                ET.SubElement(workout_elem, 'SteadyState',
                            Duration=str(duration),
                            Power=str(interval['power']))
            
            elif interval_type == 'ramp':
                ET.SubElement(workout_elem, 'Ramp',
                            Duration=str(duration),
                            PowerLow=str(interval.get('power_low', 0.5)),
                            PowerHigh=str(interval.get('power_high', 1.0)))
        
        # Convert to string with proper formatting
        ET.indent(root, space='    ')
        return ET.tostring(root, encoding='unicode', method='xml')
    
    @staticmethod
    def export_to_json(workout: Dict[str, Any]) -> str:
        """Export workout to JSON format (Cadence-compatible)"""
        return json.dumps(workout, indent=2)


# Example usage functions
def import_workout_file(file_path: str, file_type: str, user_ftp: int = None) -> Dict[str, Any]:
    """
    Import a workout file
    
    Args:
        file_path: Path to workout file
        file_type: 'mrc', 'erg', or 'zwo'
        user_ftp: User's FTP (required for ERG files)
    
    Returns:
        Workout dictionary
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    parser = WorkoutFileParser()
    
    if file_type == 'mrc':
        return parser.parse_mrc(content, user_ftp)
    elif file_type == 'erg':
        if not user_ftp:
            raise ValueError("user_ftp required for ERG file import")
        return parser.parse_erg(content, user_ftp)
    elif file_type == 'zwo':
        return parser.parse_zwo(content)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def export_workout_file(workout: Dict[str, Any], output_path: str, file_type: str, user_ftp: int = None):
    """
    Export a workout to file
    
    Args:
        workout: Workout dictionary
        output_path: Path to save file
        file_type: 'mrc', 'erg', 'zwo', or 'json'
        user_ftp: User's FTP (required for ERG export)
    """
    exporter = WorkoutFileExporter()
    
    if file_type == 'mrc':
        content = exporter.export_to_mrc(workout)
    elif file_type == 'erg':
        if not user_ftp:
            raise ValueError("user_ftp required for ERG file export")
        content = exporter.export_to_erg(workout, user_ftp)
    elif file_type == 'zwo':
        content = exporter.export_to_zwo(workout)
    elif file_type == 'json':
        content = exporter.export_to_json(workout)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    with open(output_path, 'w') as f:
        f.write(content)

