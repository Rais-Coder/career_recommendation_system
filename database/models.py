import sqlite3
import json
from datetime import datetime

DATABASE_NAME = 'career_data.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            age INTEGER,
            education_level TEXT,
            current_field TEXT,
            years_experience INTEGER,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT UNIQUE NOT NULL,
            category TEXT,
            importance_score REAL DEFAULT 0.5
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            proficiency_level INTEGER CHECK(proficiency_level BETWEEN 1 AND 5),
            source TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (skill_id) REFERENCES skills (id),
            UNIQUE(user_id, skill_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS careers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            career_title TEXT NOT NULL,
            industry TEXT,
            description TEXT,
            avg_salary_min INTEGER,
            avg_salary_max INTEGER,
            growth_rate REAL,
            education_required TEXT,
            experience_required TEXT,
            remote_friendly BOOLEAN DEFAULT 0,
            demand_score REAL DEFAULT 0.5
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS career_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            career_id INTEGER NOT NULL,
            skill_id INTEGER NOT NULL,
            importance_level INTEGER CHECK(importance_level BETWEEN 1 AND 5),
            required_proficiency INTEGER CHECK(required_proficiency BETWEEN 1 AND 5),
            FOREIGN KEY (career_id) REFERENCES careers (id),
            FOREIGN KEY (skill_id) REFERENCES skills (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            personality_type TEXT,
            interests TEXT,
            work_style_preferences TEXT,
            career_goals TEXT,
            risk_tolerance INTEGER CHECK(risk_tolerance BETWEEN 1 AND 5),
            work_life_balance_priority INTEGER CHECK(work_life_balance_priority BETWEEN 1 AND 5),
            salary_importance INTEGER CHECK(salary_importance BETWEEN 1 AND 5),
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS education_background (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            degree_type TEXT,
            field_of_study TEXT,
            institution TEXT,
            graduation_year INTEGER,
            gpa REAL,
            relevant_courses TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_experience (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_title TEXT,
            company TEXT,
            industry TEXT,
            duration_months INTEGER,
            responsibilities TEXT,
            achievements TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            career_id INTEGER NOT NULL,
            match_score REAL NOT NULL,
            reasoning TEXT,
            skill_gaps TEXT,
            learning_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (career_id) REFERENCES careers (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id INTEGER NOT NULL,
            trend_score REAL,
            demand_level TEXT,
            salary_trend REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (skill_id) REFERENCES skills (id)
        )
    ''')
    
    conn.commit()
    
    # Insert sample data if tables are empty
    cursor.execute('SELECT COUNT(*) FROM skills')
    if cursor.fetchone()[0] == 0:
        populate_sample_data(cursor)
        conn.commit()
    
    conn.close()

def populate_sample_data(cursor):
    # Sample skills data
    skills_data = [
        ('Python', 'Technical', 0.9),
        ('JavaScript', 'Technical', 0.85),
        ('React', 'Technical', 0.8),
        ('Machine Learning', 'Technical', 0.9),
        ('Data Analysis', 'Technical', 0.85),
        ('SQL', 'Technical', 0.8),
        ('Communication', 'Soft', 0.9),
        ('Leadership', 'Soft', 0.85),
        ('Problem Solving', 'Soft', 0.9),
        ('Project Management', 'Domain', 0.8),
        ('Java', 'Technical', 0.8),
        ('C++', 'Technical', 0.75),
        ('HTML/CSS', 'Technical', 0.7),
        ('AWS', 'Technical', 0.85),
        ('Docker', 'Technical', 0.8),
        ('Git', 'Technical', 0.8),
        ('Agile', 'Domain', 0.75),
        ('UI/UX Design', 'Technical', 0.8),
        ('Database Design', 'Technical', 0.8),
        ('Statistics', 'Technical', 0.8)
    ]
    
    cursor.executemany('INSERT INTO skills (skill_name, category, importance_score) VALUES (?, ?, ?)', skills_data)
    
    # Sample careers data
    careers_data = [
        ('Data Scientist', 'Technology', 'Analyze complex data to help organizations make informed decisions', 80000, 150000, 0.22, 'Bachelor', '2-4 years', 1, 0.9),
        ('Software Engineer', 'Technology', 'Design, develop, and maintain software applications', 70000, 140000, 0.15, 'Bachelor', '1-3 years', 1, 0.85),
        ('Product Manager', 'Business', 'Lead product development and strategy', 90000, 160000, 0.12, 'Bachelor', '3-5 years', 1, 0.8),
        ('UX Designer', 'Design', 'Create user-centered design solutions', 60000, 120000, 0.18, 'Bachelor', '2-4 years', 1, 0.75),
        ('DevOps Engineer', 'Technology', 'Manage deployment and infrastructure automation', 75000, 130000, 0.20, 'Bachelor', '3-5 years', 1, 0.85),
        ('Data Analyst', 'Technology', 'Collect, process and analyze data to provide insights', 55000, 100000, 0.14, 'Bachelor', '1-3 years', 1, 0.8),
        ('Machine Learning Engineer', 'Technology', 'Build and deploy ML models and systems', 90000, 160000, 0.25, 'Bachelor', '3-5 years', 1, 0.9),
        ('Frontend Developer', 'Technology', 'Build user interfaces for web applications', 60000, 110000, 0.12, 'Bachelor', '1-3 years', 1, 0.8),
        ('Backend Developer', 'Technology', 'Build server-side applications and APIs', 70000, 130000, 0.15, 'Bachelor', '2-4 years', 1, 0.8),
        ('Full Stack Developer', 'Technology', 'Work on both frontend and backend development', 65000, 125000, 0.13, 'Bachelor', '2-4 years', 1, 0.82)
    ]
    
    cursor.executemany('''INSERT INTO careers 
        (career_title, industry, description, avg_salary_min, avg_salary_max, growth_rate, 
         education_required, experience_required, remote_friendly, demand_score) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', careers_data)
    
    # Sample career-skills relationships
    career_skills_data = [
        # Data Scientist (id=1)
        (1, 1, 5, 4),  # Python
        (1, 5, 5, 4),  # Data Analysis
        (1, 4, 5, 4),  # Machine Learning
        (1, 6, 4, 3),  # SQL
        (1, 20, 4, 3), # Statistics
        
        # Software Engineer (id=2)
        (2, 1, 4, 3),  # Python
        (2, 2, 4, 3),  # JavaScript
        (2, 11, 4, 3), # Java
        (2, 16, 3, 2), # Git
        (2, 9, 4, 3),  # Problem Solving
        
        # Product Manager (id=3)
        (3, 7, 5, 4),  # Communication
        (3, 8, 5, 4),  # Leadership
        (3, 10, 4, 3), # Project Management
        (3, 17, 3, 2), # Agile
        
        # UX Designer (id=4)
        (4, 18, 5, 4), # UI/UX Design
        (4, 13, 3, 2), # HTML/CSS
        (4, 7, 4, 3),  # Communication
        (4, 9, 4, 3),  # Problem Solving
        
        # DevOps Engineer (id=5)
        (5, 14, 5, 4), # AWS
        (5, 15, 4, 3), # Docker
        (5, 16, 4, 3), # Git
        (5, 1, 3, 2),  # Python
    ]
    
    cursor.executemany('''INSERT INTO career_skills 
        (career_id, skill_id, importance_level, required_proficiency) 
        VALUES (?, ?, ?, ?)''', career_skills_data)