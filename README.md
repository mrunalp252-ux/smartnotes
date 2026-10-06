# SmartNotes

> **"Capture. Organize. Remember."**

SmartNotes is a modern, lightweight, and responsive Notes Management Web Application designed for students and developers. Built with Python Flask, SQLAlchemy, modern CSS, and Vanilla JavaScript, SmartNotes provides an intuitive interface to capture thoughts, lecture points, code snippets, and project ideas with persistent storage and seamless serverless cloud deployment.

---

## 📌 Features

- **📊 Dashboard & Metrics**: Real-time counter of total notes, pinned notes, and active categories.
- **📌 Priority Pinning**: Pin crucial notes so they stay highlighted at the top of the grid.
- **🏷️ Structured Categories**: Organize notes into predefined categories:
  - *Personal*, *College*, *Programming*, *Projects*, *Ideas*, *Other*
- **🔍 Instant Search & Filtering**: Fast search across titles, note content, and categories, plus one-click category filter pills.
- **📝 Complete CRUD Lifecycle**: Clean, validated forms for creating, editing, and updating notes.
- **🛡️ Safe Delete Confirmation**: Built-in modal dialog to prevent accidental deletion.
- **🌓 Dark / Light Mode**: Seamless theme switching with persistent user preference via `localStorage`.
- **⚡ College Demo Seed Data**: One-click demo button to instantly populate sample college & programming notes.
- **📱 Fully Responsive**: Optimized layouts for mobile, tablet, laptop, and desktop displays.
- **🚀 Serverless Ready**: Architected for Vercel deployment with support for managed PostgreSQL (Neon / Vercel Postgres) and local SQLite fallback.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11, Flask 3.0, Flask-SQLAlchemy, Werkzeug, Jinja2
- **Database**:
  - Local: SQLite (`sqlite:///smartnotes.db`)
  - Production: Serverless PostgreSQL (Neon / Vercel Postgres / Supabase via `DATABASE_URL`)
- **Frontend**: HTML5, Vanilla CSS3 (Custom Design System, CSS Variables, Flexbox/Grid), Vanilla JavaScript (ES6+)
- **Deployment**: Vercel Serverless Functions (`@vercel/python`)
- **Version Control**: Git & GitHub

---

## 📂 Project Structure

```text
smartnotes/
│
├── app.py                  # Core Flask application, SQLAlchemy models, and route controllers
├── test_smartnotes.py      # Automated unit & integration test suite
├── requirements.txt        # Python package dependencies
├── vercel.json             # Vercel deployment & routing configuration
├── .env.example            # Sample environment variables reference
├── .gitignore              # Git ignored patterns (venv, .env, __pycache__, etc.)
├── README.md               # Project documentation
│
├── api/
│   └── index.py            # Vercel serverless WSGI entry point
│
├── templates/
│   ├── base.html           # Base layout (Navbar, Theme switch, Toasts, Delete modal, Footer)
│   ├── index.html          # Main dashboard (Stats, Search, Filter pills, Note cards, Empty state)
│   ├── create_note.html    # Note creation form with validation
│   ├── edit_note.html      # Note update form with metadata
│   ├── 404.html            # User-friendly 404 Not Found page
│   └── 500.html            # User-friendly 500 Internal Error page
│
└── static/
    ├── css/
    │   └── style.css       # Responsive styling, light/dark mode CSS tokens, card layouts
    └── js/
        └── script.js       # Theme toggle, modal controls, AJAX pin toggle, character counter
```

---

## 💻 Local Installation (Windows)

Follow these exact steps to run SmartNotes on Windows:

### 1. Clone or Open the Project
```powershell
cd "c:\Users\ADMIN\OneDrive\Desktop\notes app"
```

### 2. Create and Activate Virtual Environment
```powershell
# Create virtual environment
py -m venv venv

# Activate on Windows PowerShell
.\venv\Scripts\Activate.ps1

# (Or Command Prompt: venv\Scripts\activate.bat)
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. (Optional) Set Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
*(If `DATABASE_URL` is left blank, SmartNotes will automatically create a local `smartnotes.db` SQLite database).*

---

## 🏃 Running the Application

### Start Flask Development Server
```powershell
python app.py
```
Or with the Windows Python launcher:
```powershell
py app.py
```

The application will start at:
```text
http://127.0.0.1:5000
```

Open your browser and navigate to `http://127.0.0.1:5000` to start capturing notes!

---

## 🧪 Running Automated Tests

A comprehensive test suite is included covering routes, CRUD operations, validations, search, filtering, pin toggling, and demo seeding:

```powershell
.\venv\Scripts\python.exe test_smartnotes.py
```

---

## 🗄️ Database Setup & Configuration

SmartNotes dynamically detects its database environment:

- **Local Mode (Default)**: If `DATABASE_URL` is omitted, the app initializes a local SQLite file (`smartnotes.db`) in the project directory.
- **Production Mode (Vercel / Cloud)**: Set the `DATABASE_URL` environment variable to a managed PostgreSQL instance (such as Neon, Vercel Postgres, or Supabase):
  ```text
  DATABASE_URL=postgresql://user:password@ep-sample-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
  ```
  The app automatically handles `postgres://` to `postgresql://` URI translation and executes `db.create_all()` safely on startup.

---

## 🚀 Vercel Deployment Guide

SmartNotes is pre-configured with `vercel.json` and `api/index.py` for direct deployment:

### Option A: Deploy via GitHub (Recommended for Teams)
1. Push this repository to GitHub (see instructions below).
2. Go to [vercel.com](https://vercel.com) and log in.
3. Click **"Add New..."** -> **"Project"**.
4. Import your `smartnotes` GitHub repository.
5. In **Environment Variables**, add:
   - `DATABASE_URL`: Your serverless PostgreSQL connection string (from Neon, Supabase, or Vercel Postgres).
   - `SECRET_KEY`: A random secure string.
6. Click **Deploy**. Vercel will build and host your Flask app automatically!

### Option B: Deploy via Vercel CLI
```powershell
# Log into your Vercel account
npx vercel login

# Deploy to preview
npx vercel

# Deploy to production
npx vercel --prod
```

---

## 🐙 GitHub Version Control

To push to your GitHub account:

```powershell
# Initialize repository (if not already initialized)
git init

# Stage all files
git add .

# Create initial commit
git commit -m "Initial commit: SmartNotes Flask application"

# Add your GitHub remote repository
git remote add origin https://github.com/mrunalp252-ux/smartnotes.git

# Set main branch and push
git branch -M main
git push -u origin main
```

*(Note: Secrets and local databases are protected via `.gitignore`).*

---

## 🔮 Future Enhancements

- 🏷️ Custom user-defined category tags and color pickers.
- 📤 Markdown live preview with syntax highlighting for code blocks.
- 📥 Export notes to PDF and Markdown files.
- ⏰ Reminder notifications and due dates.
