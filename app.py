from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import json
from models.ml_model import CareerRecommendationModel
from models.recommendation_engine import RecommendationEngine
from utils.resume_parser import ResumeParser
from utils.skill_extractor import SkillExtractor
from database.models import init_db, get_db_connection

app = Flask(__name__)

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

init_db()
recommendation_engine = RecommendationEngine()

# Create placeholder classes for missing modules
class ResumeParser:
    def parse_resume(self, file_path):
        return {'text': 'Sample resume text'}

class SkillExtractor:
    def extract_skills(self, text):
        return {'Python': 0.8, 'JavaScript': 0.7, 'SQL': 0.6}

resume_parser = ResumeParser()
skill_extractor = SkillExtractor()
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        # Support both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (name, email, age, education_level, current_field, years_experience, location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['full_name'] if 'full_name' in data else data.get('name'),
            data['email'],
            data.get('age'),
            data.get('education_level') or data.get('education'),
            data.get('current_field'),
            data.get('years_experience'),
            data.get('location')
        ))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        session['user_id'] = user_id
        session['user_name'] = data['full_name'] if 'full_name' in data else data.get('name')

        # If AJAX, return JSON
        if request.is_json:
            return jsonify({'success': True, 'user_id': user_id})
        else:
            return redirect(url_for('assessment'))
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)})
        flash(f'Registration failed: {str(e)}')
        return redirect(url_for('index'))

@app.route('/assessment')
def assessment():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('assessment.html')

@app.route('/submit_assessment', methods=['POST'])
def submit_assessment():
    try:
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Not logged in'})
            return redirect(url_for('index'))

        user_id = session['user_id']

        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO assessments (user_id, interests, work_style_preferences,
                                     career_goals, risk_tolerance, work_life_balance_priority,
                                     salary_importance, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            json.dumps(data.get('interests', [])),
            json.dumps({
                'team_preference': data.get('teamwork_preference') or data.get('team_preference'),
                'leadership_preference': data.get('leadership_preference'),
                'structure_preference': data.get('structure_preference')
            }),
            data.get('career_goals'),
            data.get('risk_tolerance'),
            data.get('work_life_balance'),
            data.get('salary_importance'),
            datetime.now()
        ))
        conn.commit()
        conn.close()

        if request.is_json:
            return jsonify({'success': True})
        else:
            return redirect(url_for('upload_resume'))
    except Exception as e:
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)})
        flash(f'Assessment submission failed: {str(e)}')
        return redirect(url_for('assessment'))

@app.route('/upload_resume')
def upload_resume():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('upload_resume.html')

@app.route('/process_resume', methods=['POST'])
def process_resume():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'User not logged in'})
        # Accept any file field
        if not request.files:
            return jsonify({'success': False, 'error': 'No file part in the request'})
        # Get the first file in the request
        file = next(iter(request.files.values()))
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            resume_data = resume_parser.parse_resume(file_path)
            extracted_skills = skill_extractor.extract_skills(resume_data['text'])
            user_id = session['user_id']
            conn = get_db_connection()
            cursor = conn.cursor()
            for skill_name, confidence in extracted_skills.items():
                cursor.execute('SELECT id FROM skills WHERE skill_name = ?', (skill_name,))
                skill_row = cursor.fetchone()
                if skill_row:
                    skill_id = skill_row[0]
                else:
                    cursor.execute('INSERT INTO skills (skill_name, category, importance_score) VALUES (?, ?, ?)',
                                   (skill_name, 'Technical', 0.7))
                    skill_id = cursor.lastrowid
                proficiency_level = min(5, max(1, int(confidence * 5)))
                cursor.execute('''
                    INSERT OR REPLACE INTO user_skills (user_id, skill_id, proficiency_level, source)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, skill_id, proficiency_level, 'Resume'))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))  # or wherever you want to go next
        else:
            flash('Invalid file format')
            return redirect(url_for('upload_resume'))
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_recommendations')
def get_recommendations():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    try:
        user_id = session['user_id']
        recommendations = recommendation_engine.generate_recommendations(user_id)
        return render_template('recommendations.html', recommendations=recommendations)
    except Exception as e:
        flash(f'Error generating recommendations: {str(e)}')
        return render_template('recommendations.html', recommendations=[])

@app.route('/api/career_details/<int:career_id>')
def career_details(career_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, GROUP_CONCAT(s.skill_name) as required_skills
            FROM careers c
            LEFT JOIN career_skills cs ON c.id = cs.career_id
            LEFT JOIN skills s ON cs.skill_id = s.id
            WHERE c.id = ?
            GROUP BY c.id
        ''', (career_id,))

        career = cursor.fetchone()
        conn.close()
        if career:
            career_dict = dict(career)
            career_dict['required_skills'] = career_dict['required_skills'].split(',') if career_dict['required_skills'] else []
            return jsonify(career_dict)
        else:
            return jsonify({'error': 'Career not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    try:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = dict(cursor.fetchone())
        cursor.execute('''
            SELECT s.skill_name, us.proficiency_level, s.category
            FROM user_skills us
            JOIN skills s ON us.skill_id = s.id
            WHERE us.user_id = ?
            ORDER BY us.proficiency_level DESC
        ''', (user_id,))
        skills = [dict(row) for row in cursor.fetchall()]
        cursor.execute('''
            SELECT r.*, c.career_title, c.industry, c.avg_salary_min, c.avg_salary_max
            FROM recommendations r
            JOIN careers c ON r.career_id = c.id
            WHERE r.user_id = ?
            ORDER BY r.match_score DESC
            LIMIT 5
        ''', (user_id,))
        recent_recommendations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return render_template('dashboard.html', user=user, skills=skills, recommendations=recent_recommendations)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}')
        return render_template('dashboard.html', user={}, skills=[], recommendations=[])

@app.route('/api/user_data', methods=['GET'])
def get_user_data():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'}), 401
    user_id = session['user_id']
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = dict(cursor.fetchone())
        cursor.execute('''
            SELECT s.skill_name, us.proficiency_level, s.category
            FROM user_skills us
            JOIN skills s ON us.skill_id = s.id
            WHERE us.user_id = ?
            ORDER BY us.proficiency_level DESC
        ''', (user_id,))
        skills = [dict(row) for row in cursor.fetchall()]
        cursor.execute('''
            SELECT r.*, c.career_title, c.industry, c.avg_salary_min, c.avg_salary_max
            FROM recommendations r
            JOIN careers c ON r.career_id = c.id
            WHERE r.user_id = ?
            ORDER BY r.match_score DESC
            LIMIT 5
        ''', (user_id,))
        recent_recommendations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({
            'success': True,
            'user': user,
            'skills': skills,
            'recommendations': recent_recommendations
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/skills_autocomplete')
def skills_autocomplete():
    try:
        query = request.args.get('q', '').lower()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT skill_name FROM skills
            WHERE LOWER(skill_name) LIKE ?
            ORDER BY importance_score DESC
            LIMIT 10
        ''', (f'%{query}%',))
        skills = [row[0] for row in cursor.fetchall()]
        conn.close()
        return jsonify(skills)
    except Exception as e:
        return jsonify([]), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)