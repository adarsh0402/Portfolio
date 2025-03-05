import os
import json
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from werkzeug.utils import secure_filename
import db

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for flash messages and sessions
ADMIN_PASSWORD = 'admin123'  # In production, use environment variable

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'resumes')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    portfolio = db.get_current_portfolio()
    if portfolio:
        return render_template('index.html', 
                             title=portfolio['title'],
                             about=portfolio['about'],
                             projects=portfolio['projects'],
                             skills=portfolio['skills'],
                             education=portfolio['education'],
                             achievements=portfolio['achievements'],
                             resume_filename=portfolio['resume_filename'])
    return "Portfolio not found", 404

@app.route('/admin_login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    if password == ADMIN_PASSWORD:
        session['is_admin'] = True
        return redirect(request.args.get('next') or url_for('home'))
    flash('Invalid password', 'error')
    return redirect(url_for('home'))

@app.route('/admin_logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('home'))

from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Please login as admin first', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/update_portfolio', methods=['GET', 'POST'])
@admin_required
def update_portfolio():
    if request.method == 'POST':
        try:
            # Get form data
            title = request.form['title']
            about = request.form['about']
            
            # Parse projects data
            projects = []
            project_titles = request.form.getlist('project_title[]')
            project_descriptions = request.form.getlist('project_description[]')
            project_technologies = request.form.getlist('project_technologies[]')
            project_images = request.form.getlist('project_image[]')
            
            for i in range(len(project_titles)):
                projects.append({
                    'title': project_titles[i],
                    'description': project_descriptions[i],
                    'technologies': project_technologies[i].split(','),
                    'image': project_images[i]
                })
            
            # Parse skills data
            skills = {
                'Programming Languages': request.form['programming_languages'].split(','),
                'Databases': request.form['databases'].split(','),
                'Web Technologies': request.form['web_technologies'].split(','),
                'DevOps & Tools': request.form['devops_tools'].split(',')
            }
            
            # Parse education data
            education = {
                'degree': request.form['education_degree'],
                'institution': request.form['education_institution'],
                'cgpa': request.form['education_cgpa'],
                'duration': request.form['education_duration']
            }
            
            # Parse achievements
            achievements = request.form.getlist('achievements[]')
            
            # Handle resume file upload
            resume_filename = None
            if 'resume' in request.files:
                file = request.files['resume']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    resume_filename = filename
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Update portfolio
            db.update_portfolio(
                title=title,
                about=about,
                projects=projects,
                skills=skills,
                education=education,
                achievements=achievements,
                resume_filename=resume_filename,
                change_title=request.form.get('change_title')
            )
            
            flash('Portfolio updated successfully!', 'success')
            return redirect(url_for('home'))
            
        except Exception as e:
            flash(f'Error updating portfolio: {str(e)}', 'error')
            return redirect(url_for('update_portfolio'))
    
    # GET request - show the update form
    portfolio = db.get_current_portfolio()
    return render_template('update_portfolio.html', portfolio=portfolio)

@app.route('/change_logs')
@admin_required
def change_logs():
    logs = db.get_change_logs()
    return render_template('change_logs.html', logs=logs)

@app.route('/restore/<int:log_id>', methods=['POST'])
@admin_required
def restore_portfolio(log_id):
    try:
        db.restore_portfolio(log_id)
        flash('Portfolio restored successfully!', 'success')
    except Exception as e:
        flash(f'Error restoring portfolio: {str(e)}', 'error')
    return redirect(url_for('change_logs'))

@app.route('/download_resume')
def download_resume():
    portfolio = db.get_current_portfolio()
    if portfolio and portfolio['resume_filename']:
        try:
            return send_from_directory(
                app.config['UPLOAD_FOLDER'],
                portfolio['resume_filename'],
                as_attachment=True
            )
        except Exception as e:
            flash(f'Error downloading resume: {str(e)}', 'error')
            return redirect(url_for('home'))
    flash('No resume available', 'error')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
