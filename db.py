import sqlite3
import json
from datetime import datetime, timezone
import os

DB_PATH = 'portfolio.db'

def get_db_connection():
    """Create a database connection and return the connection object"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    try:
        # Create portfolio table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                about TEXT NOT NULL,
                projects TEXT NOT NULL,
                skills TEXT NOT NULL,
                education TEXT NOT NULL,
                achievements TEXT NOT NULL,
                resume_filename TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create change_logs table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS change_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                change_title TEXT,
                details TEXT NOT NULL,
                change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert initial data if portfolio table is empty
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM portfolio')
        if cursor.fetchone()[0] == 0:
            initial_data = {
                'title': 'Full Stack Developer',
                'about': '''Experienced PHP Developer and Full Stack Engineer with a strong background in creating scalable, high-performance applications and optimizing code quality. Skilled in conducting code reviews, collaborating across teams, and validating technical solutions for robustness.

Proficient in PHP, Git version control, and Agile practices, with a focus on delivering efficient, secure, and maintainable solutions. With over 3 years of experience at Diverta Inc., Tokyo, I've consistently delivered high-quality solutions and maintained a client satisfaction rate of 83%.''',
                'resume_filename': 'sample_resume.pdf',
                'projects': json.dumps([
                    {
                        'title': 'KUROCO Headless CMS',
                        'description': 'Developed and optimized PHP-based REST APIs for KUROCO, a headless CMS, using Swagger for documentation. Enhanced API usability and maintainability, leading to faster client integrations.',
                        'technologies': ['PHP', 'REST API', 'Swagger', 'MySQL'],
                        'image': 'https://raw.githubusercontent.com/diverta/kuroco-front-nuxt/master/assets/logo.png'
                    },
                    {
                        'title': 'RCMS Query Optimization',
                        'description': 'Executed query optimization techniques for RCMS through index creation, caching, and query restructuring, resulting in 40% improvement in query performance.',
                        'technologies': ['PHP', 'MySQL', 'Caching', 'Performance Optimization'],
                        'image': 'https://www.diverta.co.jp/wp-content/uploads/2020/07/rcms-logo.png'
                    },
                    {
                        'title': 'AWS Cloud Infrastructure',
                        'description': 'Implemented AWS services including S3, Load Balancer, Lambda, EC2, and ElastiCache, enhancing technical integration and scalability of cloud solutions.',
                        'technologies': ['AWS', 'DevOps', 'Cloud Architecture', 'Load Balancing'],
                        'image': 'https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg'
                    }
                ]),
                'skills': json.dumps({
                    'Programming Languages': ['Python', 'PHP', 'JavaScript', 'C'],
                    'Databases': ['MySQL', 'PostgreSQL', 'SQLite'],
                    'Web Technologies': ['HTML', 'CSS', 'Bootstrap', 'Tailwind CSS', 'Ajax', 'REST API'],
                    'DevOps & Tools': ['AWS', 'Docker', 'Git', 'Postman', 'Confluence']
                }),
                'education': json.dumps({
                    'degree': 'B.Tech. in Information Technology',
                    'institution': 'Sathyabama Institute of Science and Technology, Chennai',
                    'cgpa': '7.62',
                    'duration': 'July 2016 - May 2020'
                }),
                'achievements': json.dumps([
                    'Received Outgoing Student Excellence Award (SIST 2020)',
                    'Delivered a training seminar on Artificial Intelligence & LLM to around 200 students (VIT 2023)',
                    'Awarded with Silver Medal in Data Mining Course and Exam (NPTEL 2019)'
                ])
            }

            conn.execute('''
                INSERT INTO portfolio (title, about, projects, skills, education, achievements)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                initial_data['title'],
                initial_data['about'],
                initial_data['projects'],
                initial_data['skills'],
                initial_data['education'],
                initial_data['achievements']
            ))

        conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
    finally:
        conn.close()

def get_current_portfolio():
    """Retrieve current portfolio details"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        portfolio = cursor.execute('SELECT * FROM portfolio ORDER BY id DESC LIMIT 1').fetchone()
        if portfolio:
            return {
                'id': portfolio['id'],
                'title': portfolio['title'],
                'about': portfolio['about'],
                'projects': json.loads(portfolio['projects']),
                'skills': json.loads(portfolio['skills']),
                'education': json.loads(portfolio['education']),
                'achievements': json.loads(portfolio['achievements']),
                'resume_filename': portfolio['resume_filename'],
                'updated_at': portfolio['updated_at']
            }
        return None
    finally:
        conn.close()

def update_portfolio(title, about, projects, skills, education, achievements, resume_filename=None, change_title=None):
    """Update portfolio details and create a change log entry"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Update portfolio
        if resume_filename:
            cursor.execute('''
                UPDATE portfolio 
                SET title=?, about=?, projects=?, skills=?, education=?, achievements=?, resume_filename=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=(SELECT id FROM portfolio ORDER BY id DESC LIMIT 1)
            ''', (title, about, json.dumps(projects), json.dumps(skills), json.dumps(education), json.dumps(achievements), resume_filename))
        else:
            cursor.execute('''
                UPDATE portfolio 
                SET title=?, about=?, projects=?, skills=?, education=?, achievements=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=(SELECT id FROM portfolio ORDER BY id DESC LIMIT 1)
            ''', (title, about, json.dumps(projects), json.dumps(skills), json.dumps(education), json.dumps(achievements)))

        # Create change log entry
        details = {
            'title': title,
            'about': about,
            'projects': projects,
            'skills': skills,
            'education': education,
            'achievements': achievements,
            'resume_filename': resume_filename
        }
        
        cursor.execute('''
            INSERT INTO change_logs (change_title, details, change_date)
            VALUES (?, ?, datetime('now'))
        ''', (change_title, json.dumps(details)))

        conn.commit()
    finally:
        conn.close()

def get_change_logs():
    """Retrieve all change log entries"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        logs = cursor.execute('SELECT * FROM change_logs ORDER BY change_date DESC').fetchall()
        return [{
            'log_id': log['log_id'],
            'change_title': log['change_title'],
            'details': json.loads(log['details']),
            'change_date': log['change_date']
        } for log in logs]
    finally:
        conn.close()

def restore_portfolio(log_id):
    """Restore portfolio to a previous version from change logs"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get the historical version
        log = cursor.execute('SELECT * FROM change_logs WHERE log_id = ?', (log_id,)).fetchone()
        if not log:
            raise ValueError("Log entry not found")

        details = json.loads(log['details'])
        
        # Update current portfolio with historical data
        if details.get('resume_filename'):
            cursor.execute('''
                UPDATE portfolio 
                SET title=?, about=?, projects=?, skills=?, education=?, achievements=?, resume_filename=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=(SELECT id FROM portfolio ORDER BY id DESC LIMIT 1)
            ''', (
                details['title'],
                details['about'],
                json.dumps(details['projects']),
                json.dumps(details['skills']),
                json.dumps(details['education']),
                json.dumps(details['achievements']),
                details['resume_filename']
            ))
        else:
            cursor.execute('''
                UPDATE portfolio 
                SET title=?, about=?, projects=?, skills=?, education=?, achievements=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=(SELECT id FROM portfolio ORDER BY id DESC LIMIT 1)
            ''', (
                details['title'],
                details['about'],
                json.dumps(details['projects']),
                json.dumps(details['skills']),
                json.dumps(details['education']),
                json.dumps(details['achievements'])
            ))

        # Create a new change log entry for the restoration
        cursor.execute('''
            INSERT INTO change_logs (change_title, details)
            VALUES (?, ?)
        ''', (f"Restored from version {log_id}", json.dumps(details)))

        conn.commit()
    finally:
        conn.close()

# Initialize the database when the module is imported
if not os.path.exists(DB_PATH):
    init_db()
