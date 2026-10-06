import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy

from urllib.parse import parse_qs, urlencode

# Load local environment variables if available
load_dotenv()

# Initialize Flask application with explicit template and static directories
basedir = os.path.abspath(os.path.dirname(__file__))
static_dir = os.path.join(basedir, 'static')
templates_dir = os.path.join(basedir, 'templates')

app = Flask(
    __name__,
    static_folder=static_dir,
    static_url_path='/static',
    template_folder=templates_dir
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'smartnotes-secret-key-prod-2026')

class VercelRouteMiddleware:
    """WSGI middleware ensuring correct PATH_INFO when Vercel rewrites requests to serverless entrypoints"""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = environ.get('QUERY_STRING', '')
        if '__route__' in qs:
            params = parse_qs(qs, keep_blank_values=True)
            if '__route__' in params:
                route = params.pop('__route__')[0]
                if not route.startswith('/'):
                    route = '/' + route
                environ['PATH_INFO'] = route
                environ['QUERY_STRING'] = urlencode(params, doseq=True)
        return self.wsgi_app(environ, start_response)

# Apply route middleware to Flask WSGI application
app.wsgi_app = VercelRouteMiddleware(app.wsgi_app)

# Production Database Strategy: Persistent PostgreSQL via DATABASE_URL
db_url = os.environ.get('DATABASE_URL')

if db_url:
    # Normalize postgres:// syntax for SQLAlchemy compatibility
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
else:
    # Fallback storage:
    # On Vercel serverless functions, the code directory is read-only.
    # We use writable /tmp for serverless runtime, or local directory for local development.
    if os.environ.get('VERCEL'):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/smartnotes.db'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'smartnotes.db')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Supported Categories
CATEGORIES = ['Personal', 'College', 'Programming', 'Projects', 'Ideas', 'Other']

# Note Model
class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Other')
    is_pinned = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Note {self.id}: {self.title}>"

# Idempotent database table initialization helper
_tables_initialized = False

def ensure_tables_exist():
    global _tables_initialized
    if not _tables_initialized:
        try:
            db.create_all()
            _tables_initialized = True
        except Exception as e:
            app.logger.warning(f"Database table verification notice: {e}")

# Ensure tables are ready on startup and on first incoming request
with app.app_context():
    ensure_tables_exist()

@app.before_request
def before_request_hook():
    # Make sure tables exist before handling database requests
    if not request.path.startswith('/static'):
        ensure_tables_exist()

# Context processor for templates
@app.context_processor
def inject_global_data():
    return {
        'all_categories': CATEGORIES,
        'current_year': datetime.utcnow().year,
        'has_persistent_db': bool(os.environ.get('DATABASE_URL')),
        'is_vercel': bool(os.environ.get('VERCEL'))
    }

# ----------------- STATIC ASSETS ROUTE ----------------- #

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static CSS, JS, and asset files reliably across all environments"""
    return send_from_directory(app.static_folder, filename)

# ----------------- HEALTH & DIAGNOSTIC ROUTE ----------------- #

@app.route('/api/health')
def health_check():
    """Diagnostic endpoint to verify serverless status, database connectivity, and configuration"""
    result = {
        'status': 'healthy',
        'is_vercel': bool(os.environ.get('VERCEL')),
        'has_database_url': bool(os.environ.get('DATABASE_URL')),
        'database_backend': 'PostgreSQL (Persistent)' if os.environ.get('DATABASE_URL') else 'SQLite'
    }
    try:
        count = Note.query.count()
        result['database_connected'] = True
        result['note_count'] = count
    except Exception as e:
        result['status'] = 'database_notice'
        result['database_connected'] = False
        result['error'] = str(e)
    return jsonify(result)

# ----------------- APPLICATION ROUTES ----------------- #

@app.route('/')
def home():
    """Redirect root path to notes dashboard"""
    return redirect(url_for('notes_dashboard'))

@app.route('/notes')
def notes_dashboard():
    """Main dashboard displaying notes, statistics, search, and filtering"""
    search_query = request.args.get('q', '').strip()
    selected_category = request.args.get('category', '').strip()

    query = Note.query

    # Apply search filter across title, content, and category
    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(
            (Note.title.ilike(search_filter)) |
            (Note.content.ilike(search_filter)) |
            (Note.category.ilike(search_filter))
        )

    # Apply category filter
    if selected_category and selected_category in CATEGORIES:
        query = query.filter(Note.category == selected_category)

    # Order pinned notes first, then latest updated
    notes = query.order_by(Note.is_pinned.desc(), Note.updated_at.desc()).all()

    # Overall stats for the dashboard header
    total_notes_count = Note.query.count()
    pinned_notes_count = Note.query.filter_by(is_pinned=True).count()
    active_categories_count = db.session.query(db.func.count(db.distinct(Note.category))).scalar() or 0

    return render_template(
        'index.html',
        notes=notes,
        total_count=total_notes_count,
        pinned_count=pinned_notes_count,
        category_count=active_categories_count,
        search_query=search_query,
        selected_category=selected_category
    )

@app.route('/notes/new', methods=['GET', 'POST'])
def create_note():
    """Create a new note with validation"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', 'Other').strip()
        is_pinned = bool(request.form.get('is_pinned'))

        if category not in CATEGORIES:
            category = 'Other'

        if not title:
            flash('Note title is required.', 'error')
            return render_template('create_note.html', title=title, content=content, category=category, is_pinned=is_pinned), 400

        if not content:
            flash('Note content is required.', 'error')
            return render_template('create_note.html', title=title, content=content, category=category, is_pinned=is_pinned), 400

        try:
            new_note = Note(
                title=title,
                content=content,
                category=category,
                is_pinned=is_pinned,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(new_note)
            db.session.commit()
            flash('Note created successfully!', 'success')
            return redirect(url_for('notes_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving note: {str(e)}', 'error')
            return render_template('create_note.html', title=title, content=content, category=category, is_pinned=is_pinned), 500

    return render_template('create_note.html', title='', content='', category='Personal', is_pinned=False)

@app.route('/notes/<int:note_id>/edit', methods=['GET', 'POST'])
def edit_note(note_id):
    """Edit an existing note"""
    note = db.session.get(Note, note_id)
    if not note:
        flash('Note not found or may have been deleted.', 'error')
        return redirect(url_for('notes_dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', 'Other').strip()
        is_pinned = bool(request.form.get('is_pinned'))

        if category not in CATEGORIES:
            category = 'Other'

        if not title:
            flash('Note title cannot be empty.', 'error')
            return render_template('edit_note.html', note=note), 400

        if not content:
            flash('Note content cannot be empty.', 'error')
            return render_template('edit_note.html', note=note), 400

        try:
            note.title = title
            note.content = content
            note.category = category
            note.is_pinned = is_pinned
            note.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Note updated successfully!', 'success')
            return redirect(url_for('notes_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating note: {str(e)}', 'error')
            return render_template('edit_note.html', note=note), 500

    return render_template('edit_note.html', note=note)

@app.route('/notes/<int:note_id>/delete', methods=['POST'])
def delete_note(note_id):
    """Delete a note with POST confirmation"""
    note = db.session.get(Note, note_id)
    if not note:
        flash('Note not found or already deleted.', 'error')
        return redirect(url_for('notes_dashboard'))

    try:
        db.session.delete(note)
        db.session.commit()
        flash('Note deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting note: {str(e)}', 'error')

    return redirect(url_for('notes_dashboard'))

@app.route('/notes/<int:note_id>/toggle-pin', methods=['POST'])
def toggle_pin(note_id):
    """Toggle pin status of a note"""
    note = db.session.get(Note, note_id)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')

    if not note:
        if is_ajax:
            return jsonify({'success': False, 'message': 'Note not found'}), 404
        flash('Note not found.', 'error')
        return redirect(url_for('notes_dashboard'))

    try:
        note.is_pinned = not note.is_pinned
        note.updated_at = datetime.utcnow()
        db.session.commit()

        if is_ajax:
            return jsonify({
                'success': True,
                'is_pinned': note.is_pinned,
                'message': 'Note pinned.' if note.is_pinned else 'Note unpinned.'
            })

        status_str = 'pinned' if note.is_pinned else 'unpinned'
        flash(f'Note {status_str} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        if is_ajax:
            return jsonify({'success': False, 'message': str(e)}), 500
        flash('Could not update pin status.', 'error')

    return redirect(url_for('notes_dashboard'))

@app.route('/seed-sample-notes', methods=['POST'])
def seed_sample_notes():
    """Populate sample notes for college demonstration"""
    sample_data = [
        {
            'title': 'Java DSA',
            'category': 'Programming',
            'content': 'Key Data Structures & Algorithms concepts:\n- Arrays & Dynamic Sizing\n- Singly & Doubly Linked Lists\n- Binary Search Trees & AVL balancing\n- Graphs: BFS, DFS, Dijkstra shortest path\n- Dynamic Programming: Knapsack, LCS, Memoization',
            'is_pinned': True
        },
        {
            'title': 'College Project Ideas',
            'category': 'Projects',
            'content': 'Innovative project concepts for the final semester presentation:\n1. SmartNotes - Modern cloud-ready note organizer\n2. AI Campus Assistant - Automated lab & class schedule guidance\n3. Peer Coding Platform - Live markdown & code snippet collaboration\n4. Smart Attendance System - Quick QR / biometric check-in',
            'is_pinned': True
        },
        {
            'title': 'Python Flask',
            'category': 'Programming',
            'content': 'Flask Architecture & Best Practices:\n- Application factories and modular Blueprints\n- Jinja2 templating with reusable layouts\n- SQLAlchemy ORM database models and migrations\n- Production deployment considerations on serverless platforms like Vercel',
            'is_pinned': False
        },
        {
            'title': 'Exam Preparation',
            'category': 'College',
            'content': 'Semester Exam Study Plan:\n- Computer Networks: OSI model, TCP/IP handshake, subnetting\n- Operating Systems: Process scheduling, semaphore deadlocks, paging\n- Database Management: Normalization forms (1NF, 2NF, 3NF, BCNF), indexing\n- Software Engineering: Agile sprints & UML class diagrams',
            'is_pinned': False
        }
    ]

    try:
        for item in sample_data:
            existing = Note.query.filter_by(title=item['title']).first()
            if not existing:
                note = Note(
                    title=item['title'],
                    category=item['category'],
                    content=item['content'],
                    is_pinned=item['is_pinned'],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.session.add(note)
        db.session.commit()
        flash('Sample notes populated successfully for college demonstration!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to load sample notes: {str(e)}', 'error')

    return redirect(url_for('notes_dashboard'))

# ----------------- ERROR HANDLERS ----------------- #

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Standalone local execution
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
