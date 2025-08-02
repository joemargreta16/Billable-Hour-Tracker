# Time Tracker Application

## Overview

This is a Flask-based time tracking application that allows users to log work hours against projects and track progress toward monthly goals. The application uses a unique monthly cycle system (25th to 24th of each month) and provides dashboard insights, time entry management, and project administration.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with Python
- **Database**: SQLAlchemy ORM with configurable database backend (defaults to SQLite, supports PostgreSQL via DATABASE_URL environment variable)
- **Session Management**: Flask sessions with configurable secret key
- **Deployment**: WSGI-ready with ProxyFix middleware for production deployments

### Frontend Architecture
- **Template Engine**: Jinja2 templates with a base template system
- **CSS Framework**: Bootstrap 5 with Replit dark theme
- **Icons**: Feather Icons for consistent iconography
- **Date Handling**: Flatpickr for enhanced date input experience
- **Charts**: Chart.js for progress visualization (referenced but not implemented in visible code)

## Key Components

### Data Models
1. **Project**: Stores project information with name, description, and active status
2. **TimeEntry**: Records billable hours with date, project association, hours (decimal format), and description
3. **Settings**: Key-value store for application configuration (monthly goals, etc.)

### Core Features
1. **Dashboard**: Monthly cycle overview with progress tracking
2. **Time Entry Management**: Add, edit, and view time entries
3. **Project Management**: Basic project administration
4. **Settings**: Configurable monthly hour goals
5. **Monthly Cycles**: Custom billing cycle from 25th to 24th of each month

### Utility Functions
- Custom monthly cycle calculations (25th to 24th pattern)
- Time format conversion (decimal hours to hours:minutes)
- Date manipulation utilities

## Data Flow

1. **Time Entry Workflow**:
   - User selects date and project
   - Enters hours (converted to decimal internally)
   - Optional description
   - Data stored in TimeEntry model

2. **Dashboard Calculations**:
   - Determines current monthly cycle
   - Aggregates total hours for cycle
   - Calculates progress against monthly goal
   - Displays recent entries and daily totals

3. **Monthly Cycle Logic**:
   - Cycles run from 25th of one month to 24th of next month
   - Automatic calculation of cycle boundaries
   - Historical cycle navigation

## External Dependencies

### Python Packages
- Flask: Web framework
- Flask-SQLAlchemy: Database ORM
- Werkzeug: WSGI utilities and middleware

### Frontend Libraries
- Bootstrap 5: UI framework with Replit dark theme
- Feather Icons: Icon library
- Flatpickr: Date picker enhancement
- Chart.js: Charting library (for future visualizations)

### Database
- SQLite: Default local database
- PostgreSQL: Production database option via DATABASE_URL

## Deployment Strategy

### Environment Configuration
- `DATABASE_URL`: Database connection string (defaults to SQLite)
- `SESSION_SECRET`: Session encryption key (defaults to development key)

### Production Considerations
- ProxyFix middleware configured for reverse proxy deployments
- Database connection pooling with health checks
- Configurable logging levels
- WSGI-ready application structure

### Database Initialization
- Automatic table creation on first run
- Default data initialization system
- Migration-ready with SQLAlchemy

### Security Features
- Session-based authentication ready (secret key configuration)
- CSRF protection ready for forms
- SQL injection protection via SQLAlchemy ORM

## Recent Changes

### July 24, 2025 - Login System Implementation
Added comprehensive user authentication and authorization system with data isolation between users.

#### New Core Features:
1. **User Authentication**: Secure login system with password hashing
2. **Data Isolation**: Users can only access their own projects and time entries
3. **Admin User Management**: Admin users can view and delete other users
4. **Default Admin User**: Automatic creation of default admin user "Joemar" with password "110291"
5. **Session Management**: Secure session handling for authenticated users

#### Enhanced Features:
- All existing features now require authentication
- Admin users have access to user management interface
- Existing data automatically associated with default admin user
- Navigation updated with login/logout functionality
- Admin users can access user management section

#### Technical Improvements:
- Added User model with password hashing using Werkzeug
- Implemented login_required and admin_required decorators
- Added user_id foreign keys to Project and TimeEntry models for data isolation
- Created login and admin user management templates
- Updated all routes to filter data by user for proper isolation
- Added database migration script for new users table and user_id columns

### July 24, 2025 - Major Feature Enhancement
Added comprehensive bonus features from original requirements:

#### New Core Features:
1. **CSV Export System**: Full export functionality with customizable date ranges, project filtering, and format options
2. **Advanced Search & Filtering**: Search through time entries by description, project, or date range with highlighting
3. **Interactive Charts & Visualizations**: Progress charts, daily bar charts, pie charts using Chart.js
4. **Reports & Analytics Dashboard**: Project breakdowns, weekly patterns, hourly distribution analysis
5. **Progressive Web App (PWA)**: Mobile app-like experience with manifest.json and service worker for offline functionality

#### Enhanced Features:
- Dashboard now includes interactive doughnut and bar charts
- Navigation expanded with Search, Reports, and Export sections
- Progress bars show percentage completion
- Visual project statistics and productivity insights
- Mobile-optimized interface for smartphone usage
- Offline capability for basic functionality

#### Technical Improvements:
- Added Chart.js integration for data visualization
- Implemented service worker for PWA functionality
- Enhanced navigation structure with additional menu items
- Improved mobile responsiveness and touch interactions
- Added visual feedback and progress indicators

The application now meets all original requirements including the 11 bonus features, providing a complete professional time tracking solution suitable for both web and mobile use.
