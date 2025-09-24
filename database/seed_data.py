import sqlite3
from database.models import get_db_connection

def seed_data():
    """Seed initial data into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Sample skills data
    skills_data = [
        ('Python', 'programming_languages', 0.8),
        ('JavaScript', 'programming_languages', 0.7),
        ('SQL', 'databases', 0.6),
        ('Machine Learning', 'data_science', 0.9),
        ('Communication', 'soft_skills', 0.5),
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO skills (skill_name, category, importance_score)
        VALUES (?, ?, ?)
    ''', skills_data)

    # Sample careers data
    careers_data = [
        ('Data Scientist', 'Technology', 'Analyze data to extract insights', 60000, 120000, 0.15, 'Bachelor', '2-4 years', 1, 0.85),
        ('Software Engineer', 'Technology', 'Develop software applications', 65000, 130000, 0.12, 'Bachelor', '1-3 years', 1, 0.8),
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO careers 
        (career_title, industry, description, avg_salary_min, avg_salary_max, growth_rate, 
         education_required, experience_required, remote_friendly, demand_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', careers_data)

    conn.commit()
    conn.close()
    print("Database seeded successfully.")

if __name__ == '__main__':
    seed_data()