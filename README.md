# 🎯 Code Arena — Battle. Learn. Build. 🛡️⚔️

A focused platform for practicing algorithms, taking quizzes, debugging code, and forming hackathon teams — all in one Arena.

---

Highlights
- Clean LeetCode-like problem solving experience with an in-browser editor
- Two quiz modes: Python MCQs and Debugging (patch selection)
- Hackathon teammate finder: search users by skills and contact via email
- Responsive UI and extensible architecture

Table of Contents
- About
- Core Features
- Quiz Modes
- Hackathon Team Finder
- Tech Stack (your stack)
- Getting Started (local)
- Contributing
- Roadmap
- License & Contact

About
-----
Code Arena combines problem-solving workflows with focused learning tools and team-finding features to help coders practice, learn, and form teams quickly.

Core Features
- 🔐 Authentication: Sign up, log in, password reset
- 👤 Profiles: Add bio, skills, email, avatar
- 📚 Problem Browser: Filter by difficulty, tags, and status (solved/attempted)
- 🧪 Editor: Run tests, custom input, submit, and view results
- 🧠 Quizzes:
  - MCQ (Python-focused): conceptual checks with immediate feedback
  - Debugging (patch selection): pick the correct code fix for buggy snippets
- 🤝 Hackathon Finder: Search users by skill tags and contact via the email on their profile

Quiz Modes
-----------
1. MCQ (Python)
   - Short conceptual questions (single/multi-select)
   - Immediate feedback and explanations

2. Debugging (Choose the Fix)
   - A buggy snippet is shown with candidate fixes
   - Choose the correct replacement to fix the bug

Hackathon Team Finder
---------------------
- Add skills to your profile (e.g., "HTML", "CSS", "Bootstrap", "Django")
- Search by skill tags to find candidates
- View matching users with skill overlap and contact email
- Save favorites for team formation (future: in-app invites)

Tech Stack (your stack)
-----------------------
- Frontend: plain HTML, CSS, Bootstrap, JavaScript (Vanilla JS)
  - Pages served as Django templates or static HTML depending on structure
  - Bootstrap for responsive UI and components
  - Optional: integrate a richer editor (CodeMirror / Monaco) if desired
- Backend: Django (Python)
  - REST endpoints (Django REST Framework optional) to serve problems, quizzes, users
  - Django templates for server-rendered pages if preferred
- Database: PostgreSQL (recommended) or SQLite for quick dev
- Runner: Secure, isolated code execution service (Dockerized worker recommended)
- Optional: Redis for caching/queues, Celery for background tasks (grading, queueing jobs)

Getting Started — Local Development (Django + static frontend)
-------------------------------------------------------------
This section is tailored to your stack: HTML/CSS/Bootstrap/JS frontend and Django backend.

Prerequisites
- Python 3.8+ and pip
- Node.js + npm (only if you build frontend assets or use tooling)
- PostgreSQL (or use SQLite for development)
- Docker (optional but recommended for a secure code runner)
- virtualenv or venv

Quick local setup (example)
1. Clone the repo
   git clone https://github.com/Nivapatel10/Code_Arena.git
   cd Code_Arena

2. Create and activate a virtual environment
   python -m venv venv
   # macOS / Linux
   source venv/bin/activate
   # Windows (PowerShell)
   .\venv\Scripts\Activate.ps1

3. Install Python dependencies
   cd server  # or wherever manage.py is located
   pip install -r requirements.txt

4. Environment variables
   - Create a `.env` file or export variables. Suggested entries:
     - SECRET_KEY=replace_with_secure_random
     - DEBUG=True
     - DATABASE_URL=postgres://user:pass@localhost:5432/code_arena
     - ALLOWED_HOSTS=localhost,127.0.0.1
     - EMAIL_HOST / EMAIL_PORT (if using email)
     - CODE_RUNNER_URL=http://localhost:5000

   If you use django-environ or python-dotenv, add `.env` to `.gitignore`.

5. Database setup & migrations
   python manage.py migrate
   python manage.py loaddata initial_data.json  # optional seed data

6. Create a superuser (admin)
   python manage.py createsuperuser

7. Static files
   - In development, Django serves static files.
   - For production, run:
     python manage.py collectstatic

8. Run the development server
   python manage.py runserver

Frontend notes (HTML/CSS/Bootstrap/JS)
- Use Django templates (server/templates/) and static files (server/static/) for HTML/CSS/JS.
- Load Bootstrap via CDN or local vendor files.
- Implement code editor UI with a <textarea> or integrate CodeMirror/Monaco for better UX. The editor should POST code to a secure API endpoint for execution.

Runner (Code Execution) — safety first
- Never execute arbitrary user code on the main host. Use an isolated service (Docker container per job or sandboxing tool).
- Runner receives code + language + stdin + tests, executes with time & memory limits, and returns results.
- Queue runner jobs (Celery) and persist results to avoid blocking web requests.

Testing
- Place tests under server/tests/
- Run tests with:
  python manage.py test

Environment and Deployment
- For production, set DEBUG=False, configure ALLOWED_HOSTS, use PostgreSQL, and set up HTTPS via nginx + gunicorn/daphne
- Use environment variables for secrets (do not commit them)
- Add a CI workflow to run tests and linting on PRs

Contributing
------------
We welcome contributors! Suggested flow:
1. Fork the repo
2. Create branch: git checkout -b feat/awesome-thing
3. Implement changes, add tests and documentation
4. Open a PR with description and screenshots for UI changes

Please include:
- Clear PR description
- Screenshots for UI changes (if applicable)
- Tests where appropriate

Roadmap
-------
- In-app messaging / team invites
- Team rooms and shared boards
- Leaderboards, badges, streaks
- More language support and runner improvements

License & Contact
-----------------
Add a LICENSE file (MIT recommended).

- Repo: https://github.com/Nivapatel10/Code_Arena
- Owner: Nivapatel10

Made with ❤️ & ⚔️ — sharpen your skills and build great teams.

Crossed Swords ASCII mini-logo (updated)

     />===================================>\
    (   C O D E   A R E N A   —  F I G H T  )
     \>===================================>/
