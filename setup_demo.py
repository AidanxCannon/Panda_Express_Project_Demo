#!/usr/bin/env python
"""
Setup script for Panda Express POS Demo
This script helps set up the project for demonstration purposes
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors gracefully"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}")
        print(f"Command: {command}")
        print(f"Error output: {e.stderr}")
        return None

def main():
    print("🐼 Panda Express POS - Demo Setup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("⚠️  Warning: Python 3.11+ recommended for best compatibility")
    
    # Create virtual environment if it doesn't exist
    venv_path = Path("venv")
    if not venv_path.exists():
        print("\n📦 Creating virtual environment...")
        run_command(f"{sys.executable} -m venv venv", "Virtual environment creation")
    else:
        print("\n✅ Virtual environment already exists")
    
    # Determine activation script based on OS
    if os.name == 'nt':  # Windows
        activate_script = "venv\\Scripts\\activate"
        python_exe = "venv\\Scripts\\python.exe"
        pip_exe = "venv\\Scripts\\pip.exe"
    else:  # Unix/Linux/macOS
        activate_script = "source venv/bin/activate"
        python_exe = "venv/bin/python"
        pip_exe = "venv/bin/pip"
    
    # Install requirements
    if run_command(f"{pip_exe} install -r requirements.txt", "Installing dependencies"):
        print("📚 All dependencies installed successfully")
    
    # Check if .env exists
    env_file = Path(".env")
    if not env_file.exists():
        print("\n📄 Creating .env file from template...")
        env_example = Path(".env.example")
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ .env file created. Please edit it with your configuration.")
        else:
            print("⚠️  No .env.example found. You'll need to create .env manually.")
    
    # Check database configuration
    print("\n🗄️  Database Setup")
    print("For a quick demo, you can use SQLite by modifying settings.py")
    print("For full features, configure PostgreSQL in your .env file")
    
    # Run migrations
    print("\n🔄 Running database migrations...")
    run_command(f"{python_exe} manage.py migrate", "Database migrations")
    
    print("\n" + "=" * 40)
    print("🎉 Setup Complete!")
    print("\nTo start the development server:")
    if os.name == 'nt':
        print("  1. venv\\Scripts\\activate")
    else:
        print("  1. source venv/bin/activate")
    print("  2. python manage.py runserver")
    print("\nThen open: http://127.0.0.1:8000/")
    print("\n📖 See README.md for detailed usage instructions")

if __name__ == "__main__":
    main()