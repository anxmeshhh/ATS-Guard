import sqlite3
import os
from datetime import datetime

def create_database():
    """Initialize the ATS Tool database with all required tables"""
    
    # Ensure the database directory exists
    db_path = 'ats_tool.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Users table with enhanced fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            profile_picture TEXT
        )
    ''')
    
    # Analysis history table with enhanced tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT,
            file_size INTEGER,
            ats_score INTEGER NOT NULL,
            keyword_score INTEGER,
            format_score INTEGER,
            content_score INTEGER,
            length_score INTEGER,
            keywords_matched INTEGER NOT NULL,
            total_keywords INTEGER NOT NULL,
            matched_keywords TEXT,
            missing_keywords TEXT,
            job_description_hash TEXT,
            analysis_data TEXT,
            ai_suggestions TEXT,
            processing_time REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # User preferences table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            theme TEXT DEFAULT 'dark',
            email_notifications BOOLEAN DEFAULT 1,
            analysis_reminders BOOLEAN DEFAULT 1,
            export_format TEXT DEFAULT 'pdf',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Job descriptions cache table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            company TEXT,
            description TEXT NOT NULL,
            description_hash TEXT UNIQUE,
            keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # System statistics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_analyses INTEGER DEFAULT 0,
            total_users INTEGER DEFAULT 0,
            avg_ats_score REAL DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_user_id ON analysis_history(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_created_at ON analysis_history(created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_desc_hash ON job_descriptions(description_hash)')
    
    # Insert initial system stats
    cursor.execute('''
        INSERT OR IGNORE INTO system_stats (id, total_analyses, total_users, avg_ats_score)
        VALUES (1, 0, 0, 0.0)
    ''')
    
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")
    print(f"Database created at: {os.path.abspath(db_path)}")

if __name__ == "__main__":
    create_database()
