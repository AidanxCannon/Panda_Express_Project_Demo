# 🐼 Panda Express Point-of-Sale System

A comprehensive **Django-based Point-of-Sale (POS) system** that simulates the complete restaurant ecosystem of Panda Express. This full-stack web application demonstrates modern software engineering practices with real-time updates, multiple user interfaces, and integrated business workflows.

## ✨ Key Features

### 🏠 **Multi-Interface System**
- **Customer Kiosk** - Self-service ordering with intuitive touch interface
- **Cashier Terminal** - Staff order entry with cart management and receipt printing
- **Kitchen Display** - Real-time order queue with live updates via WebSockets
- **Manager Dashboard** - Analytics, inventory management, and staff oversight
- **Menu Board** - Dynamic display with weather integration and multilingual support

### 🔧 **Technical Highlights**
- **Real-time Communication**: WebSocket integration using Django Channels
- **Database Management**: PostgreSQL with complex relational models
- **Authentication**: Google OAuth integration with Django Allauth
- **Internationalization**: Multi-language support with Azure Translation API
- **Responsive Design**: Mobile-first CSS with dark/light themes
- **API Integration**: Weather data and translation services
- **Production Ready**: Docker support and deployment configurations

### 📊 **Business Intelligence**
- Live sales analytics and top-selling items tracking
- Inventory management with low-stock alerts
- Employee management and scheduling
- Order history and receipt generation
- Sales reporting and trend analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL database
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/AidanxCannon/Panda_Express_Project_Demo.git
cd Panda_Express_Project_Demo
```

2. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your database credentials and API keys
```

5. **Run database migrations**
```bash
python manage.py migrate
```

6. **Start the development server**
```bash
python manage.py runserver
```

7. **Access the application**
Open your browser to `http://127.0.0.1:8000/`

## 🗄️ Database Setup

### Option 1: SQLite (Quick Demo)
For a quick demonstration, modify `settings.py` to use SQLite:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'demo_db.sqlite3',
    }
}
```

### Option 2: PostgreSQL (Recommended)
1. Create a PostgreSQL database
2. Update your `.env` file with database credentials
3. Run migrations: `python manage.py migrate`

## 🎯 Demo Scenarios

### For Interviewers & Evaluators

1. **Customer Experience**
   - Navigate to `/kiosk/` to experience the self-service ordering
   - Add items to cart, customize orders, and complete checkout

2. **Staff Operations**
   - Visit `/cashier/` for the employee order entry interface
   - Process orders with cart management and receipt options

3. **Kitchen Workflow**
   - Open `/kitchen/` to see real-time order display
   - Watch orders update live as they're placed from other interfaces

4. **Management Features**
   - Access `/manager/` for comprehensive business analytics
   - View sales reports, manage inventory, and track performance

5. **Digital Menu Board**
   - Check `/menu/` for the customer-facing menu display
   - See weather integration and language switching capabilities

## 🏗️ Architecture Overview

```
├── apps/                    # Django applications
│   ├── cashier/            # Staff order entry interface
│   ├── customer_kiosk/     # Self-service kiosk
│   ├── kitchen/            # Kitchen display system
│   ├── manager/            # Management dashboard
│   ├── menu/               # Digital menu board
│   ├── inventory/          # Inventory management
│   └── orders/             # Order processing logic
├── core/                   # Shared models and utilities
│   └── models/             # Database models
├── panda_config/           # Django project settings
├── static/                 # Static files (CSS, JS, images)
└── requirements.txt        # Python dependencies
```

## 💡 Technical Innovations

- **Channel Layers**: Real-time WebSocket communication for kitchen updates
- **Model Relationships**: Complex many-to-many relationships for recipes and ingredients
- **Session Management**: Persistent cart state across user sessions
- **API Integrations**: External weather and translation services
- **Responsive Design**: CSS Grid and Flexbox for modern layouts
- **Security**: CSRF protection, SQL injection prevention, and secure authentication

## 🌟 Professional Development Showcase

This project demonstrates proficiency in:
- **Full-Stack Development**: Frontend and backend integration
- **Database Design**: Normalized schema with proper relationships
- **Real-Time Systems**: WebSocket implementation
- **API Development**: RESTful endpoints and external API integration
- **DevOps**: Environment configuration and deployment readiness
- **Testing**: Unit tests and integration testing frameworks
- **Documentation**: Comprehensive code documentation and README

## 🔧 Environment Variables

Required variables for full functionality:

```bash
# Database
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432

# External APIs (Optional)
API_KEY_EXTERNAL_SERVICE=weather_api_key
AZURE_TRANSLATION_KEY=translation_key
AZURE_TRANSLATION_REGION=region
AZURE_TRANSLATION_ENDPOINT=endpoint

# Authentication (Optional)
GOOGLE_OAUTH_CLIENT_ID=oauth_client_id
GOOGLE_OAUTH_CLIENT_SECRET=oauth_secret

# Security
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
```

## 📱 Mobile Responsiveness

The application is fully responsive and optimized for:
- 📱 Mobile devices (customer kiosk simulation)
- 💻 Desktop browsers (cashier and management interfaces)
- 📺 Large displays (kitchen screens and menu boards)

## 🚀 Deployment Ready

- **Docker**: Containerization support with docker-compose
- **Environment Configuration**: Production/development settings
- **Static File Handling**: WhiteNoise for static file serving
- **Database Migration**: Automated database setup
- **CI/CD Ready**: GitHub Actions compatible

## 🤝 Contributing

This is a demonstration project showcasing software engineering capabilities. The codebase follows Django best practices and is structured for maintainability and scalability.

## 📄 License

MIT License - See LICENSE file for details.

## 👨‍💻 Developer

**Aidan Hester**  
*Full-Stack Developer & Software Engineer*

This project showcases enterprise-level web development skills with modern frameworks, real-time communication, and scalable architecture design.

---

*Built with Django, PostgreSQL, WebSockets, and modern web technologies*
