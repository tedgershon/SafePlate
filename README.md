# SafePlate
NOVA 2025 Gen AI Hackathon Project (airia agentic track)

An AI-powered recipe generator which combines cuisine preferences, known allergies, and ingredients on hand to craft a custom meal for you and your friends. SafePlate uses multi-agent orchestration via [Airia](https://airia.com/) to ensure recipe safety through automated validation and retry mechanisms.

## Tech Stack

- **Backend:** Django 5.2.8
- **Database:** SQLite
- **AI Agents:** Airia Multi-Agent System (OpenAI GPT-4.1, Claude 4 Sonnet)
- **Testing:** Django TestCase
- **Python:** 3.12.4

## Setup

### Prerequisites
- Python 3.12.4 (or compatible version)
- Git


### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/tedgershon/SafePlate.git
   cd SafePlate
   ```

2. **Create and activate virtual environment**

   **Windows (PowerShell):**
   ```powershell
   python -m venv .venv
   . .\.venv\Scripts\Activate.ps1
   ```
   
   **Windows (Command Prompt):**
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate.bat
   ```
   
   **macOS/Linux:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   *Note: If you encounter a PowerShell execution policy error, run:*
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

### Running the Development Server

Start the Django development server:
```bash
python manage.py runserver
```

The application will be available at: **http://127.0.0.1:8000/**

### Running Tests

Run the complete test suite (37 tests):
```bash
python manage.py test recipes
```

**Test options:**
- Compact output: `python manage.py test recipes --verbosity=1`
- Detailed output: `python manage.py test recipes --verbosity=2`
- Specific test class: `python manage.py test recipes.tests.ChefAgentTest`
- Specific test: `python manage.py test recipes.tests.ChefAgentTest.test_chef_uses_provided_ingredients`

### Quick Demo

1. Navigate to http://127.0.0.1:8000/
2. Try this example to see the full workflow:
   - **Cuisine Type:** Italian
   - **Allergies:** nuts
   - **Ingredients:** chicken, tomatoes, basil
3. Click "Generate Safe Recipe"
4. Observe the multi-agent workflow:
   - First attempt generates unsafe "Pesto Pasta" (contains pine nuts)
   - Inspector agent catches the violation
   - System automatically retries and generates a safe alternative
   - All attempts are displayed for transparency

## Project Structure

```
SafePlate/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (Airia API keys)
├── .gitignore                # Git ignore rules
├── db.sqlite3                # SQLite database
├── recipes/                  # Main Django app
│   ├── models.py           # Database models (RecipeRequest, GeneratedRecipe)
│   ├── views.py            # Business logic & agent orchestration
│   ├── forms.py            # Form definitions
│   ├── tests.py            # Test suite (37 tests)
│   ├── urls.py             # URL routing
│   ├── admin.py            # Django admin configuration
│   ├── apps.py             # App configuration
│   ├── migrations/         # Database migrations
│   ├── static/             # Static files (logos, CSS)
│   └── templates/          # HTML templates
└── safeplate_project/        # Django project settings
    ├── settings.py         # Project configuration
    ├── urls.py             # Main URL configuration
    ├── wsgi.py             # WSGI server configuration
    └── asgi.py             # ASGI server configuration
```
