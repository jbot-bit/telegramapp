#!/usr/bin/env python3
"""
Validation script for Vouch Portal
Checks that all required files exist and are properly structured
"""

import os
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Define expected file structure
REQUIRED_FILES = {
    'main.py': 'FastAPI application',
    'bot.py': 'Telegram bot handlers',
    'database.py': 'Database connection and schema',
    'requirements.txt': 'Python dependencies',
    '.env.example': 'Environment variables template',
    'README.md': 'Documentation',
    'SETUP_GUIDE.md': 'Setup instructions',
    '.replit': 'Replit configuration',
    'pyproject.toml': 'Project metadata',
    'webapp/index.html': 'WebApp frontend',
    'webapp/static/styles.css': 'CSS styling',
    'webapp/static/main.js': 'JavaScript client',
}

REQUIRED_ENV_VARS = [
    'BOT_TOKEN',
    'BOT_USERNAME',
    'WEBHOOK_URL',
    'ADMIN_ID',
    'DATABASE_URL',
]

def check_file_exists(filepath):
    """Check if a file exists"""
    return Path(filepath).exists()

def check_file_not_empty(filepath):
    """Check if a file has content"""
    try:
        return Path(filepath).stat().st_size > 0
    except:
        return False

def validate_structure():
    """Validate the project structure"""
    print("🔍 Validating Vouch Portal project structure...\n")

    all_good = True

    # Check files
    print("📁 Checking required files:")
    for filepath, description in REQUIRED_FILES.items():
        exists = check_file_exists(filepath)
        not_empty = check_file_not_empty(filepath) if exists else False

        if exists and not_empty:
            print(f"  ✅ {filepath:30} - {description}")
        elif exists and not not_empty:
            print(f"  ⚠️  {filepath:30} - File is empty!")
            all_good = False
        else:
            print(f"  ❌ {filepath:30} - MISSING!")
            all_good = False

    # Check Python syntax
    print("\n🐍 Checking Python files syntax:")
    python_files = ['main.py', 'bot.py', 'database.py']
    for pyfile in python_files:
        if check_file_exists(pyfile):
            try:
                with open(pyfile, 'r', encoding='utf-8') as f:
                    compile(f.read(), pyfile, 'exec')
                print(f"  ✅ {pyfile:30} - Valid Python syntax")
            except SyntaxError as e:
                print(f"  ❌ {pyfile:30} - Syntax error: {e}")
                all_good = False
        else:
            print(f"  ⏭️  {pyfile:30} - File not found (skipped)")

    # Check .env.example
    print("\n🔧 Checking environment variables template:")
    if check_file_exists('.env.example'):
        with open('.env.example', 'r') as f:
            env_content = f.read()

        for var in REQUIRED_ENV_VARS:
            if var in env_content:
                print(f"  ✅ {var:30} - Present in template")
            else:
                print(f"  ❌ {var:30} - MISSING from template!")
                all_good = False
    else:
        print("  ❌ .env.example file not found!")
        all_good = False

    # Check requirements.txt
    print("\n📦 Checking dependencies:")
    required_packages = [
        'fastapi',
        'uvicorn',
        'python-telegram-bot',
        'asyncpg',
        'pydantic',
    ]

    if check_file_exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            requirements = f.read().lower()

        for package in required_packages:
            if package in requirements:
                print(f"  ✅ {package:30} - Listed")
            else:
                print(f"  ❌ {package:30} - MISSING!")
                all_good = False
    else:
        print("  ❌ requirements.txt not found!")
        all_good = False

    # Check HTML structure
    print("\n🌐 Checking HTML structure:")
    if check_file_exists('webapp/index.html'):
        with open('webapp/index.html', 'r', encoding='utf-8') as f:
            html = f.read()

        html_checks = {
            'Telegram WebApp script': 'telegram-web-app.js' in html,
            'Profile tab': 'profile-tab' in html,
            'Vouch tab': 'vouch-tab' in html,
            'Community tab': 'community-tab' in html,
            'Styles CSS': 'styles.css' in html,
            'Main JS': 'main.js' in html,
        }

        for check, result in html_checks.items():
            if result:
                print(f"  ✅ {check:30}")
            else:
                print(f"  ❌ {check:30} - MISSING!")
                all_good = False
    else:
        print("  ❌ webapp/index.html not found!")
        all_good = False

    # Final summary
    print("\n" + "="*60)
    if all_good:
        print("✅ All checks passed! Your project structure is valid.")
        print("\n📝 Next steps:")
        print("  1. Copy .env.example to .env and fill in your values")
        print("  2. Install dependencies: pip install -r requirements.txt")
        print("  3. Set up your PostgreSQL database")
        print("  4. Run the app: python main.py")
        print("  5. Set your webhook URL with Telegram")
        print("\n📖 See SETUP_GUIDE.md for detailed instructions")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\n💡 Tip: Make sure you have all files from the repository")
        return 1

if __name__ == '__main__':
    try:
        exit_code = validate_structure()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏸️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)
