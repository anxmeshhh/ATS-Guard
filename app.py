from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv  # <-- Added to load .env file
import google.generativeai as genai  # kept for potential future use, but not used now
import PyPDF2
import docx
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import tempfile
from groq import Groq  # <-- Added Groq client

# Load environment variables from .env file
load_dotenv()

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

app = Flask(__name__)
app.secret_key = 'career_cosmos_secret_key_2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Load Groq API key from environment variable
groq_api_key = os.getenv('GROQ_API_KEY')
if not groq_api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables. Please set it in your .env file.")

app.config['GROQ_API_KEY'] = groq_api_key

# Configure Groq client
client = Groq(api_key=app.config['GROQ_API_KEY'])

# Model to use
GROQ_MODEL = "llama-3.1-8b-instant"  # <-- Changed to requested model

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database initialization
def init_db():
    conn = sqlite3.connect('ats_tool.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Analysis history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            ats_score INTEGER NOT NULL,
            keywords_matched INTEGER NOT NULL,
            total_keywords INTEGER NOT NULL,
            analysis_data TEXT,
            enhanced_resume TEXT,
            hr_evaluation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Advanced ATS Scoring Algorithm
class ATSScorer:
    def __init__(self):
        try:
            self.stop_words = set(stopwords.words('english'))
        except:
            self.stop_words = set(['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
        
    def extract_keywords_from_job_description(self, job_description):
        """Extract relevant keywords from job description"""
        # Clean and tokenize
        text = job_description.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        
        try:
            tokens = word_tokenize(text)
        except:
            tokens = text.split()
        
        # Remove stop words and short words
        keywords = [word for word in tokens if word not in self.stop_words and len(word) > 2]
        
        # Get most common keywords
        keyword_freq = Counter(keywords)
        
        # Extract technical skills, tools, and important terms
        technical_patterns = [
            r'\b(?:python|java|javascript|react|angular|vue|node|sql|mongodb|aws|azure|docker|kubernetes)\b',
            r'\b(?:machine learning|data science|artificial intelligence|deep learning)\b',
            r'\b(?:project management|agile|scrum|devops|ci/cd)\b',
            r'\b(?:bachelor|master|degree|certification|years?\s+experience)\b'
        ]
        
        technical_keywords = []
        for pattern in technical_patterns:
            matches = re.findall(pattern, job_description.lower())
            technical_keywords.extend(matches)
        
        # Combine frequency-based and pattern-based keywords
        all_keywords = list(keyword_freq.keys())[:20] + technical_keywords
        return list(set(all_keywords))
    
    def calculate_ats_score(self, resume_text, job_description):
        """Calculate comprehensive ATS score"""
        job_keywords = self.extract_keywords_from_job_description(job_description)
        resume_text_lower = resume_text.lower()
        
        # Keyword matching score (40% weight)
        matched_keywords = []
        for keyword in job_keywords:
            if keyword.lower() in resume_text_lower:
                matched_keywords.append(keyword)
        
        keyword_score = (len(matched_keywords) / len(job_keywords)) * 40 if job_keywords else 0
        
        # Format and structure score (25% weight)
        format_score = self.calculate_format_score(resume_text) * 25
        
        # Content quality score (20% weight)
        content_score = self.calculate_content_score(resume_text) * 20
        
        # Length and completeness score (15% weight)
        length_score = self.calculate_length_score(resume_text) * 15
        
        total_score = min(100, keyword_score + format_score + content_score + length_score)
        
        return {
            'total_score': int(round(total_score)),
            'keyword_score': int(round(keyword_score * 100/40)),
            'format_score': int(round(format_score * 100/25)),
            'content_score': int(round(content_score * 100/20)),
            'length_score': int(round(length_score * 100/15)),
            'matched_keywords': matched_keywords,
            'total_keywords': len(job_keywords),
            'missing_keywords': [kw for kw in job_keywords if kw.lower() not in resume_text_lower]
        }
    
    def calculate_format_score(self, resume_text):
        """Calculate format and structure score"""
        score = 0
        
        # Check for common resume sections
        sections = ['experience', 'education', 'skills', 'summary', 'objective']
        for section in sections:
            if section in resume_text.lower():
                score += 0.15
        
        # Check for contact information
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        
        if re.search(email_pattern, resume_text):
            score += 0.1
        if re.search(phone_pattern, resume_text):
            score += 0.1
        
        # Check for proper formatting indicators
        if len(resume_text.split('\n')) > 10:  # Multiple lines indicate structure
            score += 0.1
        
        return min(1.0, score)
    
    def calculate_content_score(self, resume_text):
        """Calculate content quality score"""
        score = 0
        
        # Check for action verbs
        action_verbs = ['managed', 'developed', 'created', 'implemented', 'designed',
                       'led', 'improved', 'increased', 'achieved', 'delivered']
        for verb in action_verbs:
            if verb in resume_text.lower():
                score += 0.05
        
        # Check for quantifiable achievements
        number_pattern = r'\b\d+%|\b\d+\s*(million|thousand|k\b)'
        if re.search(number_pattern, resume_text.lower()):
            score += 0.3
        
        # Check for relevant keywords density
        word_count = len(resume_text.split())
        if 300 <= word_count <= 800:
            score += 0.2
        
        return min(1.0, score)
    
    def calculate_length_score(self, resume_text):
        """Calculate appropriate length score"""
        word_count = len(resume_text.split())
        
        if 400 <= word_count <= 600:
            return 1.0
        elif 300 <= word_count < 400 or 600 < word_count <= 800:
            return 0.8
        elif 200 <= word_count < 300 or 800 < word_count <= 1000:
            return 0.6
        else:
            return 0.4

# Initialize ATS Scorer
ats_scorer = ATSScorer()

def extract_text_from_file(file_path, filename):
    """Extract text from uploaded file"""
    try:
        if filename.lower().endswith('.pdf'):
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        
        elif filename.lower().endswith('.docx'):
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        
        elif filename.lower().endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        
        return ""
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

# Helper function to call Groq API
def groq_generate_content(prompt):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=GROQ_MODEL,
            temperature=0.7,
            max_tokens=4096,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Generation failed: {str(e)}"

def get_hr_evaluation(resume_text, job_description):
    """Get HR professional evaluation of the resume"""
    hr_prompt = f"""
    You are an experienced Technical Human Resource Manager. Your task is to review the provided resume against the job description.

    Please share your professional evaluation on whether the candidate's profile aligns with the role. Highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.

    RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}

    Please provide a comprehensive HR evaluation covering:

    1. **OVERALL PROFILE ALIGNMENT**
       - Does the candidate's profile match the role requirements?
       - Overall suitability rating (Excellent/Good/Average/Poor)

    2. **KEY STRENGTHS**
       - Technical skills that align well with requirements
       - Relevant experience and achievements
       - Educational background fit
       - Soft skills demonstrated

    3. **AREAS OF CONCERN/WEAKNESSES**
       - Missing technical skills or experience
       - Gaps in qualifications
       - Areas that need improvement

    4. **EXPERIENCE ANALYSIS**
       - Relevance of work experience
       - Career progression assessment
       - Industry experience match

    5. **RECOMMENDATIONS**
       - Should we proceed with this candidate?
       - What questions to focus on during interview?
       - Areas to probe further

    Format your response professionally as an HR evaluation report.
    """
    
    return groq_generate_content(hr_prompt)

def get_ats_evaluation(resume_text, job_description, ats_analysis):
    """Get ATS scanner evaluation"""
    ats_prompt = f"""
    You are a skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality. Your task is to evaluate the resume against the provided job description.

    Give me the percentage of match if the resume matches the job description. First the output should come as percentage and then keywords missing and last final thoughts.

    RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}

    CURRENT ATS ANALYSIS:
    - ATS Score: {ats_analysis['total_score']}%
    - Keywords Matched: {len(ats_analysis['matched_keywords'])}/{ats_analysis['total_keywords']}
    - Missing Keywords: {', '.join(ats_analysis['missing_keywords'][:15])}

    Please provide:

    1. **MATCH PERCENTAGE: {ats_analysis['total_score']}%**

    2. **MISSING KEYWORDS:**
       {', '.join(ats_analysis['missing_keywords'][:20])}

    3. **FINAL THOUGHTS:**
       - ATS Compatibility assessment
       - Likelihood of passing initial screening
       - Critical improvements needed
       - Overall recommendation for ATS optimization

    Format your response clearly with the percentage first, then missing keywords, then final thoughts.
    """
    
    return groq_generate_content(ats_prompt)

def enhance_resume_with_ai(resume_text, job_description, ats_analysis, hr_evaluation):
    """Generate an enhanced version of the resume using AI"""
    missing_keywords = ', '.join(ats_analysis['missing_keywords'][:15])
    matched_keywords = ', '.join(ats_analysis['matched_keywords'])
    
    prompt = f"""
    As an expert resume writer and ATS optimization specialist, please rewrite and enhance this resume to significantly improve its ATS score and address the HR evaluation concerns.

    ORIGINAL RESUME:
    {resume_text}

    TARGET JOB DESCRIPTION:
    {job_description}

    CURRENT ATS ANALYSIS:
    - Current Score: {ats_analysis['total_score']}/100
    - Keywords Successfully Matched: {matched_keywords}
    - Missing Important Keywords: {missing_keywords}

    HR EVALUATION INSIGHTS:
    {hr_evaluation[:1000]}...

    ENHANCEMENT REQUIREMENTS:
    1. Naturally incorporate the missing keywords where relevant and truthful
    2. Address the weaknesses identified in the HR evaluation
    3. Strengthen the areas highlighted as concerns
    4. Improve action verbs and quantify achievements where possible
    5. Optimize section headings for ATS scanning (Experience, Education, Skills, etc.)
    6. Enhance the professional summary/objective to match job requirements
    7. Improve formatting and structure for better ATS parsing
    8. Add relevant skills and technologies mentioned in job description
    9. Strengthen accomplishment statements with metrics and results
    10. Ensure keyword density is optimized without keyword stuffing
    11. Maintain authenticity - don't add false information
    12. Structure content for maximum ATS compatibility

    Please provide a complete, enhanced resume that maintains the original experience and qualifications while significantly improving ATS compatibility and addressing HR concerns.

    IMPORTANT: Return only the enhanced resume content, properly formatted with clear sections.
    """
    
    return groq_generate_content(prompt)

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if not username or not email or not password:
            flash('All fields are required')
            return render_template('register.html')
        
        conn = sqlite3.connect('ats_tool.db')
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            flash('Username or email already exists')
            conn.close()
            return render_template('register.html')
        
        # Create new user
        password_hash = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                      (username, email, password_hash))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('ats_tool.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    try:
        # Get form data
        job_description = request.form.get('job_description', '')
        resume_file = request.files.get('resume_file')
        resume_text = request.form.get('resume_text', '')
        
        if not job_description:
            return jsonify({'error': 'Job description is required'}), 400
        
        # Extract resume text
        if resume_file and resume_file.filename:
            if not allowed_file(resume_file.filename):
                return jsonify({'error': 'Invalid file type. Please upload PDF, DOCX, or TXT files.'}), 400
            
            filename = secure_filename(resume_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            resume_file.save(file_path)
            
            resume_text = extract_text_from_file(file_path, filename)
            os.remove(file_path)  # Clean up uploaded file
        
        if not resume_text.strip():
            return jsonify({'error': 'Resume text is required'}), 400
        
        # Step 1: Get HR Evaluation
        hr_evaluation = get_hr_evaluation(resume_text, job_description)
        
        # Step 2: Perform ATS analysis
        ats_analysis = ats_scorer.calculate_ats_score(resume_text, job_description)
        
        # Step 3: Get ATS evaluation
        ats_evaluation = get_ats_evaluation(resume_text, job_description, ats_analysis)
        
        # Save analysis to database
        conn = sqlite3.connect('ats_tool.db')
        cursor = conn.cursor()
        analysis_data = json.dumps({
            'ats_analysis': ats_analysis,
            'ats_evaluation': ats_evaluation,
            'job_description': job_description[:500],  # Store first 500 chars
            'resume_text': resume_text[:1000]  # Store first 1000 chars for enhancement
        })
        
        cursor.execute('''
            INSERT INTO analysis_history 
            (user_id, filename, ats_score, keywords_matched, total_keywords, analysis_data, hr_evaluation)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            resume_file.filename if resume_file else 'Text Input',
            ats_analysis['total_score'],
            len(ats_analysis['matched_keywords']),
            ats_analysis['total_keywords'],
            analysis_data,
            hr_evaluation
        ))
        
        analysis_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'hr_evaluation': hr_evaluation,
            'ats_analysis': ats_analysis,
            'ats_evaluation': ats_evaluation
        })
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/enhance_resume', methods=['POST'])
def enhance_resume():
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    try:
        data = request.get_json()
        analysis_id = data.get('analysis_id')
        
        if not analysis_id:
            return jsonify({'error': 'Analysis ID required'}), 400
        
        # Get analysis data from database
        conn = sqlite3.connect('ats_tool.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT analysis_data, hr_evaluation FROM analysis_history 
            WHERE id = ? AND user_id = ?
        ''', (analysis_id, session['user_id']))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'Analysis not found'}), 404
        
        analysis_data_json, hr_evaluation = result
        analysis_data = json.loads(analysis_data_json)
        
        # Extract necessary data
        ats_analysis = analysis_data['ats_analysis']
        job_description = analysis_data['job_description']
        resume_text = analysis_data['resume_text']
        
        # Generate enhanced resume
        enhanced_resume = enhance_resume_with_ai(resume_text, job_description, ats_analysis, hr_evaluation)
        
        # Update database with enhanced resume
        cursor.execute('''
            UPDATE analysis_history 
            SET enhanced_resume = ? 
            WHERE id = ?
        ''', (enhanced_resume, analysis_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'enhanced_resume': enhanced_resume
        })
        
    except Exception as e:
        return jsonify({'error': f'Enhancement failed: {str(e)}'}), 500

@app.route('/download_enhanced_resume/<int:analysis_id>')
def download_enhanced_resume(analysis_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Get analysis data from database
        conn = sqlite3.connect('ats_tool.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT enhanced_resume, analysis_data, ats_score, filename
            FROM analysis_history 
            WHERE id = ? AND user_id = ?
        ''', (analysis_id, session['user_id']))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            flash('Analysis not found')
            return redirect(url_for('index'))
        
        enhanced_resume, analysis_data_json, original_score, filename = result
        
        if not enhanced_resume:
            flash('No enhanced resume available. Please generate one first.')
            return redirect(url_for('index'))
        
        # Parse analysis data
        try:
            analysis_data = json.loads(analysis_data_json)
            ats_analysis = analysis_data.get('ats_analysis', {})
        except:
            ats_analysis = {}
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            textColor=colors.HexColor('#FFD700'),
            alignment=1  # Center alignment
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#000000'),
            borderWidth=1,
            borderColor=colors.HexColor('#FFD700'),
            borderPadding=5
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=20
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph("Enhanced Resume - Career Cosmos ATS Optimization", title_style))
        story.append(Spacer(1, 20))
        
        # Score improvement info
        if ats_analysis:
            score_table_data = [
                ['Metric', 'Score', 'Details'],
                ['ATS Score', f"{ats_analysis.get('total_score', 'N/A')}%", 'Overall ATS Compatibility'],
                ['Keywords Matched', f"{len(ats_analysis.get('matched_keywords', []))}", f"Out of {ats_analysis.get('total_keywords', 0)} total"],
                ['Format Score', f"{ats_analysis.get('format_score', 'N/A')}%", 'Resume Structure & Format'],
                ['Content Score', f"{ats_analysis.get('content_score', 'N/A')}%", 'Content Quality Assessment']
            ]
            
            score_table = Table(score_table_data)
            score_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFD700')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(score_table)
            story.append(Spacer(1, 30))
        
        # Enhanced Resume Content
        story.append(Paragraph("ENHANCED RESUME", header_style))
        story.append(Spacer(1, 12))
        
        # Process the enhanced resume text
        sections = enhanced_resume.split('\n\n')
        
        for section in sections:
            if section.strip():
                lines = section.split('\n')
                if lines:
                    # Check if first line looks like a header
                    first_line = lines[0].strip()
                    if (first_line.isupper() or 
                        any(keyword in first_line.lower() for keyword in 
                            ['summary', 'experience', 'education', 'skills', 'objective', 'contact'])):
                        # This is likely a section header
                        story.append(Paragraph(first_line, header_style))
                        story.append(Spacer(1, 6))
                        
                        # Add the rest of the lines as body text
                        for line in lines[1:]:
                            if line.strip():
                                story.append(Paragraph(line.strip(), body_style))
                    else:
                        # Regular content
                        for line in lines:
                            if line.strip():
                                story.append(Paragraph(line.strip(), body_style))
                
                story.append(Spacer(1, 12))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=1
        )
        
        story.append(Spacer(1, 30))
        story.append(Paragraph("Enhanced by Career Cosmos ATS Optimization Tool", footer_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"enhanced_resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}')
        return redirect(url_for('index'))

@app.route('/analysis_history')
def analysis_history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('ats_tool.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, filename, ats_score, keywords_matched, total_keywords, created_at
        FROM analysis_history 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 20
    ''', (session['user_id'],))
    
    history = cursor.fetchall()
    conn.close()
    
    # Convert scores to integers to fix the template error
    processed_history = []
    for item in history:
        processed_item = list(item)
        # Ensure ats_score is an integer
        processed_item[2] = int(processed_item[2]) if processed_item[2] else 0
        processed_history.append(tuple(processed_item))
    
    return render_template('history.html', history=processed_history)

@app.route('/view_analysis/<int:analysis_id>')
def view_analysis(analysis_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('ats_tool.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT filename, ats_score, analysis_data, enhanced_resume, hr_evaluation, created_at
        FROM analysis_history 
        WHERE id = ? AND user_id = ?
    ''', (analysis_id, session['user_id']))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        flash('Analysis not found')
        return redirect(url_for('analysis_history'))
    
    filename, ats_score, analysis_data_json, enhanced_resume, hr_evaluation, created_at = result
    
    try:
        analysis_data = json.loads(analysis_data_json)
    except:
        analysis_data = {}
    
    # Ensure ats_score is an integer
    ats_score = int(ats_score) if ats_score else 0
    
    return render_template('view_analysis.html', 
                         analysis_id=analysis_id,
                         filename=filename,
                         ats_score=ats_score,
                         analysis_data=analysis_data,
                         enhanced_resume=enhanced_resume,
                         hr_evaluation=hr_evaluation,
                         created_at=created_at)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5007)