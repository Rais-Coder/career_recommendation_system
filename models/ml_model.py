import numpy as np
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import json
import pandas as pd
from database.models import get_db_connection

class CareerRecommendationModel:
    def __init__(self):
        self.skill_vectorizer = TfidfVectorizer()
        self.scaler = StandardScaler()
        self.career_clusters = None
        self.career_profiles = None
        
    def load_data(self):
        """Load career and user data from database"""
        conn = get_db_connection()
        
        # Load careers with their required skills
        careers_query = '''
            SELECT c.id, c.career_title, c.industry, c.description,
                   c.avg_salary_min, c.avg_salary_max, c.growth_rate,
                   c.demand_score, GROUP_CONCAT(s.skill_name) as skills
            FROM careers c
            LEFT JOIN career_skills cs ON c.id = cs.career_id
            LEFT JOIN skills s ON cs.skill_id = s.id
            GROUP BY c.id
        '''
        careers_df = pd.read_sql_query(careers_query, conn)
        
        # Load user skills
        users_query = '''
            SELECT u.id as user_id, u.name, u.education_level,
                   u.years_experience, GROUP_CONCAT(s.skill_name) as skills
            FROM users u
            LEFT JOIN user_skills us ON u.id = us.user_id
            LEFT JOIN skills s ON us.skill_id = s.id
            GROUP BY u.id
        '''
        users_df = pd.read_sql_query(users_query, conn)
        
        conn.close()
        return careers_df, users_df
    
    def create_skill_vectors(self, text_data):
        """Create TF-IDF vectors for skills"""
        skill_texts = text_data.fillna('').tolist()
        return self.skill_vectorizer.fit_transform(skill_texts)
    
    def calculate_skill_match_score(self, user_skills, career_skills):
        """Calculate skill match score between user and career"""
        if not user_skills or not career_skills:
            return 0.0
        
        user_skill_set = set(user_skills.split(',')) if user_skills else set()
        career_skill_set = set(career_skills.split(',')) if career_skills else set()
        
        if not career_skill_set:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = user_skill_set.intersection(career_skill_set)
        union = user_skill_set.union(career_skill_set)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def calculate_education_match(self, user_education, required_education):
        """Calculate education level compatibility"""
        education_hierarchy = {
            'High School': 1,
            'Diploma': 2,
            'Associate': 3,
            'Bachelor': 4,
            'Master': 5,
            'PhD': 6
        }
        
        user_level = education_hierarchy.get(user_education, 0)
        required_level = education_hierarchy.get(required_education, 0)
        
        if user_level >= required_level:
            return 1.0
        elif user_level == required_level - 1:
            return 0.8
        else:
            return 0.5
    
    def calculate_experience_match(self, user_experience, required_experience):
        """Calculate experience compatibility"""
        if not required_experience:
            return 1.0
        
        # Parse required experience (e.g., "2-4 years")
        if '-' in required_experience:
            try:
                min_exp, max_exp = map(int, required_experience.split('-')[0:2])
                min_exp = int(min_exp)
                max_exp = int(max_exp.split()[0])
                
                if user_experience >= min_exp:
                    return 1.0
                elif user_experience >= min_exp - 1:
                    return 0.8
                else:
                    return 0.5
            except:
                return 0.7
        
        return 0.7
    
    def predict_career_match(self, user_id):
        """Predict career matches for a specific user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user profile
        cursor.execute('''
            SELECT u.*, GROUP_CONCAT(s.skill_name) as skills,
                   GROUP_CONCAT(us.proficiency_level) as skill_levels
            FROM users u
            LEFT JOIN user_skills us ON u.id = us.user_id
            LEFT JOIN skills s ON us.skill_id = s.id
            WHERE u.id = ?
            GROUP BY u.id
        ''', (user_id,))
        
        user_data = cursor.fetchone()
        if not user_data:
            return []
        
        # Get user assessment data
        cursor.execute('''
            SELECT * FROM assessments WHERE user_id = ? 
            ORDER BY completed_at DESC LIMIT 1
        ''', (user_id,))
        assessment = cursor.fetchone()
        
        # Get all careers
        cursor.execute('''
            SELECT c.*, GROUP_CONCAT(s.skill_name) as required_skills
            FROM careers c
            LEFT JOIN career_skills cs ON c.id = cs.career_id
            LEFT JOIN skills s ON cs.skill_id = s.id
            GROUP BY c.id
        ''')
        careers = cursor.fetchall()
        
        conn.close()
        
        recommendations = []
        
        for career in careers:
            # Calculate different matching scores
            skill_score = self.calculate_skill_match_score(
                user_data['skills'], career['required_skills']
            )
            
            education_score = self.calculate_education_match(
                user_data['education_level'], career['education_required']
            )
            
            experience_score = self.calculate_experience_match(
                user_data['years_experience'] or 0, career['experience_required']
            )
            
            # Interest matching (if assessment available)
            interest_score = 0.7  # Default
            if assessment and assessment['interests']:
                try:
                    interests = json.loads(assessment['interests'])
                    # Simple keyword matching with career description
                    if career['description']:
                        desc_words = set(career['description'].lower().split())
                        interest_words = set([i.lower() for i in interests])
                        if desc_words.intersection(interest_words):
                            interest_score = 0.9
                except:
                    pass
            
            # Calculate overall match score
            overall_score = (
                skill_score * 0.4 +
                education_score * 0.2 +
                experience_score * 0.2 +
                interest_score * 0.1 +
                career['demand_score'] * 0.1
            )
            
            # Identify skill gaps
            user_skills = set(user_data['skills'].split(',')) if user_data['skills'] else set()
            required_skills = set(career['required_skills'].split(',')) if career['required_skills'] else set()
            skill_gaps = list(required_skills - user_skills)
            
            recommendations.append({
                'career_id': career['id'],
                'career_title': career['career_title'],
                'industry': career['industry'],
                'description': career['description'],
                'match_score': round(overall_score, 3),
                'skill_score': round(skill_score, 3),
                'education_score': round(education_score, 3),
                'experience_score': round(experience_score, 3),
                'interest_score': round(interest_score, 3),
                'skill_gaps': skill_gaps,
                'salary_range': f"${career['avg_salary_min']:,} - ${career['avg_salary_max']:,}",
                'growth_rate': career['growth_rate'],
                'demand_score': career['demand_score']
            })
        
        # Sort by match score
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        return recommendations[:10]  # Return top 10 matches
    
    def generate_learning_path(self, user_id, career_id):
        """Generate learning path for a specific career"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user's current skills
        cursor.execute('''
            SELECT s.skill_name, us.proficiency_level
            FROM user_skills us
            JOIN skills s ON us.skill_id = s.id
            WHERE us.user_id = ?
        ''', (user_id,))
        user_skills = {row['skill_name']: row['proficiency_level'] for row in cursor.fetchall()}
        
        # Get required skills for career
        cursor.execute('''
            SELECT s.skill_name, cs.required_proficiency, cs.importance_level
            FROM career_skills cs
            JOIN skills s ON cs.skill_id = s.id
            WHERE cs.career_id = ?
            ORDER BY cs.importance_level DESC
        ''', (career_id,))
        required_skills = cursor.fetchall()
        
        conn.close()
        
        learning_path = []
        
        for skill_data in required_skills:
            skill_name = skill_data['skill_name']
            required_level = skill_data['required_proficiency']
            importance = skill_data['importance_level']
            current_level = user_skills.get(skill_name, 0)
            
            if current_level < required_level:
                gap = required_level - current_level
                priority = 'High' if importance >= 4 else 'Medium' if importance >= 3 else 'Low'
                
                learning_path.append({
                    'skill': skill_name,
                    'current_level': current_level,
                    'required_level': required_level,
                    'gap': gap,
                    'priority': priority,
                    'recommended_resources': self.get_learning_resources(skill_name, gap)
                })
        
        return learning_path
    
    def get_learning_resources(self, skill_name, gap_level):
        """Get recommended learning resources for a skill"""
        resources_map = {
            'Python': {
                1: ['Python.org Tutorial', 'Codecademy Python'],
                2: ['Python Crash Course Book', 'Real Python'],
                3: ['Advanced Python Features', 'Python Design Patterns']
            },
            'JavaScript': {
                1: ['MDN JavaScript Guide', 'FreeCodeCamp'],
                2: ['JavaScript: The Good Parts', 'ES6 Features'],
                3: ['Advanced JavaScript Concepts', 'Node.js Development']
            },
            'Machine Learning': {
                1: ['Coursera ML Course', 'Scikit-learn Documentation'],
                2: ['Hands-On Machine Learning Book', 'Kaggle Courses'],
                3: ['Deep Learning Specialization', 'TensorFlow Certification']
            },
            'Data Analysis': {
                1: ['Pandas Documentation', 'Data Analysis with Python'],
                2: ['Advanced Pandas Techniques', 'Statistical Analysis'],
                3: ['Time Series Analysis', 'Advanced Visualization']
            }
        }
        
        skill_resources = resources_map.get(skill_name, {
            1: [f'Introduction to {skill_name}'],
            2: [f'Intermediate {skill_name}'],
            3: [f'Advanced {skill_name}']
        })
        
        return skill_resources.get(min(gap_level, 3), [f'Learn {skill_name}'])
    
    def update_market_trends(self):
        """Update market trends for skills (placeholder for real market data)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all skills
        cursor.execute('SELECT id, skill_name FROM skills')
        skills = cursor.fetchall()
        
        # Sample trend data (in real implementation, this would come from job market APIs)
        trending_skills = {
            'Python': {'trend': 0.8, 'demand': 'High', 'salary_trend': 0.15},
            'JavaScript': {'trend': 0.6, 'demand': 'High', 'salary_trend': 0.10},
            'Machine Learning': {'trend': 0.9, 'demand': 'High', 'salary_trend': 0.20},
            'React': {'trend': 0.7, 'demand': 'High', 'salary_trend': 0.12},
            'AWS': {'trend': 0.8, 'demand': 'High', 'salary_trend': 0.18}
        }
        
        for skill in skills:
            skill_name = skill['skill_name']
            trend_data = trending_skills.get(skill_name, {
                'trend': 0.5, 'demand': 'Medium', 'salary_trend': 0.05
            })
            
            cursor.execute('''
                INSERT OR REPLACE INTO market_trends 
                (skill_id, trend_score, demand_level, salary_trend, updated_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            ''', (skill['id'], trend_data['trend'], 
                  trend_data['demand'], trend_data['salary_trend']))
        
        conn.commit()
        conn.close()