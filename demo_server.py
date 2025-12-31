#!/usr/bin/env python
"""
Development server launcher with demo data seeding
"""
import os
import sys
import subprocess
import django
from pathlib import Path

# Add the project directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'panda_config.settings')
django.setup()

def create_demo_data():
    """Create demo data for the application"""
    try:
        # Import models after Django setup
        from core.models import Recipe, Inventory
        from django.contrib.auth.models import User
        
        print("📦 Creating demo data...")
        
        # Create sample recipes if none exist
        if not Recipe.objects.exists():
            recipes = [
                {"name": "Orange Chicken", "category": "entree", "price": 8.50},
                {"name": "Beijing Beef", "category": "entree", "price": 9.00},
                {"name": "Honey Walnut Shrimp", "category": "entree", "price": 10.50},
                {"name": "Fried Rice", "category": "side", "price": 4.50},
                {"name": "Chow Mein", "category": "side", "price": 4.50},
                {"name": "Fountain Drink", "category": "drink", "price": 2.50},
            ]
            
            for recipe_data in recipes:
                Recipe.objects.create(**recipe_data)
            
            print("✅ Sample recipes created")
        
        # Create admin user if none exists
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@pandaexpress.demo',
                password='demo123'
            )
            print("✅ Admin user created (admin/demo123)")
        
        print("🎉 Demo data setup complete!")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not create demo data: {e}")

def main():
    print("🐼 Panda Express POS - Development Server")
    print("=" * 45)
    
    # Run migrations first
    print("🔄 Running database migrations...")
    subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
    
    # Create demo data
    create_demo_data()
    
    # Start development server
    print("\n🚀 Starting development server...")
    print("📱 Access the application at: http://127.0.0.1:8000/")
    print("🔧 Admin interface at: http://127.0.0.1:8000/admin/")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 45)
    
    try:
        subprocess.run([sys.executable, "manage.py", "runserver"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Thanks for the demo!")

if __name__ == "__main__":
    main()