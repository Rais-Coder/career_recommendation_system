from models.ml_model import CareerRecommendationModel
from database.models import get_db_connection
import json
from datetime import datetime

class RecommendationEngine:
    def __init__(self):
        self.ml_model = CareerRecommendationModel()
    
    def generate_recommendations(self, user_id):
        """Generate comprehensive career recommendations for a user"""
        try:
            # Get ML-based recommendations
            ml_recommendations = self.ml_model.predict_career_match(user_id)
            
            # Save recommendations to database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Clear old recommendations
            cursor.execute('DELETE FROM recommendations WHERE user_id = ?', (user_id,))
            
            enhanced_recommendations = []
            
            for rec in ml_recommendations:
                # Generate learning path
                learning_path = self.ml_model.generate_learning_path(user_id, rec['career_id'])
                
                # Generate reasoning
                reasoning = self.generate_reasoning(rec)
                
                # Save to database
                cursor.execute('''
                    INSERT INTO recommendations 
                    (user_id, career_id, match_score, reasoning, skill_gaps, learning_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, rec['career_id'], rec['match_score'], reasoning,
                      json.dumps(rec['skill_gaps']), json.dumps(learning_path)))
                
                # Enhance recommendation with additional data
                enhanced_rec = rec.copy()
                enhanced_rec['reasoning'] = reasoning
                enhanced_rec['learning_path'] = learning_path
                enhanced_rec['match_breakdown'] = {
                    'skill_match': rec['skill_score'],
                    'education_match': rec['education_score'],
                    'experience_match': rec['experience_score'],
                    'interest_match': rec['interest_score']
                }
                
                enhanced_recommendations.append(enhanced_rec)
            
            conn.commit()
            conn.close()
            
            return enhanced_recommendations
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return []
    
    def generate_reasoning(self, recommendation):
        """Generate human-readable reasoning for recommendation"""
        reasoning_parts = []
        
        # Skill match reasoning
        if recommendation['skill_score'] >= 0.7:
            reasoning_parts.append("Strong skill alignment with your current expertise")
        elif recommendation['skill_score'] >= 0.4:
            reasoning_parts.append("Good foundation with some skill gaps to bridge")
        else:
            reasoning_parts.append("Opportunity to learn new skills in a growing field")
        
        # Experience reasoning
        if recommendation['experience_score'] >= 0.8:
            reasoning_parts.append("Your experience level matches well with typical requirements")
        elif recommendation['experience_score'] >= 0.5:
            reasoning_parts.append("Your experience provides a good starting point")
        
        # Market demand reasoning
        if recommendation['demand_score'] >= 0.8:
            reasoning_parts.append("High market demand with excellent job prospects")
        elif recommendation['demand_score'] >= 0.6:
            reasoning_parts.append("Steady market demand with good opportunities")
        
        # Growth potential
        if recommendation['growth_rate'] >= 0.15:
            reasoning_parts.append("Excellent career growth potential")
        elif recommendation['growth_rate'] >= 0.10:
            reasoning_parts.append("Good career growth prospects")
        
        return ". ".join(reasoning_parts) + "."
    
    def get_personalized_insights(self, user_id):
        """Get personalized insights for career development"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user's top skills
        cursor.execute('''
            SELECT s.skill_name, us.proficiency_level, s.category, mt.trend_score
            FROM user_skills us
            JOIN skills s ON us.skill_id = s.id
            LEFT JOIN market_trends mt ON s.id = mt.skill_id
            WHERE us.user_id = ?
            ORDER BY us.proficiency_level DESC, mt.trend_score DESC
            LIMIT 5
        ''', (user_id,))
        
        top_skills = cursor.fetchall()
        
        # Get trending skills user should consider
        cursor.execute('''
            SELECT s.skill_name, mt.trend_score, mt.demand_level, mt.salary_trend
            FROM market_trends mt
            JOIN skills s ON mt.skill_id = s.id
            LEFT JOIN user_skills us ON s.id = us.skill_id AND us.user_id = ?
            WHERE us.id IS NULL AND mt.trend_score > 0.7
            ORDER BY mt.trend_score DESC
            LIMIT 5
        ''', (user_id,))
        
        trending_skills = cursor.fetchall()
        
        # Get user's recent recommendations
        cursor.execute('''
            SELECT r.match_score, c.career_title, c.industry, r.created_at
            FROM recommendations r
            JOIN careers c ON r.career_id = c.id
            WHERE r.user_id = ?
            ORDER BY r.created_at DESC
            LIMIT 3
        ''', (user_id,))
        
        recent_recs = cursor.fetchall()
        
        conn.close()
        
        insights = {
            'top_skills': [dict(skill) for skill in top_skills],
            'trending_skills': [dict(skill) for skill in trending_skills],
            'recent_recommendations': [dict(rec) for rec in recent_recs],
            'recommendations': {
                'skill_development': self.generate_skill_development_advice(top_skills, trending_skills),
                'career_moves': self.generate_career_move_advice(recent_recs),
                'market_alignment': self.generate_market_alignment_advice(top_skills, trending_skills)
            }
        }
        
        return insights
    
    def generate_skill_development_advice(self, top_skills, trending_skills):
        """Generate advice for skill development"""
        advice = []
        
        if trending_skills:
            trending_skill_names = [skill['skill_name'] for skill in trending_skills[:3]]
            advice.append(f"Consider learning these trending skills: {', '.join(trending_skill_names)}")
        
        if top_skills:
            expert_skills = [skill['skill_name'] for skill in top_skills if skill['proficiency_level'] >= 4]
            if expert_skills:
                advice.append(f"Leverage your expertise in {', '.join(expert_skills)} for senior roles")
        
        return advice
    
    def generate_career_move_advice(self, recent_recs):
        """Generate career move advice based on recommendations"""
        advice = []
        
        if recent_recs:
            top_match = recent_recs[0]
            if top_match['match_score'] >= 0.8:
                advice.append(f"You're well-suited for {top_match['career_title']} - consider applying!")
            elif top_match['match_score'] >= 0.6:
                advice.append(f"With some preparation, {top_match['career_title']} could be a great fit")
        
        return advice
    
    def generate_market_alignment_advice(self, top_skills, trending_skills):
        """Generate market alignment advice"""
        advice = []
        
        # Check if user has trending skills
        user_skill_names = [skill['skill_name'] for skill in top_skills]
        trending_skill_names = [skill['skill_name'] for skill in trending_skills]
        
        alignment = set(user_skill_names).intersection(set(trending_skill_names))
        
        if alignment:
            advice.append(f"Your skills in {', '.join(alignment)} are highly valued in the current market")
        else:
            advice.append("Consider developing skills in high-demand areas to improve market positioning")
        
        return advice
    
    def compare_careers(self, career_ids, user_id=None):
        """Compare multiple careers side by side"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        comparison_data = []
        
        for career_id in career_ids:
            cursor.execute('''
                SELECT c.*, GROUP_CONCAT(s.skill_name) as required_skills
                FROM careers c
                LEFT JOIN career_skills cs ON c.id = cs.career_id
                LEFT JOIN skills s ON cs.skill_id = s.id
                WHERE c.id = ?
                GROUP BY c.id
            ''', (career_id,))
            
            career = cursor.fetchone()
            if career:
                career_data = dict(career)
                
                # Add match score if user provided
                if user_id:
                    cursor.execute('''
                        SELECT match_score FROM recommendations 
                        WHERE user_id = ? AND career_id = ?
                        ORDER BY created_at DESC LIMIT 1
                    ''', (user_id, career_id))
                    match = cursor.fetchone()
                    career_data['user_match_score'] = match['match_score'] if match else 0
                
                comparison_data.append(career_data)
        
        conn.close()
        return comparison_data
    
    def get_industry_insights(self, industry):
        """Get insights about a specific industry"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.career_title, c.avg_salary_min, c.avg_salary_max, 
                   c.growth_rate, c.demand_score, COUNT(r.id) as recommendation_count
            FROM careers c
            LEFT JOIN recommendations r ON c.id = r.career_id
            WHERE c.industry = ?
            GROUP BY c.id
            ORDER BY c.demand_score DESC
        ''', (industry,))
        
        careers = cursor.fetchall()
        
        if not careers:
            return None
        
        # Calculate industry metrics
        avg_salary = sum((career['avg_salary_min'] + career['avg_salary_max']) / 2 for career in careers) / len(careers)
        avg_growth = sum(career['growth_rate'] for career in careers) / len(careers)
        total_recommendations = sum(career['recommendation_count'] for career in careers)
        
        conn.close()
        
        return {
            'industry': industry,
            'career_count': len(careers),
            'average_salary': avg_salary,
            'average_growth_rate': avg_growth,
            'total_user_interest': total_recommendations,
            'top_careers': [dict(career) for career in careers[:5]]
        }