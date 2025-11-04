"""
Training Plan Generation Engine for AI Cycling Academy
Generates personalized, periodized training plans based on rider goals
"""

from datetime import datetime, timedelta
from src.models.training_plan import TrainingPlan, PlannedWorkout, ProgressionLevel
from src.utils.workout_library import WORKOUT_TEMPLATES, get_workout_by_criteria, get_test_workout
from src.models.user import db
import random


class PlanGenerator:
    """Generates personalized training plans"""
    
    def __init__(self, user):
        self.user = user
        self.progression_levels = self._get_or_create_progression_levels()
    
    def _get_or_create_progression_levels(self):
        """Get existing progression levels or create new ones"""
        levels = ProgressionLevel.query.filter_by(user_id=self.user.id).first()
        if not levels:
            levels = ProgressionLevel(user_id=self.user.id)
            db.session.add(levels)
            db.session.commit()
        return levels
    
    def generate_plan(self, goal_type, goal_description, weeks, hours_per_week, rides_per_week, training_days, target_ftp=None):
        """
        Generate a complete training plan
        
        Args:
            goal_type: 'ftp_increase', 'century_ride', 'race_prep', 'general_fitness'
            goal_description: User's stated goal
            weeks: Total weeks for the plan
            hours_per_week: Available training hours per week
            rides_per_week: Number of rides per week
            training_days: List of training day numbers (0=Monday)
            target_ftp: Optional FTP goal
        
        Returns:
            TrainingPlan object with all PlannedWorkouts
        """
        
        # Create training plan
        plan = TrainingPlan(
            user_id=self.user.id,
            name=self._generate_plan_name(goal_type, weeks),
            goal=goal_description,
            goal_type=goal_type,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(weeks=weeks),
            baseline_ftp=self.user.current_ftp,
            baseline_weight=self.user.weight,
            target_ftp=target_ftp,
            total_weeks=weeks,
            weekly_hours_available=hours_per_week,
            rides_per_week=rides_per_week,
            training_days=training_days,
            status='active',
            current_week=1
        )
        
        # Determine phase distribution
        phases = self._calculate_phases(weeks, goal_type)
        plan.base_weeks = phases['base']
        plan.build_weeks = phases['build']
        plan.specialty_weeks = phases['specialty']
        plan.current_phase = 'base'
        
        # Schedule FTP tests
        plan.last_ftp_test = datetime.now()
        plan.next_ftp_test = datetime.now() + timedelta(weeks=4)
        
        # Generate workouts for each week
        week_start = datetime.now().date()
        for week_num in range(1, weeks + 1):
            phase = self._get_phase_for_week(week_num, phases)
            week_in_mesocycle = ((week_num - 1) % 4) + 1
            
            # Generate workouts for this week
            week_workouts = self._generate_week_workouts(
                plan=plan,
                week_num=week_num,
                phase=phase,
                week_in_mesocycle=week_in_mesocycle,
                rides_per_week=rides_per_week,
                hours_per_week=hours_per_week,
                training_days=training_days,
                week_start=week_start
            )
            
            # Add workouts to plan
            for workout in week_workouts:
                plan.workouts.append(workout)
            
            week_start += timedelta(weeks=1)
        
        # Save plan
        db.session.add(plan)
        db.session.commit()
        
        return plan
    
    def _generate_plan_name(self, goal_type, weeks):
        """Generate a descriptive plan name"""
        names = {
            'ftp_increase': f'{weeks}-Week FTP Builder',
            'century_ride': f'{weeks}-Week Century Prep',
            'race_prep': f'{weeks}-Week Race Preparation',
            'general_fitness': f'{weeks}-Week General Fitness'
        }
        return names.get(goal_type, f'{weeks}-Week Training Plan')
    
    def _calculate_phases(self, total_weeks, goal_type):
        """Calculate phase distribution based on total weeks and goal"""
        
        if goal_type == 'ftp_increase' or goal_type == 'general_fitness':
            # More build phase for FTP gains
            if total_weeks <= 8:
                return {'base': total_weeks // 2, 'build': total_weeks // 2, 'specialty': 0}
            elif total_weeks <= 16:
                base = total_weeks // 3
                build = total_weeks // 2
                specialty = total_weeks - base - build
                return {'base': base, 'build': build, 'specialty': specialty}
            else:
                base = total_weeks // 3
                build = total_weeks // 2
                specialty = total_weeks - base - build
                return {'base': base, 'build': build, 'specialty': specialty}
        
        elif goal_type == 'century_ride':
            # More endurance base
            if total_weeks <= 8:
                return {'base': total_weeks * 2 // 3, 'build': total_weeks // 3, 'specialty': 0}
            else:
                base = total_weeks // 2
                build = total_weeks // 3
                specialty = total_weeks - base - build
                return {'base': base, 'build': build, 'specialty': specialty}
        
        elif goal_type == 'race_prep':
            # Balanced with specialty phase
            if total_weeks <= 8:
                return {'base': total_weeks // 3, 'build': total_weeks // 2, 'specialty': total_weeks // 6}
            else:
                base = total_weeks // 3
                build = total_weeks // 3
                specialty = total_weeks - base - build
                return {'base': base, 'build': build, 'specialty': specialty}
        
        # Default distribution
        return {'base': total_weeks // 3, 'build': total_weeks // 2, 'specialty': total_weeks // 6}
    
    def _get_phase_for_week(self, week_num, phases):
        """Determine which phase a given week falls into"""
        if week_num <= phases['base']:
            return 'base'
        elif week_num <= phases['base'] + phases['build']:
            return 'build'
        else:
            return 'specialty'
    
    def _generate_week_workouts(self, plan, week_num, phase, week_in_mesocycle, rides_per_week, hours_per_week, training_days, week_start):
        """Generate workouts for a single week"""
        
        workouts = []
        
        # Calculate target TSS for the week
        weekly_tss = self._calculate_weekly_tss(hours_per_week, phase, week_in_mesocycle)
        
        # Determine workout types for the week based on phase
        workout_distribution = self._get_workout_distribution(phase, rides_per_week)
        
        # Schedule FTP test if needed (every 4 weeks)
        if week_num % 4 == 0 and week_num > 0:
            workout_distribution[0] = 'test'  # Replace first workout with test
        
        # Generate each workout
        for i, workout_type in enumerate(workout_distribution):
            if i >= len(training_days):
                break
            
            day_offset = training_days[i]
            scheduled_date = week_start + timedelta(days=day_offset)
            
            if workout_type == 'test':
                workout = self._create_test_workout(plan, week_num, phase, scheduled_date)
            else:
                workout = self._create_workout(plan, week_num, phase, workout_type, scheduled_date, weekly_tss / rides_per_week)
            
            if workout:
                workouts.append(workout)
        
        return workouts
    
    def _calculate_weekly_tss(self, hours_per_week, phase, week_in_mesocycle):
        """Calculate target TSS for the week"""
        
        # Base TSS per hour by phase
        base_tss_per_hour = {
            'base': 50,
            'build': 65,
            'specialty': 75
        }
        
        # Weekly progression within 4-week mesocycle
        progression_multiplier = {
            1: 1.0,
            2: 1.1,
            3: 1.2,
            4: 0.6  # Recovery week
        }
        
        base_tss = hours_per_week * base_tss_per_hour[phase]
        weekly_tss = base_tss * progression_multiplier[week_in_mesocycle]
        
        return round(weekly_tss)
    
    def _get_workout_distribution(self, phase, rides_per_week):
        """Determine workout type distribution for the week"""
        
        if phase == 'base':
            # Base phase: mostly endurance and sweet spot
            distributions = {
                3: ['endurance', 'sweet_spot', 'endurance'],
                4: ['endurance', 'sweet_spot', 'recovery', 'endurance'],
                5: ['endurance', 'sweet_spot', 'tempo', 'recovery', 'endurance'],
                6: ['endurance', 'sweet_spot', 'tempo', 'recovery', 'endurance', 'sweet_spot']
            }
        
        elif phase == 'build':
            # Build phase: threshold and VO2 max work
            distributions = {
                3: ['endurance', 'threshold', 'sweet_spot'],
                4: ['endurance', 'threshold', 'sweet_spot', 'recovery'],
                5: ['endurance', 'threshold', 'vo2max', 'sweet_spot', 'recovery'],
                6: ['endurance', 'threshold', 'vo2max', 'sweet_spot', 'recovery', 'tempo']
            }
        
        elif phase == 'specialty':
            # Specialty phase: race-specific high intensity
            distributions = {
                3: ['endurance', 'vo2max', 'threshold'],
                4: ['endurance', 'vo2max', 'threshold', 'recovery'],
                5: ['endurance', 'vo2max', 'threshold', 'anaerobic', 'recovery'],
                6: ['endurance', 'vo2max', 'threshold', 'anaerobic', 'recovery', 'sweet_spot']
            }
        
        else:
            # Default
            distributions = {
                3: ['endurance', 'sweet_spot', 'endurance'],
                4: ['endurance', 'sweet_spot', 'recovery', 'endurance'],
                5: ['endurance', 'sweet_spot', 'tempo', 'recovery', 'endurance'],
                6: ['endurance', 'sweet_spot', 'tempo', 'recovery', 'endurance', 'sweet_spot']
            }
        
        return distributions.get(rides_per_week, distributions[4])
    
    def _create_workout(self, plan, week_num, phase, workout_type, scheduled_date, target_tss):
        """Create a single workout"""
        
        # Get progression level for this zone
        zone_to_level = {
            'recovery': self.progression_levels.recovery_level,
            'endurance': self.progression_levels.endurance_level,
            'tempo': self.progression_levels.tempo_level,
            'sweet_spot': self.progression_levels.sweet_spot_level,
            'threshold': self.progression_levels.threshold_level,
            'vo2max': self.progression_levels.vo2max_level,
            'anaerobic': self.progression_levels.anaerobic_level
        }
        
        progression_level = zone_to_level.get(workout_type, 3.0)
        
        # Find suitable workouts
        matching_workouts = get_workout_by_criteria(
            zone=workout_type,
            progression_level=progression_level,
            phase=phase
        )
        
        if not matching_workouts:
            return None
        
        # Select workout (prefer closer to target TSS)
        selected = min(matching_workouts, key=lambda w: abs(w['estimated_tss'] - target_tss))
        
        # Create PlannedWorkout
        workout = PlannedWorkout(
            plan_id=plan.id,
            user_id=self.user.id,
            scheduled_date=scheduled_date,
            week_number=week_num,
            phase=phase,
            name=selected['name'],
            description=selected['description'],
            primary_zone=selected['primary_zone'],
            secondary_zone=selected.get('secondary_zone'),
            planned_duration=selected['duration'],
            planned_tss=selected['estimated_tss'],
            intervals=selected['intervals'],
            progression_level=progression_level,
            difficulty_score=selected['difficulty_score'],
            status='scheduled'
        )
        
        return workout
    
    def _create_test_workout(self, plan, week_num, phase, scheduled_date):
        """Create an FTP test workout"""
        
        # Determine test type based on user preference or experience
        test_type = self.user.preferred_test_type or '20_minute'
        if self.user.training_experience == 'beginner':
            test_type = 'ramp'
        elif self.user.training_experience == 'intermediate':
            test_type = '8_minute'
        
        test_workout = get_test_workout(test_type)
        if not test_workout:
            return None
        
        workout = PlannedWorkout(
            plan_id=plan.id,
            user_id=self.user.id,
            scheduled_date=scheduled_date,
            week_number=week_num,
            phase=phase,
            name=test_workout['name'],
            description=test_workout['description'],
            primary_zone=test_workout['primary_zone'],
            planned_duration=test_workout['duration'],
            planned_tss=test_workout['estimated_tss'],
            intervals=test_workout['intervals'],
            progression_level=5.0,
            difficulty_score=test_workout['difficulty_score'],
            status='scheduled'
        )
        
        return workout


def populate_workout_templates():
    """Populate database with workout templates from library"""
    from src.models.training_plan import WorkoutTemplate
    
    for template_data in WORKOUT_TEMPLATES:
        # Check if template already exists
        existing = WorkoutTemplate.query.filter_by(name=template_data['name']).first()
        if existing:
            continue
        
        template = WorkoutTemplate(
            name=template_data['name'],
            short_name=template_data['short_name'],
            description=template_data['description'],
            primary_zone=template_data['primary_zone'],
            secondary_zone=template_data.get('secondary_zone'),
            workout_type=template_data['workout_type'],
            min_progression_level=template_data['min_progression_level'],
            max_progression_level=template_data['max_progression_level'],
            difficulty_score=template_data['difficulty_score'],
            duration=template_data['duration'],
            work_duration=template_data['work_duration'],
            estimated_tss=template_data['estimated_tss'],
            intensity_factor=template_data['intensity_factor'],
            intervals=template_data['intervals'],
            suitable_for_base=template_data['suitable_for_base'],
            suitable_for_build=template_data['suitable_for_build'],
            suitable_for_specialty=template_data['suitable_for_specialty'],
            tags=template_data['tags']
        )
        
        db.session.add(template)
    
    db.session.commit()
    print(f"Added {len(WORKOUT_TEMPLATES)} workout templates to database")

