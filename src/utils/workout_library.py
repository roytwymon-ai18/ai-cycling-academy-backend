"""
Workout Template Library for AI Cycling Academy
Contains 50+ structured workouts across all training zones
"""

def calculate_tss(duration_seconds, intensity_factor):
    """Calculate Training Stress Score"""
    duration_hours = duration_seconds / 3600
    tss = duration_hours * intensity_factor * intensity_factor * 100
    return round(tss, 1)


# Workout templates organized by zone and difficulty
WORKOUT_TEMPLATES = [
    
    # ===== RECOVERY WORKOUTS (Z1) =====
    {
        'name': 'Easy Recovery Spin',
        'short_name': 'Recovery 30min',
        'description': 'Light spinning to promote recovery and blood flow',
        'primary_zone': 'recovery',
        'workout_type': 'steady_state',
        'min_progression_level': 1.0,
        'max_progression_level': 10.0,
        'difficulty_score': 1.0,
        'duration': 1800,  # 30 minutes
        'work_duration': 1800,
        'estimated_tss': 15.0,
        'intensity_factor': 0.45,
        'intervals': [
            {'type': 'steady', 'duration': 1800, 'power': 0.50}
        ],
        'suitable_for_base': True,
        'suitable_for_build': True,
        'suitable_for_specialty': True,
        'tags': ['recovery', 'easy', 'regeneration']
    },
    {
        'name': 'Recovery Ride',
        'short_name': 'Recovery 60min',
        'description': 'Extended easy ride for active recovery',
        'primary_zone': 'recovery',
        'workout_type': 'steady_state',
        'min_progression_level': 1.0,
        'max_progression_level': 10.0,
        'difficulty_score': 1.5,
        'duration': 3600,  # 60 minutes
        'work_duration': 3600,
        'estimated_tss': 30.0,
        'intensity_factor': 0.45,
        'intervals': [
            {'type': 'steady', 'duration': 3600, 'power': 0.50}
        ],
        'suitable_for_base': True,
        'suitable_for_build': True,
        'suitable_for_specialty': True,
        'tags': ['recovery', 'easy', 'regeneration']
    },
    
    # ===== ENDURANCE WORKOUTS (Z2) =====
    {
        'name': 'Base Endurance 90',
        'short_name': 'Endurance 90min',
        'description': 'Steady aerobic endurance ride',
        'primary_zone': 'endurance',
        'workout_type': 'steady_state',
        'min_progression_level': 2.0,
        'max_progression_level': 6.0,
        'difficulty_score': 3.0,
        'duration': 5400,  # 90 minutes
        'work_duration': 5400,
        'estimated_tss': 60.0,
        'intensity_factor': 0.65,
        'intervals': [
            {'type': 'warmup', 'duration': 600, 'power': 0.55},
            {'type': 'steady', 'duration': 4200, 'power': 0.65},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': True,
        'suitable_for_build': True,
        'suitable_for_specialty': False,
        'tags': ['endurance', 'aerobic', 'base']
    },
    {
        'name': 'Long Endurance Ride',
        'short_name': 'Endurance 2hr',
        'description': 'Extended aerobic base building ride',
        'primary_zone': 'endurance',
        'workout_type': 'steady_state',
        'min_progression_level': 3.0,
        'max_progression_level': 7.0,
        'difficulty_score': 4.0,
        'duration': 7200,  # 2 hours
        'work_duration': 7200,
        'estimated_tss': 85.0,
        'intensity_factor': 0.65,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'steady', 'duration': 5400, 'power': 0.65},
            {'type': 'cooldown', 'duration': 900, 'power': 0.55}
        ],
        'suitable_for_base': True,
        'suitable_for_build': True,
        'suitable_for_specialty': False,
        'tags': ['endurance', 'aerobic', 'long_ride']
    },
    {
        'name': 'Epic Endurance',
        'short_name': 'Endurance 3hr',
        'description': 'Long aerobic ride for endurance development',
        'primary_zone': 'endurance',
        'workout_type': 'steady_state',
        'min_progression_level': 4.0,
        'max_progression_level': 8.0,
        'difficulty_score': 5.5,
        'duration': 10800,  # 3 hours
        'work_duration': 10800,
        'estimated_tss': 135.0,
        'intensity_factor': 0.67,
        'intervals': [
            {'type': 'warmup', 'duration': 1200, 'power': 0.55},
            {'type': 'steady', 'duration': 8400, 'power': 0.67},
            {'type': 'cooldown', 'duration': 1200, 'power': 0.55}
        ],
        'suitable_for_base': True,
        'suitable_for_build': False,
        'suitable_for_specialty': False,
        'tags': ['endurance', 'aerobic', 'long_ride', 'century_prep']
    },
    
    # ===== TEMPO WORKOUTS (Z3) =====
    {
        'name': 'Tempo Intervals 2x20',
        'short_name': 'Tempo 2x20',
        'description': 'Two 20-minute tempo intervals',
        'primary_zone': 'tempo',
        'workout_type': 'intervals',
        'min_progression_level': 2.0,
        'max_progression_level': 5.0,
        'difficulty_score': 4.5,
        'duration': 4200,  # 70 minutes
        'work_duration': 2400,
        'estimated_tss': 65.0,
        'intensity_factor': 0.78,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 1200, 'power': 0.82, 'repeats': 2},
            {'type': 'recovery', 'duration': 300, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': True,
        'suitable_for_build': True,
        'suitable_for_specialty': False,
        'tags': ['tempo', 'muscular_endurance']
    },
    {
        'name': 'Tempo Intervals 3x15',
        'short_name': 'Tempo 3x15',
        'description': 'Three 15-minute tempo intervals',
        'primary_zone': 'tempo',
        'workout_type': 'intervals',
        'min_progression_level': 2.5,
        'max_progression_level': 5.5,
        'difficulty_score': 5.0,
        'duration': 4500,  # 75 minutes
        'work_duration': 2700,
        'estimated_tss': 70.0,
        'intensity_factor': 0.79,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 900, 'power': 0.83, 'repeats': 3},
            {'type': 'recovery', 'duration': 300, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': True,
        'suitable_for_build': True,
        'suitable_for_specialty': False,
        'tags': ['tempo', 'muscular_endurance']
    },
    {
        'name': 'Sustained Tempo',
        'short_name': 'Tempo 60min',
        'description': 'Single 60-minute tempo effort',
        'primary_zone': 'tempo',
        'workout_type': 'steady_state',
        'min_progression_level': 4.0,
        'max_progression_level': 7.0,
        'difficulty_score': 6.0,
        'duration': 5400,  # 90 minutes
        'work_duration': 3600,
        'estimated_tss': 85.0,
        'intensity_factor': 0.80,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 3600, 'power': 0.80},
            {'type': 'cooldown', 'duration': 900, 'power': 0.55}
        ],
        'suitable_for_base': True,
        'suitable_for_build': True,
        'suitable_for_specialty': False,
        'tags': ['tempo', 'muscular_endurance', 'time_trial']
    },
    
    # ===== SWEET SPOT WORKOUTS (Z4a) =====
    {
        'name': 'Sweet Spot 3x10',
        'short_name': 'SS 3x10',
        'description': 'Three 10-minute sweet spot intervals',
        'primary_zone': 'sweet_spot',
        'workout_type': 'intervals',
        'min_progression_level': 2.0,
        'max_progression_level': 4.5,
        'difficulty_score': 5.0,
        'duration': 3900,  # 65 minutes
        'work_duration': 1800,
        'estimated_tss': 70.0,
        'intensity_factor': 0.86,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 600, 'power': 0.90, 'repeats': 3},
            {'type': 'recovery', 'duration': 180, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': True,
        'suitable_for_build': True,
        'suitable_for_specialty': False,
        'tags': ['sweet_spot', 'ftp_builder', 'time_efficient']
    },
    {
        'name': 'Sweet Spot 3x12',
        'short_name': 'SS 3x12',
        'description': 'Three 12-minute sweet spot intervals',
        'primary_zone': 'sweet_spot',
        'workout_type': 'intervals',
        'min_progression_level': 2.5,
        'max_progression_level': 5.0,
        'difficulty_score': 5.5,
        'duration': 4200,  # 70 minutes
        'work_duration': 2160,
        'estimated_tss': 75.0,
        'intensity_factor': 0.86,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 720, 'power': 0.90, 'repeats': 3},
            {'type': 'recovery', 'duration': 180, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': True,
        'suitable_for_build': True,
        'suitable_for_specialty': False,
        'tags': ['sweet_spot', 'ftp_builder', 'time_efficient']
    },
    {
        'name': 'Sweet Spot 2x20',
        'short_name': 'SS 2x20',
        'description': 'Two 20-minute sweet spot intervals',
        'primary_zone': 'sweet_spot',
        'workout_type': 'intervals',
        'min_progression_level': 3.5,
        'max_progression_level': 6.0,
        'difficulty_score': 6.5,
        'duration': 4800,  # 80 minutes
        'work_duration': 2400,
        'estimated_tss': 85.0,
        'intensity_factor': 0.87,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 1200, 'power': 0.90, 'repeats': 2},
            {'type': 'recovery', 'duration': 300, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': True,
        'suitable_for_build': True,
        'suitable_for_specialty': False,
        'tags': ['sweet_spot', 'ftp_builder', 'muscular_endurance']
    },
    {
        'name': 'Sweet Spot 4x10',
        'short_name': 'SS 4x10',
        'description': 'Four 10-minute sweet spot intervals',
        'primary_zone': 'sweet_spot',
        'workout_type': 'intervals',
        'min_progression_level': 3.0,
        'max_progression_level': 5.5,
        'difficulty_score': 6.0,
        'duration': 4500,  # 75 minutes
        'work_duration': 2400,
        'estimated_tss': 80.0,
        'intensity_factor': 0.87,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 600, 'power': 0.92, 'repeats': 4},
            {'type': 'recovery', 'duration': 180, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': False,
        'suitable_for_build': True,
        'suitable_for_specialty': False,
        'tags': ['sweet_spot', 'ftp_builder']
    },
    
    # ===== THRESHOLD WORKOUTS (Z4b) =====
    {
        'name': 'Threshold 4x8',
        'short_name': 'Threshold 4x8',
        'description': 'Four 8-minute threshold intervals',
        'primary_zone': 'threshold',
        'workout_type': 'intervals',
        'min_progression_level': 2.0,
        'max_progression_level': 4.5,
        'difficulty_score': 6.0,
        'duration': 4200,  # 70 minutes
        'work_duration': 1920,
        'estimated_tss': 80.0,
        'intensity_factor': 0.92,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 480, 'power': 1.00, 'repeats': 4},
            {'type': 'recovery', 'duration': 240, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': False,
        'suitable_for_build': True,
        'suitable_for_specialty': True,
        'tags': ['threshold', 'ftp_builder', 'lactate_threshold']
    },
    {
        'name': 'Threshold 3x10',
        'short_name': 'Threshold 3x10',
        'description': 'Three 10-minute threshold intervals',
        'primary_zone': 'threshold',
        'workout_type': 'intervals',
        'min_progression_level': 2.5,
        'max_progression_level': 5.0,
        'difficulty_score': 6.5,
        'duration': 4500,  # 75 minutes
        'work_duration': 1800,
        'estimated_tss': 85.0,
        'intensity_factor': 0.92,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 600, 'power': 1.00, 'repeats': 3},
            {'type': 'recovery', 'duration': 300, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': False,
        'suitable_for_build': True,
        'suitable_for_specialty': True,
        'tags': ['threshold', 'ftp_builder', 'lactate_threshold']
    },
    {
        'name': 'Threshold 2x20',
        'short_name': 'Threshold 2x20',
        'description': 'Two 20-minute threshold intervals (FTP test workout)',
        'primary_zone': 'threshold',
        'workout_type': 'intervals',
        'min_progression_level': 4.0,
        'max_progression_level': 7.0,
        'difficulty_score': 8.0,
        'duration': 5400,  # 90 minutes
        'work_duration': 2400,
        'estimated_tss': 100.0,
        'intensity_factor': 0.95,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 1200, 'power': 0.95, 'repeats': 2},
            {'type': 'recovery', 'duration': 600, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': False,
        'suitable_for_build': True,
        'suitable_for_specialty': True,
        'tags': ['threshold', 'ftp_test', 'time_trial']
    },
    {
        'name': 'Over-Unders 6x6',
        'short_name': 'O/U 6x6',
        'description': 'Six 6-minute over-under intervals',
        'primary_zone': 'threshold',
        'secondary_zone': 'sweet_spot',
        'workout_type': 'intervals',
        'min_progression_level': 3.0,
        'max_progression_level': 6.0,
        'difficulty_score': 7.0,
        'duration': 4500,  # 75 minutes
        'work_duration': 2160,
        'estimated_tss': 90.0,
        'intensity_factor': 0.93,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 120, 'power': 1.05, 'repeats': 6},
            {'type': 'work', 'duration': 240, 'power': 0.90, 'repeats': 6},
            {'type': 'recovery', 'duration': 180, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': False,
        'suitable_for_build': True,
        'suitable_for_specialty': True,
        'tags': ['threshold', 'over_under', 'lactate_tolerance']
    },
    
    # ===== VO2 MAX WORKOUTS (Z5) =====
    {
        'name': 'VO2 Max 6x3',
        'short_name': 'VO2 6x3',
        'description': 'Six 3-minute VO2 max intervals',
        'primary_zone': 'vo2max',
        'workout_type': 'intervals',
        'min_progression_level': 2.0,
        'max_progression_level': 4.5,
        'difficulty_score': 7.0,
        'duration': 4200,  # 70 minutes
        'work_duration': 1080,
        'estimated_tss': 85.0,
        'intensity_factor': 0.98,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 180, 'power': 1.15, 'repeats': 6},
            {'type': 'recovery', 'duration': 180, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': False,
        'suitable_for_build': True,
        'suitable_for_specialty': True,
        'tags': ['vo2max', 'aerobic_capacity', 'high_intensity']
    },
    {
        'name': 'VO2 Max 5x5',
        'short_name': 'VO2 5x5',
        'description': 'Five 5-minute VO2 max intervals',
        'primary_zone': 'vo2max',
        'workout_type': 'intervals',
        'min_progression_level': 3.0,
        'max_progression_level': 6.0,
        'difficulty_score': 8.0,
        'duration': 4800,  # 80 minutes
        'work_duration': 1500,
        'estimated_tss': 95.0,
        'intensity_factor': 1.00,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 300, 'power': 1.12, 'repeats': 5},
            {'type': 'recovery', 'duration': 300, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': False,
        'suitable_for_build': True,
        'suitable_for_specialty': True,
        'tags': ['vo2max', 'aerobic_capacity', 'high_intensity']
    },
    {
        'name': 'VO2 Max 3x8',
        'short_name': 'VO2 3x8',
        'description': 'Three 8-minute VO2 max intervals',
        'primary_zone': 'vo2max',
        'workout_type': 'intervals',
        'min_progression_level': 4.0,
        'max_progression_level': 7.5,
        'difficulty_score': 8.5,
        'duration': 5100,  # 85 minutes
        'work_duration': 1440,
        'estimated_tss': 100.0,
        'intensity_factor': 1.02,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 480, 'power': 1.10, 'repeats': 3},
            {'type': 'recovery', 'duration': 360, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': False,
        'suitable_for_build': False,
        'suitable_for_specialty': True,
        'tags': ['vo2max', 'aerobic_capacity', 'high_intensity']
    },
    {
        'name': 'Micro Bursts 10x1',
        'short_name': 'Micro 10x1',
        'description': 'Ten 1-minute micro bursts at VO2 max',
        'primary_zone': 'vo2max',
        'workout_type': 'intervals',
        'min_progression_level': 2.5,
        'max_progression_level': 5.0,
        'difficulty_score': 7.5,
        'duration': 3600,  # 60 minutes
        'work_duration': 600,
        'estimated_tss': 75.0,
        'intensity_factor': 0.95,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 60, 'power': 1.20, 'repeats': 10},
            {'type': 'recovery', 'duration': 120, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': False,
        'suitable_for_build': True,
        'suitable_for_specialty': True,
        'tags': ['vo2max', 'micro_bursts', 'high_intensity']
    },
    
    # ===== ANAEROBIC WORKOUTS (Z6) =====
    {
        'name': 'Anaerobic 10x30sec',
        'short_name': 'Anaerobic 10x30',
        'description': 'Ten 30-second anaerobic efforts',
        'primary_zone': 'anaerobic',
        'workout_type': 'intervals',
        'min_progression_level': 2.0,
        'max_progression_level': 5.0,
        'difficulty_score': 7.5,
        'duration': 3600,  # 60 minutes
        'work_duration': 300,
        'estimated_tss': 70.0,
        'intensity_factor': 0.92,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 30, 'power': 1.50, 'repeats': 10},
            {'type': 'recovery', 'duration': 180, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': False,
        'suitable_for_build': False,
        'suitable_for_specialty': True,
        'tags': ['anaerobic', 'sprint', 'power']
    },
    {
        'name': 'Sprint Intervals 8x20sec',
        'short_name': 'Sprint 8x20',
        'description': 'Eight 20-second all-out sprints',
        'primary_zone': 'anaerobic',
        'workout_type': 'intervals',
        'min_progression_level': 2.5,
        'max_progression_level': 6.0,
        'difficulty_score': 8.0,
        'duration': 3300,  # 55 minutes
        'work_duration': 160,
        'estimated_tss': 65.0,
        'intensity_factor': 0.88,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 20, 'power': 2.00, 'repeats': 8},
            {'type': 'recovery', 'duration': 220, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': False,
        'suitable_for_build': False,
        'suitable_for_specialty': True,
        'tags': ['anaerobic', 'sprint', 'neuromuscular']
    },
    {
        'name': 'Tabata Intervals',
        'short_name': 'Tabata 8x20/10',
        'description': 'Eight rounds of 20sec on, 10sec off',
        'primary_zone': 'anaerobic',
        'workout_type': 'intervals',
        'min_progression_level': 3.0,
        'max_progression_level': 7.0,
        'difficulty_score': 8.5,
        'duration': 3000,  # 50 minutes
        'work_duration': 160,
        'estimated_tss': 60.0,
        'intensity_factor': 0.85,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 20, 'power': 1.80, 'repeats': 8},
            {'type': 'recovery', 'duration': 10, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': False,
        'suitable_for_build': False,
        'suitable_for_specialty': True,
        'tags': ['anaerobic', 'tabata', 'high_intensity']
    },
    
    # ===== MIXED ZONE WORKOUTS =====
    {
        'name': 'Pyramid Intervals',
        'short_name': 'Pyramid',
        'description': '1-2-3-4-3-2-1 minute intervals at threshold',
        'primary_zone': 'threshold',
        'secondary_zone': 'vo2max',
        'workout_type': 'mixed',
        'min_progression_level': 3.5,
        'max_progression_level': 6.5,
        'difficulty_score': 7.5,
        'duration': 4800,  # 80 minutes
        'work_duration': 960,
        'estimated_tss': 90.0,
        'intensity_factor': 0.94,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 60, 'power': 1.00},
            {'type': 'recovery', 'duration': 60, 'power': 0.50},
            {'type': 'work', 'duration': 120, 'power': 1.00},
            {'type': 'recovery', 'duration': 120, 'power': 0.50},
            {'type': 'work', 'duration': 180, 'power': 1.00},
            {'type': 'recovery', 'duration': 180, 'power': 0.50},
            {'type': 'work', 'duration': 240, 'power': 1.00},
            {'type': 'recovery', 'duration': 240, 'power': 0.50},
            {'type': 'work', 'duration': 180, 'power': 1.00},
            {'type': 'recovery', 'duration': 180, 'power': 0.50},
            {'type': 'work', 'duration': 120, 'power': 1.00},
            {'type': 'recovery', 'duration': 120, 'power': 0.50},
            {'type': 'work', 'duration': 60, 'power': 1.00},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': False,
        'suitable_for_build': True,
        'suitable_for_specialty': True,
        'tags': ['mixed', 'threshold', 'variety']
    },
    {
        'name': 'Race Simulation',
        'short_name': 'Race Sim',
        'description': 'Mixed intensity ride simulating race efforts',
        'primary_zone': 'threshold',
        'secondary_zone': 'vo2max',
        'workout_type': 'mixed',
        'min_progression_level': 5.0,
        'max_progression_level': 8.0,
        'difficulty_score': 9.0,
        'duration': 5400,  # 90 minutes
        'work_duration': 3600,
        'estimated_tss': 110.0,
        'intensity_factor': 1.05,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'steady', 'duration': 1200, 'power': 0.85},
            {'type': 'work', 'duration': 180, 'power': 1.15, 'repeats': 3},
            {'type': 'recovery', 'duration': 120, 'power': 0.60},
            {'type': 'work', 'duration': 300, 'power': 1.05},
            {'type': 'recovery', 'duration': 180, 'power': 0.60},
            {'type': 'work', 'duration': 60, 'power': 1.50, 'repeats': 5},
            {'type': 'recovery', 'duration': 60, 'power': 0.60},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': False,
        'suitable_for_build': False,
        'suitable_for_specialty': True,
        'tags': ['mixed', 'race_prep', 'high_intensity']
    },
    
    # ===== FTP TEST WORKOUTS =====
    {
        'name': 'Ramp Test',
        'short_name': 'Ramp Test',
        'description': 'Progressive ramp test to failure for FTP assessment',
        'primary_zone': 'threshold',
        'workout_type': 'test',
        'min_progression_level': 1.0,
        'max_progression_level': 10.0,
        'difficulty_score': 9.0,
        'duration': 3600,  # 60 minutes
        'work_duration': 1200,
        'estimated_tss': 75.0,
        'intensity_factor': 0.90,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'ramp', 'start_power': 0.50, 'increment': 0.05, 'step_duration': 60, 'steps': 20},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': True,
        'suitable_for_build': True,
        'suitable_for_specialty': True,
        'tags': ['test', 'ftp', 'ramp']
    },
    {
        'name': '8-Minute FTP Test',
        'short_name': '8min Test',
        'description': 'Two 8-minute all-out efforts for FTP assessment',
        'primary_zone': 'threshold',
        'workout_type': 'test',
        'min_progression_level': 1.0,
        'max_progression_level': 10.0,
        'difficulty_score': 9.5,
        'duration': 4500,  # 75 minutes
        'work_duration': 960,
        'estimated_tss': 85.0,
        'intensity_factor': 0.95,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 480, 'power': 1.10, 'repeats': 2},
            {'type': 'recovery', 'duration': 600, 'power': 0.50},
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': True,
        'suitable_for_build': True,
        'suitable_for_specialty': True,
        'tags': ['test', 'ftp', '8_minute']
    },
    {
        'name': '20-Minute FTP Test',
        'short_name': '20min Test',
        'description': 'Single 20-minute all-out effort for FTP assessment',
        'primary_zone': 'threshold',
        'workout_type': 'test',
        'min_progression_level': 1.0,
        'max_progression_level': 10.0,
        'difficulty_score': 10.0,
        'duration': 4800,  # 80 minutes
        'work_duration': 1200,
        'estimated_tss': 90.0,
        'intensity_factor': 0.95,
        'intervals': [
            {'type': 'warmup', 'duration': 900, 'power': 0.55},
            {'type': 'work', 'duration': 300, 'power': 1.00},  # 5-min effort
            {'type': 'recovery', 'duration': 600, 'power': 0.50},
            {'type': 'work', 'duration': 1200, 'power': 1.00},  # 20-min test
            {'type': 'cooldown', 'duration': 600, 'power': 0.55}
        ],
        'suitable_for_base': True,
        'suitable_for_build': True,
        'suitable_for_specialty': True,
        'tags': ['test', 'ftp', '20_minute']
    },
]


def get_workout_by_criteria(zone, progression_level, phase, duration_range=None):
    """
    Find suitable workouts based on criteria
    
    Args:
        zone: Primary training zone
        progression_level: Current progression level in that zone
        phase: Training phase ('base', 'build', 'specialty')
        duration_range: Tuple of (min_duration, max_duration) in seconds
    
    Returns:
        List of matching workout templates
    """
    matching_workouts = []
    
    for workout in WORKOUT_TEMPLATES:
        # Check zone
        if workout['primary_zone'] != zone:
            continue
        
        # Check progression level
        if not (workout['min_progression_level'] <= progression_level <= workout['max_progression_level']):
            continue
        
        # Check phase suitability
        phase_key = f'suitable_for_{phase}'
        if not workout.get(phase_key, False):
            continue
        
        # Check duration if specified
        if duration_range:
            min_dur, max_dur = duration_range
            if not (min_dur <= workout['duration'] <= max_dur):
                continue
        
        matching_workouts.append(workout)
    
    return matching_workouts


def get_test_workout(test_type):
    """Get FTP test workout by type"""
    test_names = {
        'ramp': 'Ramp Test',
        '8_minute': '8-Minute FTP Test',
        '20_minute': '20-Minute FTP Test'
    }
    
    test_name = test_names.get(test_type)
    for workout in WORKOUT_TEMPLATES:
        if workout['name'] == test_name:
            return workout
    
    return None

