# 🐼 Panda Express POS System - Portfolio Project

**A comprehensive Django-based Point-of-Sale system showcasing full-stack development expertise**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/django-5.2-green.svg)](https://djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-15+-blue.svg)](https://postgresql.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com/)

## 🎯 Project Overview

This professional-grade POS system demonstrates enterprise-level web development skills through a complete restaurant management ecosystem. Built with Django and modern web technologies, it showcases real-time communication, complex database relationships, and intuitive user interfaces.

## ✨ Core Features

### 🏪 **Multi-Interface Architecture**
- **Customer Kiosk**: Touch-optimized self-service ordering
- **Cashier Terminal**: Staff order processing with cart management
- **Kitchen Display**: Real-time order queue with WebSocket updates
- **Manager Dashboard**: Analytics, inventory, and business intelligence
- **Digital Menu Board**: Dynamic display with weather integration

### 🔧 **Technical Excellence**
- **Real-time Updates**: WebSocket implementation via Django Channels
- **Database Design**: Complex relational models with proper normalization
- **API Integration**: External weather and translation services
- **Authentication**: Google OAuth + traditional auth with Django Allauth
- **Responsive Design**: Mobile-first CSS with dark/light themes
- **Internationalization**: Multi-language support with Azure Translation

## 🚀 Quick Demo Setup

### Option 1: Docker (Recommended)
```bash
git clone https://github.com/AidanxCannon/Panda_Express_Project_Demo.git
cd Panda_Express_Project_Demo
docker-compose up --build
```
Access: http://localhost:8000

### Option 2: Local Development
```bash
# Clone and setup
git clone https://github.com/AidanxCannon/Panda_Express_Project_Demo.git
cd Panda_Express_Project_Demo
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Quick SQLite setup for demo
cp .env.example .env
python manage.py migrate
python demo_server.py  # Includes sample data
```

## 🎪 Demo Walkthrough

### 1. **Customer Experience** (`/kiosk/`)
- Interactive menu browsing with categories
- Add items to cart with customizations
- Smooth checkout process
- Receipt generation (print/email)

### 2. **Staff Operations** (`/cashier/`)
- Efficient order entry interface
- Real-time cart management
- Customer information handling
- Receipt and payment processing

### 3. **Kitchen Workflow** (`/kitchen/`)
- Live order queue display
- WebSocket real-time updates
- Order status management
- Production workflow optimization

### 4. **Management Suite** (`/manager/`)
- Sales analytics and reporting
- Inventory management with alerts
- Employee oversight
- Business intelligence dashboard

### 5. **Digital Signage** (`/menu/`)
- Customer-facing menu display
- Weather widget integration
- Language switching capability

## 🏗️ Technical Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Django        │    │   Database      │
│   (Templates)   │◄──►│   Backend       │◄──►│   PostgreSQL    │
│   CSS/JS        │    │   (Views/APIs)  │    │   (Models)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       
         │                       │                       
         ▼                       ▼                       
┌─────────────────┐    ┌─────────────────┐              
│   WebSockets    │    │   External APIs │              
│   (Channels)    │    │   Weather/Trans │              
└─────────────────┘    └─────────────────┘              
```

### Key Technologies
- **Backend**: Django 5.2, Django Channels, PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript ES6+
- **Real-time**: WebSockets, Redis
- **Authentication**: Django Allauth, OAuth 2.0
- **APIs**: RESTful design, External integrations
- **Deployment**: Docker, Docker Compose
- **Development**: Python 3.11+, Virtual environments

## 🎯 Professional Skills Demonstrated

### **Full-Stack Development**
- ✅ Django MVT architecture implementation
- ✅ Complex database modeling and relationships
- ✅ RESTful API design and integration
- ✅ WebSocket real-time communication
- ✅ Responsive CSS and modern JavaScript

### **Software Engineering**
- ✅ Clean, maintainable code structure
- ✅ Proper separation of concerns
- ✅ Environment-based configuration
- ✅ Database migrations and version control
- ✅ Error handling and input validation

### **DevOps & Deployment**
- ✅ Docker containerization
- ✅ Environment variable management
- ✅ Production-ready configurations
- ✅ Database optimization
- ✅ Static file management

### **User Experience**
- ✅ Intuitive interface design
- ✅ Mobile-responsive layouts
- ✅ Accessibility considerations
- ✅ Performance optimization
- ✅ Cross-browser compatibility

## 📊 Business Logic Complexity

### **Order Management**
- Multi-item cart with modifications
- Recipe-ingredient relationships
- Inventory tracking and depletion
- Order status workflow

### **Real-time Operations**
- Kitchen order queue updates
- Inventory level monitoring
- Sales analytics computation
- Customer notification system

### **Data Analytics**
- Top-selling items analysis
- Sales trend reporting
- Inventory turnover metrics
- Employee performance tracking

## 🔐 Security & Best Practices

- **Authentication**: Secure user sessions and OAuth integration
- **Data Protection**: CSRF tokens, SQL injection prevention
- **Input Validation**: Comprehensive form validation
- **Environment Security**: Sensitive data in environment variables
- **Database Security**: Proper user permissions and connection handling

## 📱 Mobile Responsiveness

Optimized for all device types:
- **📱 Mobile**: Touch-friendly kiosk interface
- **📟 Tablet**: Perfect for cashier terminals
- **💻 Desktop**: Full management capabilities
- **📺 Display**: Kitchen and menu board screens

## 🚀 Deployment Options

### **Development**
```bash
python demo_server.py  # Includes sample data
```

### **Production**
```bash
docker-compose -f docker-compose.prod.yml up
```

### **Cloud Platforms**
- Heroku ready
- Digital Ocean compatible
- AWS deployment ready
- Google Cloud Platform ready

## 📈 Performance Features

- **Efficient Queries**: Optimized database access patterns
- **Static Files**: WhiteNoise for fast static file serving
- **Caching Strategy**: Redis integration for session storage
- **Asset Optimization**: Minified CSS/JS for production
- **Database Indexing**: Proper indexes for query performance

## 🎓 Learning Outcomes

This project demonstrates understanding of:
- Enterprise-level web application architecture
- Real-time web technologies and WebSockets
- Complex database design and ORM usage
- Modern frontend development practices
- Security best practices and authentication
- DevOps and containerization technologies
- API design and external service integration
- User experience and interface design

## 📞 Contact

**Aidan Hester**  
*Full-Stack Developer*

📧 Email: ahester731@gmail.com  
💼 LinkedIn: [linkedin.com/in/aidan-hester-731](https://linkedin.com/in/aidan-hester-731)  
🐱 GitHub: [github.com/AidanxCannon](https://github.com/AidanxCannon)

---

*This project showcases professional web development capabilities suitable for enterprise environments, demonstrating both technical depth and practical business application.*