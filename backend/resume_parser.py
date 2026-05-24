import re
import json
from PyPDF2 import PdfReader
from docx import Document

nlp = None

def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        text = clean_text(text)
        return text
    except Exception as e:
        raise Exception(f"Error extracting PDF: {str(e)}")

def clean_text(text):
    artifacts = ['¯', '½', 'Ó']
    for artifact in artifacts:
        text = text.replace(artifact, ' ')
    
    icon_patterns = [
        '/envelope_alt', '/envelope', '/github', '/linkedin', '/twitter', 
        '/phone', '/map_marker', '/email', '/mail'
    ]
    for icon in icon_patterns:
        text = text.replace(icon, ' ')
    
    lines = text.split('\n')
    cleaned_lines = [re.sub(r'[ \t]+', ' ', line.strip()) for line in lines]
    text = '\n'.join(cleaned_lines)
    
    text = re.sub(r'\n\n\n+', '\n\n', text)
    
    return text

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        raise Exception(f"Error extracting DOCX: {str(e)}")

def extract_email(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    valid_emails = []
    for email in emails:
        email_lower = email.lower()
        invalid_patterns = ['envelope_alt', 'linkedin', 'github', 'twitter', 'icon_']
        
        is_invalid = any(pattern in email_lower for pattern in invalid_patterns)
        is_invalid = is_invalid or email.count('_') >= 3
        
        if not is_invalid:
            valid_emails.append(email)
    
    return valid_emails[0] if valid_emails else None

def extract_phone(text):
    phone_patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\+?\d{10,}',
        r'\d{3}[-.\s]\d{3}[-.\s]\d{4}'
    ]
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        if phones:
            return phones[0]
    return None

def extract_name(text):
    lines = text.split('\n')
    for line in lines[:5]:
        line = line.strip()
        line = re.sub(r'\s+', ' ', line)
        
        line = re.sub(r'\bPA\s+WA\b', 'PAWA', line, flags=re.IGNORECASE)
        line = re.sub(r'\bLA\s+L\b', 'LAL', line, flags=re.IGNORECASE)
        
        if line and len(line.split()) <= 4 and len(line) > 3:
            if not any(char.isdigit() for char in line) and not '@' in line:
                return line
    
    if nlp:
        doc = nlp(text[:1000])
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = re.sub(r'\s+', ' ', ent.text.strip())
                name = re.sub(r'\bPA\s+WA\b', 'PAWA', name, flags=re.IGNORECASE)
                name = re.sub(r'\bLA\s+L\b', 'LAL', name, flags=re.IGNORECASE)
                return name
    
    return "Unknown"

def extract_company_designation(text):
    company_keywords = ['at', 'with', 'working for', 'employed by', 'company:', 'organization:']
    designation_keywords = ['as', 'role:', 'position:', 'title:', 'designation:']
    
    lines = text.split('\n')
    company = None
    designation = None
    
    date_pattern = r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december|\d{4})'
    
    experience_start_idx = -1
    for idx, line in enumerate(lines):
        line_stripped = line.strip().lower()
        if line_stripped in ['experience', 'work experience', 'professional experience', 'employment', 'work history']:
            experience_start_idx = idx
            break
    
    start_idx = experience_start_idx + 1 if experience_start_idx >= 0 else 0
    
    for i in range(start_idx, len(lines)):
        line = lines[i]
        line_lower = line.lower()
        
        if company and designation:
            break
        
        if line.strip().startswith('•') or line.strip().startswith('-'):
            continue
            
        if re.search(date_pattern, line_lower) and ('-' in line or 'present' in line_lower or 'current' in line_lower):
            
            if ',' in line:
                parts = line.split(',')
                first_part = parts[0].strip()
                
                if re.search(date_pattern + r'.*?(-|present|current)', first_part, re.IGNORECASE):
                    match = re.search(r'^(.+?)\s+(' + date_pattern + r')', first_part, re.IGNORECASE)
                    if match and not company:
                        potential_company = match.group(1).strip()
                        if len(potential_company.split()) <= 5 and len(potential_company) > 2:
                            company = potential_company
                    
                    if len(parts) > 1 and not designation:
                        potential_designation = parts[-1].strip()
                        if potential_designation and len(potential_designation.split()) <= 8 and len(potential_designation) > 2:
                            if not re.search(date_pattern, potential_designation.lower()):
                                designation = potential_designation
                
                else:
                    potential_company = first_part.strip()
                    
                    if not re.search(date_pattern, potential_company.lower()) and not company:
                        if len(potential_company.split()) <= 5 and len(potential_company) > 2:
                            company = potential_company
                            
                            if not designation and i > start_idx:
                                prev_line = lines[i-1].strip()
                                if prev_line and not re.search(date_pattern, prev_line.lower()):
                                    if not prev_line.startswith('•') and not prev_line.startswith('-'):
                                        if len(prev_line.split()) <= 8 and len(prev_line) > 5:
                                            designation = prev_line
                            
        if not company and any(keyword in line_lower for keyword in company_keywords):
            parts = re.split(r'\bat\b|\bwith\b|\bworking for\b|\bemployed by\b', line_lower, maxsplit=1)
            if len(parts) > 1:
                company = parts[1].strip().split()[0:3]
                company = ' '.join(company).title()
        
        if not designation and any(keyword in line_lower for keyword in designation_keywords):
            parts = re.split(r'\bas\b|\brole:\b|\bposition:\b|\btitle:\b', line_lower, maxsplit=1)
            if len(parts) > 1:
                designation = parts[1].strip().split()[0:5]
                designation = ' '.join(designation).title()
    
    if nlp and not company:
        doc = nlp(text[:2000])
        for ent in doc.ents:
            if ent.label_ == "ORG":
                company = ent.text
                break
    
    return company, designation

def extract_skills(text):
    lines = text.split('\n')
    skills = []
    
    skills_section_headers = [
        'skills', 'technical skills', 'core competencies', 'technologies',
        'tools & technologies', 'technical expertise', 'key skills',
        'professional skills', 'competencies'
    ]
    
    skills_start_idx = -1
    for idx, line in enumerate(lines):
        line_stripped = line.strip().lower()
        if any(header == line_stripped or line_stripped.startswith(header + ':') for header in skills_section_headers):
            skills_start_idx = idx
            break
    
    if skills_start_idx == -1:
        return []
    
    skills_text = []
    for i in range(skills_start_idx + 1, len(lines)):
        line = lines[i].strip()
        
        if not line:
            continue
        
        line_lower = line.lower()
        section_keywords = ['experience', 'education', 'projects', 'certifications', 'work history', 'employment']
        if any(keyword == line_lower for keyword in section_keywords):
            break
        
        skills_text.append(line)
        
        if len(skills_text) >= 15:
            break
    
    all_skills_text = ' '.join(skills_text)
    
    separators = [',', '|', '•', '-', '/', ';', '\n']
    for sep in separators:
        all_skills_text = all_skills_text.replace(sep, ',')
    
    skill_candidates = [s.strip() for s in all_skills_text.split(',')]
    
    for skill in skill_candidates:
        if not skill:
            continue
        
        skill = re.sub(r'\(.*?\)', '', skill).strip()
        
        if 2 <= len(skill) <= 50 and not skill[0].isdigit():
            if len(skill.split()) <= 5:
                skills.append(skill)
    
    skills = list(dict.fromkeys(skills))
    
    return skills[:15]

def calculate_confidence_scores(data):
    scores = {}
    
    scores['name'] = 0.9 if data.get('name') and data['name'] != 'Unknown' else 0.3
    scores['email'] = 0.95 if data.get('email') else 0.0
    scores['phone'] = 0.9 if data.get('phone') else 0.0
    scores['company'] = 0.7 if data.get('company') else 0.0
    scores['designation'] = 0.7 if data.get('designation') else 0.0
    scores['skills'] = 0.8 if data.get('skills') and len(data['skills']) > 0 else 0.2
    
    return scores

def parse_resume(file_path, filename):
    if filename.lower().endswith('.pdf'):
        text = extract_text_from_pdf(file_path)
    elif filename.lower().endswith('.docx'):
        text = extract_text_from_docx(file_path)
    else:
        raise Exception("Unsupported file format")
    
    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    company, designation = extract_company_designation(text)
    skills = extract_skills(text)
    
    data = {
        'name': name,
        'email': email,
        'phone': phone,
        'company': company,
        'designation': designation,
        'skills': skills
    }
    
    confidence_scores = calculate_confidence_scores(data)
    
    return data, confidence_scores
