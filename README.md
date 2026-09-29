# Our Little World — Raj ❤️ Ashmita

This is a simple and romantic Flask web app for two people to share memories, messages, music, food wishes, mood notes, and locations in a private personal space.

## Project structure

```text
raj-asmita-love/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── .env
├── README.md
├── instance/
│   └── love.db
├── uploads/
│   └── photos/
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── images/
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── dashboard.html
│   ├── gallery.html
│   ├── messages.html
│   ├── music.html
│   ├── mood.html
│   ├── food.html
│   ├── mood_swings.html
│   └── location.html
└── .venv/
```

## Step 1: Install Python

Download Python from:

https://www.python.org/downloads/

During installation, make sure to check:

- Add Python to PATH

Then confirm it is installed:

```bash
python --version
```

## Step 2: Install VS Code

Download VS Code:

https://code.visualstudio.com/

Then open VS Code.

## Step 3: Open the project folder

In VS Code, click:

- File
- Open Folder
- Select the folder containing this project

## Step 4: Open the terminal in VS Code

Press:

- Ctrl + `

or use:

- Terminal > New Terminal

## Step 5: Create a virtual environment

Run this command:

```bash
python -m venv .venv
```

## Step 6: Activate the virtual environment

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the script, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

On Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

## Step 7: Install dependencies

```bash
pip install -r requirements.txt
```

## Step 8: Create your environment file

Copy the example file:

```bash
copy .env.example .env
```

Then edit `.env` and set the values, for example:

```env
SECRET_KEY=generate-a-long-random-secret
DATABASE_URL=instance/love.db
DEFAULT_RAJ_PASSWORD=replace-with-a-strong-unique-password
DEFAULT_ASMITA_PASSWORD=replace-with-a-strong-unique-password
```

## Step 9: Initialize the database and create accounts

Run:

```bash
python app.py
```

The app will automatically create the SQLite database and the default users:

- Raj
  - username: raj
- Ashmita
  - username: asmita

Passwords are stored as password hashes using Werkzeug, not in plain text.

## Step 10: Run the Flask app

```bash
python app.py
```

If Flask is running successfully, you will see output similar to:

```text
* Running on http://127.0.0.1:5000
```

Open the browser and visit:

```text
http://127.0.0.1:5000
```

## Step 11: Login

Use:

- Username: raj
- Password: the value from `DEFAULT_RAJ_PASSWORD`

and then:

- Username: asmita
- Password: the value from `DEFAULT_ASMITA_PASSWORD`

## Important notes

- Do not commit the `.env` file.
- Keep your database in the `instance` folder.
- Uploaded photos are saved in `uploads/photos`.
- The app is ready to grow into a larger project later.

## Features included in this MVP

- Private login system
- Dashboard with sections
- Photo gallery upload and delete
- Private messages
- Music search and song history
- Mood vibe analyzer
- Food wish tracker
- Mood swing notes
- Location sharing with browser geolocation
- SQLite database structure with a clean modular layout

## Future ideas

- Relationship timeline
- Anniversary countdown
- Love letters
- Private chat
- Notifications
- Couple calendar
- Daily couple questions
- Voice messages
- Dark mode

## Security reminder

This project uses:

- password hashing
- session-based login
- login check for protected pages
- safe upload validation
- secure filename generation
- environment variables for secrets

## Troubleshooting

If you get an import error, run:

```bash
pip install -r requirements.txt
```

If the database is not created yet, start the app once and it will initialize automatically.

If the page does not load, check the terminal output for any error message.

---

Made with love for Raj and Ashmita.
