import PyPDF2
import docx
import re
from datetime import datetime
import os

class ResumeParser:
    def __init__(self):
        self.education_keywords = [
            'education', 'degree', 'university', 'college', 'bachelor', 'master', 
            'phd', 'diploma', 'certification', 'course', 'school'
        ]
        
        self.experience_keywords = [
            'experience', 'work', 'employment', 'job', 'position', 'role',
            'worked', 'served', 'employed', 'career', 'professional'
        ]
        
        self.skill_keywords = [
            'skills', 'technical skills', 'programming', 'languages', 
            'technologies', 'tools', 'software', 'frameworks', 'libraries'
        ]
    
    def parse_resume(self, file_path):
        """Parse resume and extract structured information"""
        try:
            # Extract text based on file type
            text = self.extract_text(file_path)
            
            if not text:
                return {'error': 'Could not extract text from file'}
            
            # Parse different sections
            parsed_data = {
                'text': text,
                'contact_info': self.extract_contact_info(text),
                'education': self.extract_education(text),
                'experience': self.extract_experience(text),
                'skills': self.extract_skills_section(text),
                'summary': self.extract_summary(text)
            }
            
            return parsed_data
            
        except Exception as e:
            return {'error': f'Error parsing resume: {str(e)}'}
    
    def extract_text(self, file_path):
        """Extract text from different file formats"""
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            return self.extract_pdf_text(file_path)
        elif file_extension in ['.doc', '.docx']:
            return self.extract_docx_text(file_path)
        elif file_extension == '.txt':
            return self.extract_txt_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def extract_pdf_text(self, file_path):
        """Extract text from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    def extract_docx_text(self, file_path):
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")
    
    def extract_txt_text(self, file_path):
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            raise Exception(f"Error reading TXT: {str(e)}")
    
    def extract_contact_info(self, text):
        """Extract contact information"""
        contact_info = {}
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
        
        # Extract phone number
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        if phones:
            contact_info['phone'] = ''.join(phones[0])
        
        # Extract LinkedIn profile
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin = re.search(linkedin_pattern, text, re.IGNORECASE)
        if linkedin:
            contact_info['linkedin'] = linkedin.group()
        
        # Extract name (heuristic: first line that's not contact info)
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and len(line.split()) <= 4 and not any(keyword in line.lower() for keyword in ['email', 'phone', 'address']):
                if not re.search(r'[0-9@]', line):
                    contact_info['name'] = line
                    break
        
        return contact_info
    
    def extract_education(self, text):
        """Extract education information"""
        education = []
        
        # Find education section
        education_section = self.find_section(text, self.education_keywords)
        
        if education_section:
            # Extract degrees
            degree_patterns = [
                r'(Bachelor|Master|PhD|Ph\.D|MBA|B\.S|M\.S|B\.A|M\.A)\s+.*?(\d{4})',
                r'(Diploma|Certificate)\s+.*?(\d{4})',
                r'(University|College)\s+.*?(\d{4})'
            ]
            
            for pattern in degree_patterns:
                matches = re.finditer(pattern, education_section, re.IGNORECASE)
                for match in matches:
                    education.append({
                        'degree': match.group(1),
                        'details': match.group(0),
                        'year': match.group(2) if len(match.groups()) > 1 else None
                    })
        
        return education
    
    def extract_experience(self, text):
        """Extract work experience information"""
        experience = []
        
        # Find experience section
        experience_section = self.find_section(text, self.experience_keywords)
        
        if experience_section:
            # Extract job titles and companies
            job_patterns = [
                r'([A-Z][a-z\s]+(?:Manager|Developer|Engineer|Analyst|Specialist|Coordinator|Director|Lead|Senior|Junior))\s*[-–]\s*([A-Z][A-Za-z\s&.,]+)?\s*\(?([\d]{4})\s*[-–]\s*([\d]{4}|Present)',
                r'([A-Z][a-z\s]+(?:Manager|Developer|Engineer|Analyst|Specialist|Coordinator|Director|Lead|Senior|Junior))\s+at\s+([A-Z][A-Za-z\s&.,]+)\s*\(?([\d]{4})'
            ]
            
            for pattern in job_patterns:
                matches = re.finditer(pattern, experience_section, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    groups = match.groups()
                    experience.append({
                        'title': groups[0].strip() if groups[0] else '',
                        'company': groups[1].strip() if len(groups) > 1 and groups[1] else '',
                        'start_year': groups[2] if len(groups) > 2 else None,
                        'end_year': groups[3] if len(groups) > 3 else None,
                        'details': match.group(0)
                    })
        
        return experience
    
    def extract_skills_section(self, text):
        """Extract skills from dedicated skills section"""
        skills = []
        
        # Find skills section
        skills_section = self.find_section(text, self.skill_keywords)
        
        if skills_section:
            # Common skill patterns
            skill_patterns = [
                r'([A-Z][a-zA-Z+#\s]+(?:Python|Java|JavaScript|React|Angular|Vue|Node|SQL|HTML|CSS|AWS|Docker|Git|Linux|Windows|MacOS|Office|Excel|PowerPoint|Photoshop|Illustrator))',
                r'•\s*([A-Za-z+#\s]+)',
                r'-\s*([A-Za-z+#\s]+)',
                r'\n([A-Z][a-zA-Z+#\s]{2,20})(?:\n|$)',
            ]
            
            for pattern in skill_patterns:
                matches = re.findall(pattern, skills_section)
                for match in matches:
                    skill = match.strip() if isinstance(match, str) else match[0].strip()
                    if len(skill) > 1 and len(skill) < 30:
                        skills.append(skill)
        
        # Remove duplicates while preserving order
        unique_skills = []
        for skill in skills:
            if skill not in unique_skills:
                unique_skills.append(skill)
        
        return unique_skills[:20]  # Limit to 20 skills
    
    def extract_summary(self, text):
        """Extract professional summary or objective"""
        summary_keywords = ['summary', 'objective', 'profile', 'about', 'overview']
        
        lines = text.split('\n')
        summary_start = -1
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in summary_keywords):
                summary_start = i
                break
        
        if summary_start != -1:
            # Extract next few lines as summary
            summary_lines = []
            for i in range(summary_start + 1, min(summary_start + 5, len(lines))):
                line = lines[i].strip()
                if line and not any(keyword in line.lower() for keyword in ['education', 'experience', 'skills']):
                    summary_lines.append(line)
                else:
                    break
            
            return ' '.join(summary_lines) if summary_lines else None
        
        return None
    
    def find_section(self, text, keywords):
        """Find a section in the text based on keywords"""
        lines = text.split('\n')
        section_start = -1
        section_end = len(lines)
        
        # Find section start
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in keywords):
                section_start = i
                break
        
        if section_start == -1:
            return None
        
        # Find section end (next major section)
        other_section_keywords = [
            'education', 'experience', 'skills', 'projects', 'certifications',
            'achievements', 'awards', 'references', 'contact', 'summary'
        ]
        
        current_keywords = set(keywords)
        
        for i in range(section_start + 2, len(lines)):
            line = lines[i].lower().strip()
            if any(keyword in line for keyword in other_section_keywords):
                if not any(keyword in line for keyword in current_keywords):
                    section_end = i
                    break
        
        # Extract section text
        section_lines = lines[section_start:section_end]
        return '\n'.join(section_lines)
    
    def calculate_experience_years(self, experience_list):
        """Calculate total years of experience"""
        total_months = 0
        current_year = datetime.now().year
        
        for exp in experience_list:
            start_year = int(exp.get('start_year', 0)) if exp.get('start_year') else 0
            end_year = int(exp.get('end_year', current_year)) if exp.get('end_year') and exp.get('end_year') != 'Present' else current_year
            
            if start_year > 0:
                years_diff = end_year - start_year
                total_months += years_diff * 12
        
        return round(total_months / 12, 1)
    
    def extract_certifications(self, text):
        """Extract certifications and courses"""
        certifications = []
        
        cert_keywords = ['certification', 'certificate', 'course', 'training', 'certified']
        cert_section = self.find_section(text, cert_keywords)
        
        if cert_section:
            # Common certification patterns
            cert_patterns = [
                r'([A-Z][A-Za-z\s]+(?:Certification|Certificate|Course))\s*[-–]\s*([A-Za-z\s]+)?\s*\(?([\d]{4})',
                r'([A-Z][A-Za-z\s]+)\s+Certified\s*\(?([\d]{4})',
                r'([A-Z][A-Za-z\s]+)\s+Certificate\s*\(?([\d]{4})'
            ]
            
            for pattern in cert_patterns:
                matches = re.finditer(pattern, cert_section, re.IGNORECASE)
                for match in matches:
                    groups = match.groups()
                    certifications.append({
                        'name': groups[0].strip(),
                        'issuer': groups[1].strip() if len(groups) > 1 and groups[1] else '',
                        'year': groups[-1] if groups[-1] else None
                    })
        
        return certifications
    
    def get_resume_score(self, parsed_data):
        """Calculate a completeness score for the resume"""
        score = 0
        max_score = 100
        
        # Contact information (20 points)
        contact = parsed_data.get('contact_info', {})
        if contact.get('email'):
            score += 10
        if contact.get('phone'):
            score += 5
        if contact.get('name'):
            score += 5
        
        # Education (20 points)
        education = parsed_data.get('education', [])
        if education:
            score += 20
        
        # Experience (30 points)
        experience = parsed_data.get('experience', [])
        if experience:
            score += min(30, len(experience) * 10)
        
        # Skills (20 points)
        skills = parsed_data.get('skills', [])
        if skills:
            score += min(20, len(skills) * 2)
        
        # Summary (10 points)
        if parsed_data.get('summary'):
            score += 10
        
        return min(score, max_score)