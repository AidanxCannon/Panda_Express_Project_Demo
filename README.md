# 🐼 Panda Express Point-of-Sale System — Demo Repository

**Academic Capstone Project**  
**Role:** Project Manager & Full-Stack Developer  
**Purpose:** Portfolio demonstration of system design, UI/UX, and real-time architecture

## Overview

This repository is a curated, public-facing demo snapshot of a full-scale Django-based Point-of-Sale (POS) system designed to simulate the operational ecosystem of a Panda Express restaurant.

Developed as a team-based capstone project, this system showcases modern software engineering practices including agile development, version control workflows, and collaborative coding standards. The application handles complex business workflows from order placement through kitchen fulfillment, demonstrating enterprise-level system design principles.

The project demonstrates real-time order synchronization, multi-role interfaces, and production-oriented system architecture, while intentionally omitting proprietary logic, credentials, and deployment secrets.

⚠️ **Note:** This repository is not intended to run locally. It exists to showcase engineering decisions, interface design, and system structure for recruiters and reviewers.

## System Interfaces

### 🧑‍🍜 Customer Kiosk
- Touch-first self-service ordering flow with intuitive category navigation
- Dynamic meal customization with pricing calculations
- Cart persistence and order modification capabilities
- Multi-language support with session-based preferences
- Optimized for tablet and kiosk displays with accessibility considerations

### 💳 Cashier Terminal
- Streamlined assisted order entry for staff efficiency
- Real-time order summaries with itemized breakdown
- Integrated pricing, tax calculation, and receipt logic
- Customer information capture and order tracking
- Support for payment processing workflows

### 🔥 Kitchen Display System
- Live order queue with real-time status updates
- WebSocket-driven communication for instant order notifications
- Clear visual prioritization system for active orders
- Order completion tracking and kitchen workflow optimization
- Color-coded order status indicators

### 🧑‍💼 Manager Dashboard
- Comprehensive inventory management with low-stock alerts
- Menu item activation/deactivation with real-time updates
- Employee management and scheduling tools
- Sales analytics with trend analysis and reporting
- Performance tracking and business intelligence features

### 📺 Digital Menu Board
- Dynamic menu display with automatic updates
- Language-aware labels and pricing localization
- External data integration (weather, promotional content)
- Responsive design for various display sizes
- Centralized content management system

## Technical Highlights

- **Backend Framework:** Django 5.2 with modular app architecture
- **Real-Time Communication:** WebSockets via Django Channels with Redis backing
- **Database:** PostgreSQL with complex relational modeling
- **Frontend Technologies:** Modern HTML5, CSS3 Grid/Flexbox, Vanilla JavaScript
- **Authentication System:** Google OAuth2 integration with Django Allauth
- **Internationalization:** Multi-language support with Azure Translation API
- **Cloud Infrastructure:** Containerized deployment ready for cloud platforms
- **Development Practices:** Git workflow, code review, and documentation standards

## Architecture Overview

```
├── apps/
│   ├── kiosk/          # Customer self-service UI
│   ├── cashier/        # Staff order entry
│   ├── kitchen/        # Real-time kitchen display
│   ├── manager/        # Management dashboard
│   └── menu_board/     # Digital menu display
│
├── architecture/       # System and data-flow documentation
├── sample_code/        # Redacted, annotated backend excerpts
├── static/             # CSS, JS, UI assets
└── screenshots/        # Interface previews
```

*Additional architectural explanations are provided in `/architecture`.*

## Real-Time System Design

The application implements a sophisticated real-time communication system using WebSocket technology:

- **Centralized Order State Management:** Single source of truth for order data
- **Cross-Interface Broadcasting:** WebSocket events synchronized across all interfaces:
  - Customer kiosk order updates
  - Cashier terminal notifications
  - Kitchen display queue management
  - Manager dashboard analytics refresh
- **Role-Based Access Control:** Interface-specific permissions and data filtering
- **Event-Driven Architecture:** Asynchronous updates without page refresh
- **Session Persistence:** Stateful connections with automatic reconnection handling

The system ensures data consistency across all interfaces while maintaining responsive user experiences and efficient resource utilization.

*Annotated WebSocket and permission examples can be found in `/sample_code`.*

## My Contributions

As Project Manager and Lead Developer on this team-based capstone project:

**Project Leadership:**
- Served as **Scrum Master** coordinating 6-person development team
- Implemented agile methodologies with sprint planning and retrospectives
- Managed project timeline, deliverables, and stakeholder communication

**Technical Implementation:**
- **Architected real-time WebSocket system** for cross-interface communication
- **Led comprehensive UI/UX redesign** across all five system interfaces
- **Integrated disparate team modules** into cohesive, unified system
- **Developed responsive design framework** ensuring consistency across interfaces

**Code Quality & Integration:**
- Established code review processes and Git workflow standards
- **Refactored legacy kiosk and manager interfaces** for improved usability
- Implemented comprehensive error handling and input validation
- Created documentation and deployment guides for team knowledge transfer

## What This Repository Includes

✅ **Complete UI Templates & Assets:** All interface designs and styling  
✅ **Static Resources:** Images, CSS frameworks, and JavaScript components  
✅ **System Architecture Documentation:** Design decisions and data flow diagrams  
✅ **Code Structure Examples:** Annotated Django views, models, and WebSocket handlers  
✅ **Interface Mockups:** Visual representations of all five system interfaces  
✅ **Project Documentation:** Development process, team workflows, and technical specifications

## What This Repository Excludes

❌ **Production Database Schemas:** Sensitive data models and migration files  
❌ **Business Logic Implementation:** Complete backend processing and algorithms  
❌ **Authentication Credentials:** API keys, OAuth secrets, and security tokens  
❌ **Deployment Configurations:** Server settings, environment variables, and infrastructure code  
❌ **Third-Party Integrations:** Complete payment processing and external service implementations  

## Intended Audience

This demonstration repository is specifically designed for:

**Technical Recruiters:** Showcase of full-stack development capabilities and project management experience  
**Hiring Managers:** Evidence of collaborative leadership and system design thinking  
**Software Engineers:** Code quality, architecture decisions, and technical implementation approach  
**Product Managers:** Understanding of user experience design and cross-functional coordination

**Use Cases:**
- Technical portfolio review and discussion
- System design interview preparation and walkthrough
- Code quality assessment and architectural decision analysis
- Project management and team leadership demonstration

This repository is designed to support technical walkthroughs, system design discussions, and portfolio review — **not local execution**.

## License

This project is shared for educational and portfolio demonstration purposes only.

## Developer

**Aidan Cannon**  
*Full-Stack Developer · Software Engineer*
