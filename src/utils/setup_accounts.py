#!/usr/bin/env python3
"""
Setup script for AI Cycling Academy dual account system
Creates demo account with example data and fresh user account
"""

import json
import os
import sys
from datetime import datetime, timedelta
import sqlite3
from werkzeug.security import generate_password_hash

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_database():
    """Initialize the database with proper schema"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'app.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            ftp INTEGER DEFAULT 250,
            weight REAL DEFAULT 70.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            account_type TEXT DEFAULT 'user'
        )
    ''')
    
    # Create rides table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            duration INTEGER NOT NULL,
            distance REAL NOT NULL,
            avg_power INTEGER,
            max_power INTEGER,
            avg_heart_rate INTEGER,
            max_heart_rate INTEGER,
            elevation_gain REAL,
            avg_speed REAL,
            max_speed REAL,
            calories INTEGER,
            tss REAL,
            if_score REAL,
            ride_type TEXT DEFAULT 'outdoor',
            filename TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create coaching_sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coaching_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            session_type TEXT DEFAULT 'chat',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    return conn

def create_demo_account(conn):
    """Create demo account with example data"""
    cursor = conn.cursor()
    
    # Create demo user
    demo_password = generate_password_hash('demo123')
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (username, email, password_hash, full_name, ftp, weight, account_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('demo', 'demo@aicyclistacademy.com', demo_password, 'Demo User', 285, 72.5, 'demo'))
    
    demo_user_id = cursor.lastrowid or 1
    
    # Load converted ride data
    try:
        with open('/home/ubuntu/user01_rides.json', 'r') as f:
            rides_data = json.load(f)
        
        # Insert demo rides
        for ride in rides_data:
            # Calculate metrics from available data
            power_values = ride.get('power_values', [])
            hr_values = ride.get('heart_rate_values', [])
            
            avg_power = int(sum(power_values) / len(power_values)) if power_values else None
            max_power = max(power_values) if power_values else None
            avg_hr = int(sum(hr_values) / len(hr_values)) if hr_values else None
            max_hr = max(hr_values) if hr_values else None
            
            # Calculate training metrics
            if avg_power and avg_power > 0:
                ftp = 285  # Demo user FTP
                if_score = avg_power / ftp if ftp > 0 else 0
                tss = (ride['duration'] / 3600) * (avg_power / ftp) ** 2 * 100 if ftp > 0 else 0
            else:
                if_score = 0
                tss = 0
            
            # Estimate calories
            calories = int(ride['duration'] / 60 * 12)  # Rough estimate
            
            cursor.execute('''
                INSERT INTO rides 
                (user_id, date, duration, distance, avg_power, max_power, 
                 avg_heart_rate, max_heart_rate, elevation_gain, avg_speed, 
                 max_speed, calories, tss, if_score, ride_type, filename)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                demo_user_id,
                ride['date'],
                ride['duration'],
                ride['distance'],
                avg_power,
                max_power,
                avg_hr,
                max_hr,
                ride['elevation_gain'],
                ride.get('avg_speed', 25.0),  # Use actual field or default
                ride.get('avg_speed', 25.0) * 1.5 if ride.get('avg_speed') else 37.5,  # Estimate max speed
                calories,
                tss,
                if_score,
                'outdoor',
                f"demo_{ride['name'].replace(' ', '_')}.fit"
            ))
        
        print(f"✅ Created demo account with {len(rides_data)} rides")
        
    except FileNotFoundError:
        print("⚠️  No ride data found, creating demo account without rides")
    
    # Add sample coaching sessions for demo
    sample_sessions = [
        {
            "message": "Analyze my last ride performance",
            "response": "Great ride! Your average power of 265W shows strong endurance. Your power curve indicates good sustained efforts, but we could work on your sprint power. Consider adding some 15-second max efforts to your training."
        },
        {
            "message": "What should I focus on this week?",
            "response": "Based on your recent rides, I recommend focusing on threshold intervals. Your FTP has improved to 285W, so let's consolidate that with 2x20min efforts at 95% FTP. Also include one recovery ride and one tempo session."
        },
        {
            "message": "How's my training load?",
            "response": "Your 7-day TSS is 420, which is in a good range for your fitness level. Your CTL is trending upward nicely. Just watch your TSB - it's getting low, so consider a recovery week soon."
        }
    ]
    
    for session in sample_sessions:
        cursor.execute('''
            INSERT INTO coaching_sessions (user_id, message, response, session_type)
            VALUES (?, ?, ?, ?)
        ''', (demo_user_id, session['message'], session['response'], 'chat'))
    
    conn.commit()
    return demo_user_id

def create_user_account(conn):
    """Create fresh user account"""
    cursor = conn.cursor()
    
    # Create user account
    user_password = generate_password_hash('user123')
    cursor.execute('''
        INSERT OR REPLACE INTO users 
        (username, email, password_hash, full_name, ftp, weight, account_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('user', 'user@aicyclistacademy.com', user_password, 'New User', 250, 70.0, 'user'))
    
    user_id = cursor.lastrowid or 2
    
    # Add welcome coaching session
    cursor.execute('''
        INSERT INTO coaching_sessions (user_id, message, response, session_type)
        VALUES (?, ?, ?, ?)
    ''', (
        user_id, 
        "Welcome to AI Cycling Academy!", 
        "Welcome! I'm your AI cycling coach. Upload your first ride to get started with personalized analysis and training recommendations. I can help you improve your performance, create training plans, and answer any cycling questions you have.",
        'welcome'
    ))
    
    conn.commit()
    print("✅ Created fresh user account")
    return user_id

def main():
    """Main setup function"""
    print("🚀 Setting up AI Cycling Academy dual account system...")
    
    # Setup database
    conn = setup_database()
    print("✅ Database schema created")
    
    # Create accounts
    demo_id = create_demo_account(conn)
    user_id = create_user_account(conn)
    
    # Create account info file
    account_info = {
        "demo_account": {
            "id": demo_id,
            "username": "demo",
            "email": "demo@aicyclistacademy.com",
            "password": "demo123",
            "description": "Demo account with example ride data and coaching history"
        },
        "user_account": {
            "id": user_id,
            "username": "user",
            "email": "user@aicyclistacademy.com", 
            "password": "user123",
            "description": "Fresh user account for actual use"
        }
    }
    
    with open('/home/ubuntu/account_info.json', 'w') as f:
        json.dump(account_info, f, indent=2)
    
    conn.close()
    
    print("\n🎉 Dual account system setup complete!")
    print("\n📋 Account Details:")
    print("Demo Account (with example data):")
    print("  Username: demo")
    print("  Email: demo@aicyclistacademy.com")
    print("  Password: demo123")
    print("\nUser Account (fresh for actual use):")
    print("  Username: user")
    print("  Email: user@aicyclistacademy.com")
    print("  Password: user123")
    print("\n💾 Account info saved to: /home/ubuntu/account_info.json")

if __name__ == "__main__":
    main()

