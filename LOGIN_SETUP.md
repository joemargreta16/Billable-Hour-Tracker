# Login System Setup

This document explains how to set up and use the login system for the Time Tracker application.

## Overview

The login system provides:
- User authentication with username and password
- Data isolation between users
- Admin user management capabilities
- Default admin user creation

## Setup Instructions

### 1. Run Database Migrations

After implementing the login system, you need to run the database migration to create the users table and add user_id columns to existing tables:

```bash
flask db upgrade
```

### 2. Default Admin User

The system automatically creates a default admin user on startup if no users exist:
- Username: `Joemar`
- Password: `110291`
- Role: Admin

This user will have access to all existing data in the system.

### 3. Existing Data Association

When the default admin user is created, all existing projects and time entries will be automatically associated with this user for data isolation purposes.

## Features

### User Authentication
- Users can log in with their username and password
- Session management for authenticated users
- Login required for all application features

### Data Isolation
- Users can only see and modify their own projects and time entries
- Admin users can see and manage all data

### Admin User Management
- Admin users can view all registered users
- Admin users can delete other users (except the last admin user)
- Admin users cannot delete themselves

## Usage

### Logging In
1. Navigate to the login page
2. Enter your username and password
3. Click "Login"

### Logging Out
1. Click the "Logout" link in the navigation bar

### Admin User Management
1. Admin users will see a "Users" link in the navigation bar
2. Click the "Users" link to view the user management page
3. From this page, you can delete users (except the last admin user)

## Security Notes

- Passwords are securely hashed using Werkzeug's security utilities
- Sessions are managed using Flask's built-in session handling
- Data isolation is enforced at the application level
- Admin privileges are required for user management functions

## Troubleshooting

### If you can't log in
- Verify that the database migration has been run
- Check that the default admin user was created (check application logs)
- Reset the database and re-run migrations if needed

### If you can't access existing data
- Ensure that existing data has been properly associated with the default admin user
- Check application logs for any errors during data association

### If user management functions aren't working
- Verify that you're logged in as an admin user
- Check application logs for any errors
