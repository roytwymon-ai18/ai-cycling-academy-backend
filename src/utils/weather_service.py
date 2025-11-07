"""
Weather service for fetching and managing weather forecasts
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# OpenWeatherMap API configuration
WEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')
WEATHER_API_BASE = 'https://api.openweathermap.org/data/2.5'


def get_weather_forecast(lat: float, lon: float, days: int = 7) -> Optional[List[Dict]]:
    """
    Fetch weather forecast for a location
    
    Args:
        lat: Latitude
        lon: Longitude
        days: Number of days to forecast (default 7)
    
    Returns:
        List of daily weather forecasts or None if error
    """
    if not WEATHER_API_KEY:
        print("Warning: OPENWEATHER_API_KEY not set")
        return None
    
    try:
        # Use 5-day/3-hour forecast (free tier)
        url = f"{WEATHER_API_BASE}/forecast"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': WEATHER_API_KEY,
            'units': 'imperial',  # Fahrenheit
            'cnt': 40  # 5 days * 8 (3-hour intervals)
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Process forecast data into daily summaries
        daily_forecasts = process_forecast_data(data)
        
        return daily_forecasts[:days]
        
    except requests.exceptions.RequestException as e:
        print(f"Weather API error: {e}")
        return None
    except Exception as e:
        print(f"Weather processing error: {e}")
        return None


def process_forecast_data(api_data: Dict) -> List[Dict]:
    """
    Process OpenWeatherMap API data into daily summaries
    
    Args:
        api_data: Raw API response
    
    Returns:
        List of daily weather summaries
    """
    daily_data = {}
    
    for item in api_data.get('list', []):
        # Get date from timestamp
        dt = datetime.fromtimestamp(item['dt'])
        date_key = dt.date()
        
        # Initialize day if not exists
        if date_key not in daily_data:
            daily_data[date_key] = {
                'date': date_key,
                'temps': [],
                'conditions': [],
                'precipitation': [],
                'wind_speeds': [],
                'wind_dirs': [],
                'humidity': []
            }
        
        # Collect data points
        daily_data[date_key]['temps'].append(item['main']['temp'])
        daily_data[date_key]['conditions'].append(item['weather'][0]['main'])
        daily_data[date_key]['wind_speeds'].append(item['wind']['speed'])
        daily_data[date_key]['wind_dirs'].append(item['wind'].get('deg', 0))
        daily_data[date_key]['humidity'].append(item['main']['humidity'])
        
        # Precipitation
        rain = item.get('rain', {}).get('3h', 0)
        snow = item.get('snow', {}).get('3h', 0)
        daily_data[date_key]['precipitation'].append(rain + snow)
    
    # Create daily summaries
    forecasts = []
    for date_key in sorted(daily_data.keys()):
        day = daily_data[date_key]
        
        # Calculate daily values
        temps = day['temps']
        temp_high = int(max(temps))
        temp_low = int(min(temps))
        temp_avg = int(sum(temps) / len(temps))
        
        # Most common condition
        conditions = day['conditions']
        main_condition = max(set(conditions), key=conditions.count)
        
        # Total precipitation
        total_precip = sum(day['precipitation'])
        precip_chance = int((len([p for p in day['precipitation'] if p > 0]) / len(day['precipitation'])) * 100)
        
        # Average wind
        avg_wind = int(sum(day['wind_speeds']) / len(day['wind_speeds']))
        
        # Average wind direction (simplified)
        avg_wind_dir = int(sum(day['wind_dirs']) / len(day['wind_dirs']))
        wind_dir_name = degrees_to_direction(avg_wind_dir)
        
        # Average humidity
        avg_humidity = int(sum(day['humidity']) / len(day['humidity']))
        
        forecasts.append({
            'date': date_key.strftime('%Y-%m-%d'),
            'day_name': date_key.strftime('%A'),
            'temp_high': temp_high,
            'temp_low': temp_low,
            'temp_avg': temp_avg,
            'conditions': main_condition,
            'conditions_emoji': condition_to_emoji(main_condition),
            'precipitation_chance': precip_chance,
            'precipitation_amount': round(total_precip / 25.4, 2),  # mm to inches
            'wind_speed': avg_wind,
            'wind_direction': wind_dir_name,
            'humidity': avg_humidity,
            'is_good_for_outdoor': is_good_riding_weather(
                temp_avg, main_condition, precip_chance, avg_wind
            )
        })
    
    return forecasts


def degrees_to_direction(degrees: int) -> str:
    """Convert wind direction degrees to compass direction"""
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    idx = int((degrees + 22.5) / 45) % 8
    return directions[idx]


def condition_to_emoji(condition: str) -> str:
    """Convert weather condition to emoji"""
    emoji_map = {
        'Clear': '☀️',
        'Clouds': '☁️',
        'Rain': '🌧️',
        'Drizzle': '🌦️',
        'Thunderstorm': '⛈️',
        'Snow': '❄️',
        'Mist': '🌫️',
        'Fog': '🌫️',
        'Haze': '🌫️'
    }
    return emoji_map.get(condition, '🌤️')


def is_good_riding_weather(temp: int, condition: str, precip_chance: int, wind: int) -> bool:
    """
    Determine if weather is good for outdoor cycling
    
    Args:
        temp: Temperature in Fahrenheit
        condition: Weather condition
        precip_chance: Precipitation chance (%)
        wind: Wind speed (mph)
    
    Returns:
        bool: True if good riding weather
    """
    # Temperature check (40-85°F ideal)
    if temp < 35 or temp > 90:
        return False
    
    # Precipitation check
    if precip_chance > 60:
        return False
    
    # Dangerous conditions
    if condition in ['Thunderstorm', 'Snow']:
        return False
    
    # High wind check
    if wind > 25:
        return False
    
    return True


def get_weather_summary_text(forecasts: List[Dict]) -> str:
    """
    Generate human-readable weather summary for Coach Manee
    
    Args:
        forecasts: List of daily forecasts
    
    Returns:
        str: Formatted weather summary
    """
    if not forecasts:
        return "Weather forecast unavailable."
    
    summary = "7-Day Weather Forecast:\n"
    
    for forecast in forecasts:
        date = forecast['date']
        day = forecast['day_name']
        emoji = forecast['conditions_emoji']
        temp_high = forecast['temp_high']
        temp_low = forecast['temp_low']
        condition = forecast['conditions']
        wind = forecast['wind_speed']
        wind_dir = forecast['wind_direction']
        precip = forecast['precipitation_chance']
        
        # Build day summary
        summary += f"\n{day} ({date}) {emoji}\n"
        summary += f"  Temp: {temp_low}-{temp_high}°F, {condition}\n"
        summary += f"  Wind: {wind}mph {wind_dir}"
        
        if precip > 30:
            summary += f", {precip}% chance rain"
        
        # Riding assessment
        if forecast['is_good_for_outdoor']:
            summary += " ✅ Good for outdoor riding"
        else:
            if precip > 60:
                summary += " 🏠 Consider indoor (rain likely)"
            elif temp_high > 90:
                summary += " 🔥 Hot - ride early or indoor"
            elif temp_low < 40:
                summary += " 🥶 Cold - layer up or indoor"
            elif wind > 20:
                summary += " 💨 Windy - sheltered route or indoor"
        
        summary += "\n"
    
    return summary


def get_weather_coaching_insights(forecasts: List[Dict], workouts: List[Dict]) -> List[str]:
    """
    Generate weather-based coaching insights for workouts
    
    Args:
        forecasts: List of daily forecasts
        workouts: List of scheduled workouts with dates
    
    Returns:
        List of coaching insights/recommendations
    """
    insights = []
    
    # Create forecast lookup by date
    forecast_map = {f['date']: f for f in forecasts}
    
    for workout in workouts:
        workout_date = workout.get('date')
        if not workout_date or workout_date not in forecast_map:
            continue
        
        forecast = forecast_map[workout_date]
        workout_name = workout.get('name', 'Workout')
        workout_type = workout.get('type', 'unknown')
        
        # Rain check
        if forecast['precipitation_chance'] > 70:
            if 'interval' in workout_type.lower() or 'vo2' in workout_type.lower():
                insights.append(
                    f"⚠️ {workout['date']}: {workout_name} - Rain likely ({forecast['precipitation_chance']}%). "
                    f"Consider indoor trainer for better control during intervals."
                )
            else:
                insights.append(
                    f"🌧️ {workout['date']}: {workout_name} - Rain likely ({forecast['precipitation_chance']}%). "
                    f"Indoor alternative or reschedule?"
                )
        
        # Heat check
        if forecast['temp_high'] > 90:
            insights.append(
                f"🔥 {workout['date']}: {workout_name} - Hot day ({forecast['temp_high']}°F). "
                f"Consider early morning ride or reduce intensity by 5-10%."
            )
        
        # Wind check
        if forecast['wind_speed'] > 20 and 'long' in workout_type.lower():
            insights.append(
                f"💨 {workout['date']}: {workout_name} - Windy ({forecast['wind_speed']}mph {forecast['wind_direction']}). "
                f"Plan route with tailwind on return or add 10-15% to TSS estimate."
            )
        
        # Perfect weather highlight
        if forecast['is_good_for_outdoor'] and forecast['temp_avg'] >= 65 and forecast['temp_avg'] <= 75:
            if 'long' in workout_type.lower() or 'endurance' in workout_type.lower():
                insights.append(
                    f"✨ {workout['date']}: {workout_name} - Perfect conditions ({forecast['temp_avg']}°F, {forecast['conditions']})! "
                    f"Great day for this ride."
                )
    
    return insights


def get_location_from_city(city: str) -> Optional[tuple]:
    """
    Get lat/lon coordinates from city name using OpenWeatherMap Geocoding API
    
    Args:
        city: City name (e.g., "Austin, TX" or "London, UK")
    
    Returns:
        tuple: (lat, lon) or None if not found
    """
    if not WEATHER_API_KEY:
        return None
    
    try:
        url = "http://api.openweathermap.org/geo/1.0/direct"
        params = {
            'q': city,
            'limit': 1,
            'appid': WEATHER_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data and len(data) > 0:
            return (data[0]['lat'], data[0]['lon'])
        
        return None
        
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None
