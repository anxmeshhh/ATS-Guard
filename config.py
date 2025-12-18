import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'career-cosmos-secret-key-2024'
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY') or 'your-google-api-key-here'
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Database configuration
    DATABASE_PATH = 'ats_tool.db'
    
    # File extensions
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
    
    # ATS Scoring weights
    KEYWORD_WEIGHT = 0.40
    FORMAT_WEIGHT = 0.25
    CONTENT_WEIGHT = 0.20
    LENGTH_WEIGHT = 0.15
    
    # AI Configuration
    AI_MODEL = 'gemini-2.0-flash-exp'
    AI_TEMPERATURE = 0.7
    AI_MAX_TOKENS = 2048
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
