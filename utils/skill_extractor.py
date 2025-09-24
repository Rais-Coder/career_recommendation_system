import re
from collections import Counter
import json

class SkillExtractor:
    def __init__(self):
        # Comprehensive skill database organized by categories
        self.skill_database = {
            'programming_languages': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c', 'php', 'ruby', 
                'go', 'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl', 'shell', 'bash'
            ],
            'web_technologies': [
                'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django', 
                'flask', 'spring', 'bootstrap', 'jquery', 'sass', 'less', 'webpack', 'npm'
            ],
            'databases': [
                'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 
                'cassandra', 'elasticsearch', 'dynamodb', 'firebase'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'google cloud', 'gcp', 'heroku', 'digitalocean', 'linode'
            ],
            'devops_tools': [
                'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab', 'bitbucket', 
                'ansible', 'terraform', 'vagrant', 'chef', 'puppet'
            ],
            'data_science': [
                'machine learning', 'deep learning', 'artificial intelligence', 'data analysis',
                'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'matplotlib',
                'seaborn', 'plotly', 'tableau', 'power bi', 'jupyter', 'statistics'
            ],
            'mobile_development': [
                'android', 'ios', 'react native', 'flutter', 'xamarin', 'cordova', 'ionic'
            ],
            'design_tools': [
                'photoshop', 'illustrator', 'figma', 'sketch', 'adobe xd', 'indesign', 
                'canva', 'ui/ux design', 'user experience', 'user interface'
            ],
            'project_management': [
                'agile', 'scrum', 'kanban', 'jira', 'trello', 'asana', 'monday.com', 
                'project management', 'waterfall'
            ],
            'soft_skills': [
                'communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking',
                'time management', 'adaptability', 'creativity', 'analytical thinking', 
                'decision making', 'collaboration', 'negotiation', 'presentation'
            ],
            'business_skills': [
                'business analysis', 'market research', 'strategic planning', 'financial analysis',
                'risk management', 'process improvement', 'stakeholder management', 'budgeting'
            ],
            'microsoft_office': [
                'excel', 'word', 'powerpoint', 'outlook', 'access', 'visio', 'sharepoint', 'teams'
            ],
            'operating_systems': [
                'linux', 'unix', 'windows', 'macos', 'ubuntu', 'centos', 'debian'
            ]
        }
        
        # Flatten skill database for easier searching
        self.all_skills = []
        for category, skills in self.skill_database.items():
            for skill in skills:
                self.all_skills.append({
                    'skill': skill,
                    'category': category,
                    'variations': self.get_skill_variations(skill)
                })
        
        # Common skill patterns and variations
        self.skill_patterns = {
            'programming': r'\b(python|java|javascript|c\+\+|c#|php|ruby|go|rust|swift|kotlin)\b',
            'web_framework': r'\b(react|angular|vue|django|flask|spring|express)\b',
            'database': r'\b(sql|mysql|postgresql|mongodb|redis|oracle)\b',
            'cloud': r'\b(aws|azure|google cloud|gcp|docker|kubernetes)\b',
            'tools': r'\b(git|jenkins|jira|tableau|excel|photoshop)\b'
        }
    
    def get_skill_variations(self, skill):
        """Generate common variations of a skill name"""
        variations = [skill.lower()]
        
        # Add variations with different separators
        if ' ' in skill:
            variations.append(skill.replace(' ', '-'))
            variations.append(skill.replace(' ', '_'))
            variations.append(skill.replace(' ', ''))
        
        # Add variations with dots
        if '.' not in skill:
            variations.append(skill + '.js' if 'node' in skill else skill)
        
        # Add common abbreviations
        abbreviations = {
            'javascript': ['js'],
            'typescript': ['ts'],
            'python': ['py'],
            'artificial intelligence': ['ai'],
            'machine learning': ['ml'],
            'user experience': ['ux'],
            'user interface': ['ui'],
            'cascading style sheets': ['css'],
            'hypertext markup language': ['html'],
            'structured query language': ['sql']
        }
        
        if skill.lower() in abbreviations:
            variations.extend(abbreviations[skill.lower()])
        
        return variations
    
    def extract_skills(self, text, confidence_threshold=0.6):
        """Extract skills from text with confidence scores"""
        if not text:
            return {}
        
        text_lower = text.lower()
        extracted_skills = {}
        
        # Extract skills using pattern matching
        for skill_data in self.all_skills:
            skill_name = skill_data['skill']
            variations = skill_data['variations']
            category = skill_data['category']
            
            confidence = 0
            matches = 0
            
            # Check for exact matches and variations
            for variation in variations:
                pattern = r'\b' + re.escape(variation) + r'\b'
                found_matches = len(re.findall(pattern, text_lower))
                matches += found_matches
                
                if found_matches > 0:
                    # Base confidence based on context
                    confidence += self.calculate_context_confidence(text_lower, variation)
            
            # Calculate final confidence score
            if matches > 0:
                # Boost confidence based on frequency
                frequency_boost = min(matches * 0.1, 0.3)
                context_boost = self.get_context_boost(text_lower, skill_name, category)
                
                final_confidence = min(confidence + frequency_boost + context_boost, 1.0)
                
                if final_confidence >= confidence_threshold:
                    extracted_skills[skill_name.title()] = final_confidence
        
        # Sort by confidence and return top skills
        sorted_skills = dict(sorted(extracted_skills.items(), key=lambda x: x[1], reverse=True))
        return dict(list(sorted_skills.items())[:25])  # Return top 25 skills
    
    def calculate_context_confidence(self, text, skill):
        """Calculate confidence based on context around skill mentions"""
        base_confidence = 0.7
        
        # Context words that indicate skill proficiency
        proficiency_indicators = [
            'expert', 'advanced', 'proficient', 'skilled', 'experienced', 
            'familiar', 'knowledge', 'years', 'project', 'developed', 'built',
            'implemented', 'designed', 'created', 'managed', 'led'
        ]
        
        # Find skill mentions in context
        skill_pattern = r'.{0,50}\b' + re.escape(skill) + r'\b.{0,50}'
        contexts = re.findall(skill_pattern, text, re.IGNORECASE)
        
        context_confidence = 0
        for context in contexts:
            context_lower = context.lower()
            for indicator in proficiency_indicators:
                if indicator in context_lower:
                    context_confidence += 0.1
        
        return min(base_confidence + context_confidence, 1.0)
    
    def get_context_boost(self, text, skill, category):
        """Get confidence boost based on skill category context"""
        category_contexts = {
            'programming_languages': ['programming', 'coding', 'development', 'software', 'application'],
            'web_technologies': ['web', 'frontend', 'backend', 'fullstack', 'website'],
            'databases': ['database', 'data', 'query', 'storage', 'schema'],
            'cloud_platforms': ['cloud', 'infrastructure', 'deployment', 'scalability'],
            'data_science': ['analytics', 'analysis', 'modeling', 'prediction', 'insights'],
            'design_tools': ['design', 'creative', 'visual', 'graphics', 'branding'],
            'soft_skills': ['team', 'communication', 'management', 'leadership', 'collaboration']
        }
        
        context_words = category_contexts.get(category, [])
        boost = 0
        
        for word in context_words:
            if word in text:
                boost += 0.05
        
        return min(boost, 0.2)
    
    def extract_skill_levels(self, text, skills):
        """Extract proficiency levels for identified skills"""
        skill_levels = {}
        
        level_indicators = {
            5: ['expert', 'advanced', 'senior', 'lead', 'architect', 'specialist'],
            4: ['proficient', 'experienced', 'skilled', 'strong', 'solid'],
            3: ['intermediate', 'competent', 'working knowledge', 'familiar'],
            2: ['basic', 'beginner', 'learning', 'exposure', 'some experience'],
            1: ['novice', 'entry-level', 'introductory', 'fundamentals']
        }
        
        text_lower = text.lower()
        
        for skill in skills:
            skill_level = 3  # Default intermediate level
            skill_lower = skill.lower()
            
            # Look for skill mentions with level indicators
            skill_pattern = r'.{0,100}\b' + re.escape(skill_lower) + r'\b.{0,100}'
            contexts = re.findall(skill_pattern, text_lower)
            
            for context in contexts:
                for level, indicators in level_indicators.items():
                    if any(indicator in context for indicator in indicators):
                        skill_level = max(skill_level, level)
                        break
            
            # Adjust based on years of experience mentioned
            years_pattern = r'(\d+)\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience\s*)?(?:with\s*|in\s*|using\s*)?' + re.escape(skill_lower)
            years_match = re.search(years_pattern, text_lower)
            
            if years_match:
                years = int(years_match.group(1))
                if years >= 5:
                    skill_level = 5
                elif years >= 3:
                    skill_level = max(skill_level, 4)
                elif years >= 1:
                    skill_level = max(skill_level, 3)
            
            skill_levels[skill] = skill_level
        
        return skill_levels
    
    def categorize_skills(self, skills):
        """Categorize extracted skills"""
        categorized = {}
        
        for skill in skills:
            skill_lower = skill.lower()
            category_found = False
            
            for category, category_skills in self.skill_database.items():
                if skill_lower in [s.lower() for s in category_skills]:
                    if category not in categorized:
                        categorized[category] = []
                    categorized[category].append(skill)
                    category_found = True
                    break
            
            if not category_found:
                if 'other' not in categorized:
                    categorized['other'] = []
                categorized['other'].append(skill)
        
        return categorized
    
    def suggest_related_skills(self, current_skills, limit=5):
        """Suggest related skills based on current skills"""
        current_skills_lower = [skill.lower() for skill in current_skills]
        suggestions = {}
        
        # Find categories of current skills
        user_categories = set()
        for skill in current_skills_lower:
            for category, category_skills in self.skill_database.items():
                if skill in [s.lower() for s in category_skills]:
                    user_categories.add(category)
        
        # Suggest skills from same categories
        for category in user_categories:
            category_skills = self.skill_database[category]
            for skill in category_skills:
                if skill.lower() not in current_skills_lower:
                    # Calculate relevance score based on category popularity
                    relevance = self.calculate_skill_relevance(skill, category, current_skills)
                    if relevance > 0.5:
                        suggestions[skill.title()] = relevance
        
        # Sort by relevance and return top suggestions
        sorted_suggestions = dict(sorted(suggestions.items(), key=lambda x: x[1], reverse=True))
        return dict(list(sorted_suggestions.items())[:limit])
    
    def calculate_skill_relevance(self, skill, category, current_skills):
        """Calculate how relevant a skill is based on current skills"""
        base_relevance = 0.6
        
        # Skill combinations that work well together
        skill_synergies = {
            'python': ['pandas', 'numpy', 'django', 'flask', 'machine learning'],
            'javascript': ['react', 'node.js', 'html', 'css', 'typescript'],
            'react': ['javascript', 'html', 'css', 'node.js', 'redux'],
            'aws': ['docker', 'kubernetes', 'linux', 'python', 'terraform'],
            'machine learning': ['python', 'statistics', 'pandas', 'numpy', 'tensorflow']
        }
        
        skill_lower = skill.lower()
        current_skills_lower = [s.lower() for s in current_skills]
        
        # Check for synergies
        synergy_boost = 0
        if skill_lower in skill_synergies:
            synergistic_skills = skill_synergies[skill_lower]
            common_skills = set(synergistic_skills).intersection(set(current_skills_lower))
            synergy_boost = len(common_skills) * 0.1
        
        # Check reverse synergies (current skills that work well with this skill)
        reverse_synergy_boost = 0
        for current_skill in current_skills_lower:
            if current_skill in skill_synergies:
                if skill_lower in skill_synergies[current_skill]:
                    reverse_synergy_boost += 0.15
        
        return min(base_relevance + synergy_boost + reverse_synergy_boost, 1.0)
    
    def get_skill_market_data(self, skills):
        """Get market demand data for skills (mock data for demonstration)"""
        # In a real implementation, this would fetch actual market data
        market_data = {}
        
        high_demand_skills = [
            'python', 'javascript', 'react', 'aws', 'machine learning', 
            'docker', 'kubernetes', 'java', 'sql', 'git'
        ]
        
        medium_demand_skills = [
            'angular', 'vue', 'php', 'c++', 'mongodb', 'postgresql', 
            'tableau', 'power bi', 'jenkins', 'ansible'
        ]
        
        for skill in skills:
            skill_lower = skill.lower()
            if any(s in skill_lower for s in high_demand_skills):
                demand_level = 'High'
                growth_trend = 'Growing'
            elif any(s in skill_lower for s in medium_demand_skills):
                demand_level = 'Medium'
                growth_trend = 'Stable'
            else:
                demand_level = 'Low'
                growth_trend = 'Stable'
            
            market_data[skill] = {
                'demand_level': demand_level,
                'growth_trend': growth_trend,
                'avg_salary_impact': 'Positive' if demand_level in ['High', 'Medium'] else 'Neutral'
            }
        
        return market_data