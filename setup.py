#!/usr/bin/env python3
"""
Career Cosmos ATS Setup Script
Run this script to set up the application
"""

import os
import sqlite3
import sys

def create_directories():
    """Create necessary directories"""
    directories = ['uploads', 'static/css', 'static/js', 'templates']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ Created directory: {directory}")

def setup_database():
    """Initialize the SQLite database"""
    try:
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
        print("✓ Database initialized successfully!")
        
    except Exception as e:
        print(f"✗ Error setting up database: {e}")
        return False
    
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        'flask',
        'werkzeug',
        'google.generativeai',
        'PyPDF2',
        'docx',
        'reportlab',
        'nltk'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("✗ Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n📦 Install them using: pip install -r requirements.txt")
        return False
    
    print("✓ All required packages are installed!")
    return True

def setup_environment():
    """Setup environment variables"""
    env_file = '.env'
    
    if not os.path.exists(env_file):
        with open(env_file, 'w') as f:
            f.write("# Career Cosmos Environment Variables\n")
            f.write("GOOGLE_API_KEY=your-gemini-api-key-here\n")
            f.write("FLASK_SECRET_KEY=career_cosmos_secret_key_2024\n")
            f.write("FLASK_ENV=development\n")
        
        print(f"✓ Created {env_file} file. Please update with your API keys.")
    else:
        print(f"✓ {env_file} already exists.")

def main():
    """Main setup function"""
    print("🚀 Setting up Career Cosmos ATS Tracker...")
    print("=" * 60)
    
    # Create directories
    print("\n1. Creating directories...")
    create_directories()
    
    # Check dependencies
    print("\n2. Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and run setup again.")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    
    # Setup database
    print("\n3. Setting up database...")
    if not setup_database():
        print("❌ Database setup failed!")
        sys.exit(1)
    
    # Setup environment
    print("\n4. Setting up environment...")
    setup_environment()
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update your Google Gemini API key in the .env file or set GOOGLE_API_KEY environment variable")
    print("2. Run the application: python app.py")
    print("3. Open your browser to http://localhost:5000")
    print("4. Register a new account and start analyzing resumes!")
    print("\n🌟 Enjoy using Career Cosmos ATS Tracker!")

if __name__ == "__main__":
    main()
