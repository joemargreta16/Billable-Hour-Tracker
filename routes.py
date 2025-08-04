from flask import render_template, request, redirect, url_for, flash, jsonify, Response, make_response, session, abort
from app import app, db
import logging
from functools import wraps
from app import app, db
from models import TimeEntry, Project, Settings, get_setting, set_setting, User
from utils import (
    get_current_monthly_cycle, 
    get_monthly_cycle_for_date, 
    hours_to_decimal, 
    decimal_to_hours_minutes,
    get_previous_cycles,
    format_date_for_input,
    parse_date_from_input
)
from datetime import date, datetime, timedelta
from sqlalchemy import func, and_, or_
import csv
import io

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Helper functions for authentication
def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=session['username']).first()
        if not user or not user.is_admin:
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get the current logged-in user"""
    if 'username' not in session:
        return None
    return User.query.filter_by(username=session['username']).first()

def require_login():
    """Check if user is logged in, redirect to login if not"""
    if 'username' not in session:
        flash('Please login to access this page', 'error')
        return redirect(url_for('login'))
    return None

@app.route('/')
@login_required
def dashboard():
    """Main dashboard showing current cycle statistics with date range filter"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            cycle_name = f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
            return redirect(url_for('dashboard'))
    else:
        start_date, end_date, cycle_name = get_current_monthly_cycle()
    
    # Get monthly goal
    monthly_goal = float(get_setting('monthly_goal_hours', '160'))
    
    # Calculate total billable hours for current cycle
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))
    
    total_hours = db.session.query(func.sum(TimeEntry.hours)).filter(
        and_(
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date,
            TimeEntry.user_id == current_user.id
        )
    ).scalar() or 0.0
    
    # Calculate remaining hours
    remaining_hours = max(0, monthly_goal - total_hours)
    
    # Calculate progress percentage
    progress_percentage = min(100, (total_hours / monthly_goal) * 100) if monthly_goal > 0 else 0
    
    # Get recent entries (last 10)
    recent_entries = TimeEntry.query.filter(
        and_(
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date,
            TimeEntry.user_id == current_user.id
        )
    ).order_by(TimeEntry.date.desc(), TimeEntry.created_at.desc()).limit(10).all()
    
    # Get daily totals for current cycle
    daily_totals = db.session.query(
        TimeEntry.date,
        func.sum(TimeEntry.hours).label('total_hours')
    ).filter(
        and_(
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date,
            TimeEntry.user_id == current_user.id
        )
    ).group_by(TimeEntry.date).order_by(TimeEntry.date.desc()).all()
    
    # Calculate working days in cycle and working days completed
    total_days = (end_date - start_date).days + 1
    days_completed = (date.today() - start_date).days + 1 if date.today() >= start_date else 0
    days_completed = min(days_completed, total_days)
    
    available_cycles = get_previous_cycles(12)
    
    # Get current month for the filter default
    current_month = start_date.strftime('%Y-%m')

    return render_template('dashboard.html',
                         cycle_name=cycle_name,
                         start_date=start_date,
                         end_date=end_date,
                         total_hours=total_hours,
                         monthly_goal=monthly_goal,
                         remaining_hours=remaining_hours,
                         progress_percentage=progress_percentage,
                         recent_entries=recent_entries,
                         daily_totals=daily_totals,
                         days_completed=days_completed,
                         total_days=total_days,
                         decimal_to_hours_minutes=decimal_to_hours_minutes,
                         available_cycles=available_cycles,
                         current_month=current_month)


@app.route('/entries')
@app.route('/entries/<cycle_date>')
@login_required
def entries(cycle_date=None):
    """View all entries with filters for cycle, week, and project"""
    try:
        # Get filter parameters
        cycle_date_param = request.args.get('cycle_date') or cycle_date
        week_param = request.args.get('week')
        project_id_param = request.args.get('project_id')
        
        # Determine date range
        if week_param:
            try:
                year, week_num = map(int, week_param.split('-W'))
                start_date = datetime.strptime(f'{year}-W{week_num - 1}-1', "%Y-W%W-%w").date()
                end_date = start_date + timedelta(days=6)
                cycle_name = f"Week {week_num}, {year}"
            except ValueError:
                flash('Invalid week format. Use YYYY-WNN (e.g. 2023-W05)', 'error')
                return redirect(url_for('entries'))
        elif cycle_date_param:
            try:
                target_date = datetime.strptime(cycle_date_param, '%Y-%m-%d').date()
                cycle_data = get_monthly_cycle_for_date(target_date)
                
                # Handle both tuple and object returns
                if hasattr(cycle_data, 'start_date'):  # If it's a Cycle object
                    start_date = cycle_data.start_date
                    end_date = cycle_data.end_date
                    cycle_name = cycle_data.name
                else:  # If it's a tuple
                    start_date, end_date, cycle_name = cycle_data
            except (ValueError, TypeError) as e:
                logger.error(f"Date processing error: {e}")
                flash('Invalid date format or cycle data', 'error')
                return redirect(url_for('entries'))
        else:
            cycle_data = get_current_monthly_cycle()
            # Handle both tuple and object returns
            if hasattr(cycle_data, 'start_date'):
                start_date = cycle_data.start_date
                end_date = cycle_data.end_date
                cycle_name = cycle_data.name
            else:
                start_date, end_date, cycle_name = cycle_data

        # Build query
        current_user = get_current_user()
        if not current_user:
            return redirect(url_for('login'))
            
        query = TimeEntry.query.filter(
            and_(
                TimeEntry.date.between(start_date, end_date),
                TimeEntry.user_id == current_user.id
            )
        ).order_by(TimeEntry.date.desc(), TimeEntry.created_at.desc())
        
        # Apply project filter if specified
        if project_id_param and project_id_param.isdigit():
            query = query.filter(TimeEntry.project_id == int(project_id_param))
        
        # Execute query
        entries = query.all()
        
        # Group entries by date
        entries_by_date = {}
        for entry in entries:
            if entry.date not in entries_by_date:
                entries_by_date[entry.date] = []
            entries_by_date[entry.date].append(entry)
        
        # Calculate total hours
        total_hours = sum(entry.hours for entry in entries)
        
        # Get available cycles - convert Cycle objects to tuples if needed
        available_cycles = []
        for cycle in get_previous_cycles(12):
            if hasattr(cycle, 'start_date'):  # It's a Cycle object
                available_cycles.append((
                    cycle.start_date,
                    cycle.end_date,
                    cycle.name
                ))
            else:  # It's already a tuple
                available_cycles.append(cycle)
        
        projects = Project.query.filter_by(active=True).order_by(Project.name).all()
        
        return render_template('entries.html',
                            entries_by_date=entries_by_date,
                            cycle_name=cycle_name,
                            start_date=start_date,
                            end_date=end_date,
                            total_hours=total_hours,
                            available_cycles=available_cycles,
                            current_cycle_date=start_date,
                            decimal_to_hours_minutes=decimal_to_hours_minutes,
                            projects=projects)
        
    except Exception as e:
        logger.error(f"Error in entries route: {str(e)}", exc_info=True)
        flash(f'An error occurred while loading entries: {str(e)}', 'error')
        return redirect(url_for('dashboard'))


@app.route('/add_entry', methods=['GET', 'POST'])
@login_required
def add_entry():
    """Add a new time entry"""
    stay_on_page = request.args.get('stay', 'false').lower() == 'true'
    if request.method == 'POST':
        # Get form data
        date_str = request.form.get('date')
        project_id = request.form.get('project_id')
        hours_str = request.form.get('hours')
        description = request.form.get('description', '').strip()
        stay_on_page = request.form.get('stay_on_page') == 'true'
        
        # Validate data
        errors = []
        
        # Validate date
        entry_date = parse_date_from_input(date_str)
        if not entry_date:
            errors.append('Please provide a valid date')
        
        # Validate project
        if not project_id:
            errors.append('Please select a project')
        else:
            project = Project.query.get(project_id)
            if not project:
                errors.append('Invalid project selected')
        
        # Validate hours
        hours = hours_to_decimal(hours_str)
        if hours <= 0:
            errors.append('Please provide valid hours (greater than 0)')
        if hours > 24:
            errors.append('Hours cannot exceed 24 per day')
        
        if errors:
            for error in errors:
                flash(error, 'error')
        else:
            # Create new time entry
            try:
                new_entry = TimeEntry()
                new_entry.date = entry_date
                new_entry.project_id = int(project_id) if project_id else None
                new_entry.hours = hours
                new_entry.description = description
                db.session.add(new_entry)
                db.session.commit()
                flash('Time entry added successfully!', 'success')
                if stay_on_page:
                    return redirect(url_for('add_entry', stay='true'))
                else:
                    return redirect(url_for('entries'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding entry: {str(e)}', 'error')
    
    # Get active projects for the form
    projects = Project.query.filter_by(active=True).order_by(Project.name).all()
    
    # Default to today's date
    default_date = format_date_for_input(date.today())
    
    return render_template('add_entry.html', 
                         projects=projects, 
                         default_date=default_date)

@app.route('/edit_entry/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    """Edit an existing time entry"""
    entry = TimeEntry.query.get_or_404(entry_id)
    
    if request.method == 'POST':
        # Get form data
        date_str = request.form.get('date')
        project_id = request.form.get('project_id')
        hours_str = request.form.get('hours')
        description = request.form.get('description', '').strip()
        
        # Validate data
        errors = []
        
        # Validate date
        entry_date = parse_date_from_input(date_str)
        if not entry_date:
            errors.append('Please provide a valid date')
        
        # Validate project
        if not project_id:
            errors.append('Please select a project')
        else:
            project = Project.query.get(project_id)
            if not project:
                errors.append('Invalid project selected')
        
        # Validate hours
        hours = hours_to_decimal(hours_str)
        if hours <= 0:
            errors.append('Please provide valid hours (greater than 0)')
        if hours > 24:
            errors.append('Hours cannot exceed 24 per day')
        
        if errors:
            for error in errors:
                flash(error, 'error')
        else:
            # Update the entry
            try:
                entry.date = entry_date
                entry.project_id = int(project_id) if project_id else None
                entry.hours = hours
                entry.description = description
                entry.updated_at = datetime.utcnow()
                db.session.commit()
                flash('Time entry updated successfully!', 'success')
                return redirect(url_for('entries'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating entry: {str(e)}', 'error')
    
    # Get active projects for the form
    projects = Project.query.filter_by(active=True).order_by(Project.name).all()
    
    return render_template('edit_entry.html', 
                         entry=entry, 
                         projects=projects,
                         format_date_for_input=format_date_for_input,
                         decimal_to_hours_minutes=decimal_to_hours_minutes)

@app.route('/delete_entry/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    """Delete a time entry"""
    entry = TimeEntry.query.get_or_404(entry_id)
    
    try:
        db.session.delete(entry)
        db.session.commit()
        flash('Time entry deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting entry: {str(e)}', 'error')
    
    return redirect(url_for('entries'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Application settings page"""
    if request.method == 'POST':
        # Update settings
        monthly_goal = request.form.get('monthly_goal_hours')
        
        try:
            # Validate monthly goal
            goal_hours = float(monthly_goal) if monthly_goal else 0.0
            if goal_hours <= 0:
                flash('Monthly goal must be greater than 0', 'error')
            else:
                set_setting('monthly_goal_hours', str(goal_hours))
                flash('Settings updated successfully!', 'success')
        except ValueError:
            flash('Please provide a valid number for monthly goal', 'error')
        
        return redirect(url_for('settings'))
    
    # Get current settings
    current_goal = get_setting('monthly_goal_hours', '160')
    
    # Get projects for management
    projects = Project.query.order_by(Project.name).all()
    
    return render_template('settings.html', 
                         monthly_goal=current_goal,
                         projects=projects)

@app.route('/toggle_project/<int:project_id>', methods=['POST'])
@login_required
def toggle_project(project_id):
    """Toggle project active status"""
    project = Project.query.get_or_404(project_id)
    
    try:
        project.active = not project.active
        db.session.commit()
        status = 'activated' if project.active else 'deactivated'
        flash(f'Project "{project.name}" {status} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating project: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

@app.route('/add_project', methods=['POST'])
@login_required
def add_project():
    """Add a new project"""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name:
        flash('Project name is required', 'error')
        return redirect(url_for('settings'))
    
    # Check if project already exists
    existing_project = Project.query.filter_by(name=name).first()
    if existing_project:
        flash('A project with this name already exists', 'error')
        return redirect(url_for('settings'))
    
    try:
        new_project = Project()
        new_project.name = name
        new_project.description = description
        db.session.add(new_project)
        db.session.commit()
        flash(f'Project "{name}" added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding project: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

@app.route('/delete_project/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    """Delete a project and its associated time entries"""
    project = Project.query.get_or_404(project_id)

    try:
        # The 'delete-orphan' cascade will handle deleting associated time entries
        db.session.delete(project)
        db.session.commit()
        flash(f'Project "{project.name}" and all its time entries have been deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting project: {str(e)}', 'error')

    return redirect(url_for('settings'))

@app.route('/edit_project/<int:project_id>', methods=['POST'])
def edit_project(project_id):
    """Edit an existing project"""
    project = Project.query.get_or_404(project_id)

    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Project name is required', 'error')
        return redirect(url_for('settings'))

    # Check if another project with the same name already exists
    existing_project = Project.query.filter(Project.name == name, Project.id != project_id).first()
    if existing_project:
        flash('A project with this name already exists', 'error')
        return redirect(url_for('settings'))

    try:
        project.name = name
        project.description = description
        project.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Project "{name}" updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating project: {str(e)}', 'error')

    return redirect(url_for('settings'))

@app.route('/export')
@login_required
def export_page():
    """Export data page"""
    # Get all projects for filter
    projects = Project.query.order_by(Project.name).all()
    
    # Get current cycle dates as defaults
    start_date, end_date, cycle_name = get_current_monthly_cycle()
    
    return render_template('export.html', 
                         projects=projects,
                         start_date=format_date_for_input(start_date),
                         end_date=format_date_for_input(end_date))

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

@app.route('/export_data', methods=['GET', 'POST'])
@login_required
def export_data():
    """Export time tracking data to CSV or PDF"""
    
    # Handle quick export via GET
    if request.method == 'GET':
        quick_type = request.args.get('quick')
        
        if quick_type == 'current_month':
            start_date, end_date, cycle_name = get_current_monthly_cycle()
            project_ids = None
            include_descriptions = True
            include_totals = True
            export_format = 'csv'
        elif quick_type == 'all_data':
            start_date = None
            end_date = None
            project_ids = None
            include_descriptions = True
            include_totals = True
            export_format = 'csv'
        else:
            return redirect(url_for('export_page'))
    else:
        # Handle form submission via POST
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        project_ids = request.form.getlist('project_ids')
        include_descriptions = 'include_descriptions' in request.form
        include_totals = 'include_totals' in request.form
        export_format = request.form.get('format', 'csv')
        
        start_date = parse_date_from_input(start_date_str) if start_date_str else None
        end_date = parse_date_from_input(end_date_str) if end_date_str else None
    
    # Build query
    query = TimeEntry.query.join(Project)
    
    # Apply date filters
    if start_date:
        query = query.filter(TimeEntry.date >= start_date)
    if end_date:
        query = query.filter(TimeEntry.date <= end_date)
    
    # Apply project filters
    if project_ids:
        query = query.filter(TimeEntry.project_id.in_(project_ids))
    
    # Get entries ordered by date
    entries = query.order_by(TimeEntry.date.desc(), TimeEntry.created_at.desc()).all()
    
    if export_format == 'pdf':
        # Generate PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(inch, height - inch, "Time Tracking Export")
        
        # Date range info
        date_range_str = "All Data"
        if start_date and end_date:
            date_range_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        elif start_date:
            date_range_str = f"From {start_date.strftime('%Y-%m-%d')}"
        elif end_date:
            date_range_str = f"Until {end_date.strftime('%Y-%m-%d')}"
        p.setFont("Helvetica", 12)
        p.drawString(inch, height - inch - 20, f"Date Range: {date_range_str}")
        
        # Table headers
        y = height - inch - 50
        p.setFont("Helvetica-Bold", 10)
        headers = ['Date', 'Project', 'Hours (Decimal)', 'Hours (HH:MM)']
        if include_descriptions:
            headers.append('Description')
        for i, header in enumerate(headers):
            p.drawString(inch + i*100, y, header)
        
        # Table rows
        p.setFont("Helvetica", 10)
        y -= 15
        for entry in entries:
            if y < inch:
                p.showPage()
                y = height - inch
            row = [
                entry.date.strftime('%Y-%m-%d'),
                entry.project.name,
                f"{entry.hours:.2f}",
                entry.hours_minutes_display
            ]
            if include_descriptions:
                row.append(entry.description or '')
            for i, cell in enumerate(row):
                p.drawString(inch + i*100, y, str(cell))
            y -= 15
        
        # Totals if requested
        if include_totals and entries:
            if y < inch + 40:
                p.showPage()
                y = height - inch
            y -= 10
            p.setFont("Helvetica-Bold", 12)
            p.drawString(inch, y, "SUMMARY")
            y -= 15
            
            project_totals = {}
            total_hours = 0
            for entry in entries:
                project_name = entry.project.name
                if project_name not in project_totals:
                    project_totals[project_name] = 0
                project_totals[project_name] += entry.hours
                total_hours += entry.hours
            
            p.setFont("Helvetica", 10)
            for project_name, hours in project_totals.items():
                if y < inch:
                    p.showPage()
                    y = height - inch
                p.drawString(inch, y, f"TOTAL - {project_name}: {hours:.2f} ({decimal_to_hours_minutes(hours)})")
                y -= 15
            
            if y < inch:
                p.showPage()
                y = height - inch
            p.drawString(inch, y, f"GRAND TOTAL - All Projects: {total_hours:.2f} ({decimal_to_hours_minutes(total_hours)})")
            y -= 15
        
        p.save()
        buffer.seek(0)
        
        response = make_response(buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        filename = f"time_tracking_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    else:
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = ['Date', 'Project', 'Hours (Decimal)', 'Hours (HH:MM)']
        if include_descriptions:
            headers.append('Description')
        headers.extend(['Created At', 'Updated At'])
        writer.writerow(headers)
        
        # Write data rows
        for entry in entries:
            row = [
                entry.date.strftime('%Y-%m-%d'),
                entry.project.name,
                f"{entry.hours:.2f}",
                entry.hours_minutes_display
            ]
            if include_descriptions:
                row.append(entry.description or '')
            row.extend([
                entry.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                entry.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
            writer.writerow(row)
        
        # Add totals if requested
        if include_totals and entries:
            writer.writerow([])  # Empty row
            writer.writerow(['SUMMARY'])
            
            # Calculate project totals
            project_totals = {}
            total_hours = 0
            
            for entry in entries:
                project_name = entry.project.name
                if project_name not in project_totals:
                    project_totals[project_name] = 0
                project_totals[project_name] += entry.hours
                total_hours += entry.hours
            
            # Write project totals
            for project_name, hours in project_totals.items():
                writer.writerow([
                    'TOTAL',
                    project_name,
                    f"{hours:.2f}",
                    decimal_to_hours_minutes(hours)
                ])
            
            # Write grand total
            writer.writerow([
                'GRAND TOTAL',
                'All Projects',
                f"{total_hours:.2f}",
                decimal_to_hours_minutes(total_hours)
            ])
        
        # Create response
        csv_content = output.getvalue()
        output.close()
        
        # Generate filename
        date_range = ""
        if start_date and end_date:
            date_range = f"_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"
        elif start_date:
            date_range = f"_from_{start_date.strftime('%Y%m%d')}"
        elif end_date:
            date_range = f"_until_{end_date.strftime('%Y%m%d')}"
        
        filename = f"time_tracking_export{date_range}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response

@app.route('/search')
@login_required
def search_entries():
    """Search and filter time entries"""
    query_text = request.args.get('q', '').strip()
    project_filter = request.args.get('project', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Start with base query
    query = TimeEntry.query.join(Project)
    
    # Apply text search
    if query_text:
        query = query.filter(
            or_(
                TimeEntry.description.ilike(f'%{query_text}%'),
                Project.name.ilike(f'%{query_text}%')
            )
        )
    
    # Apply project filter
    if project_filter:
        query = query.filter(TimeEntry.project_id == project_filter)
    
    # Apply date filters
    if date_from:
        start_date = parse_date_from_input(date_from)
        if start_date:
            query = query.filter(TimeEntry.date >= start_date)
    
    if date_to:
        end_date = parse_date_from_input(date_to)
        if end_date:
            query = query.filter(TimeEntry.date <= end_date)
    
    # Get results
    entries = query.order_by(TimeEntry.date.desc(), TimeEntry.created_at.desc()).limit(100).all()
    
    # Calculate total hours for results
    total_hours = sum(entry.hours for entry in entries)
    
    # Get all projects for filter dropdown
    projects = Project.query.filter_by(active=True).order_by(Project.name).all()
    
    # Group entries by date
    entries_by_date = {}
    for entry in entries:
        date_key = entry.date
        if date_key not in entries_by_date:
            entries_by_date[date_key] = []
        entries_by_date[date_key].append(entry)
    
    return render_template('search.html',
                         entries_by_date=entries_by_date,
                         total_hours=total_hours,
                         projects=projects,
                         query_text=query_text,
                         project_filter=project_filter,
                         date_from=date_from,
                         date_to=date_to,
                         decimal_to_hours_minutes=decimal_to_hours_minutes)

@app.route('/reports')
@login_required
def reports():
    """Advanced reports and analytics"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            cycle_name = f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
            return redirect(url_for('reports'))
    else:
        start_date, end_date, cycle_name = get_current_monthly_cycle()
    
    # Get project statistics
    project_stats = db.session.query(
        Project.name,
        func.sum(TimeEntry.hours).label('total_hours'),
        func.count(TimeEntry.id).label('entry_count'),
        func.avg(TimeEntry.hours).label('avg_hours')
    ).join(TimeEntry).filter(
        and_(
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date
        )
    ).group_by(Project.name).order_by(func.sum(TimeEntry.hours).desc()).all()
    
    # Get hourly distribution
    hourly_stats = db.session.query(
        func.extract('hour', TimeEntry.created_at).label('hour'),
        func.count(TimeEntry.id).label('entries'),
        func.sum(TimeEntry.hours).label('total_hours')
    ).filter(
        and_(
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date
        )
    ).group_by(func.extract('hour', TimeEntry.created_at)).all()
    
    # Get weekly patterns
    weekly_stats = db.session.query(
        func.extract('dow', TimeEntry.date).label('day_of_week'),
        func.avg(TimeEntry.hours).label('avg_hours'),
        func.sum(TimeEntry.hours).label('total_hours')
    ).filter(
        and_(
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date
        )
    ).group_by(func.extract('dow', TimeEntry.date)).all()
    
    # Additional data for new charts
    # Get daily totals for heatmap (date and total hours)
    daily_totals = db.session.query(
        TimeEntry.date,
        func.sum(TimeEntry.hours).label('total_hours')
    ).filter(
        and_(
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date
        )
    ).group_by(TimeEntry.date).order_by(TimeEntry.date).all()
    
    # Get project totals by date for stacked bar chart
    project_daily_totals = db.session.query(
        TimeEntry.date,
        Project.name,
        func.sum(TimeEntry.hours).label('total_hours')
    ).join(Project).filter(
        and_(
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date
        )
    ).group_by(TimeEntry.date, Project.name).order_by(TimeEntry.date).all()

    # Convert project_daily_totals to list of dicts for JSON serialization
    project_daily_totals = [
        {
            'date': item.date.strftime('%Y-%m-%d') if hasattr(item.date, 'strftime') else str(item.date),
            'name': item.name,
            'total_hours': float(item.total_hours) if item.total_hours is not None else 0.0
        }
        for item in project_daily_totals
    ]
    
    # Calculate efficiency metrics
    total_hours = sum(stat.total_hours for stat in project_stats)
    monthly_goal = float(get_setting('monthly_goal_hours', '160'))

    # Debug logging for data counts
    logger.debug(f"Reports data counts - Projects: {len(project_stats)}, Hourly: {len(hourly_stats)}, Weekly: {len(weekly_stats)}, Daily: {len(daily_totals)}, Project Daily: {len(project_daily_totals)}")
    
    return render_template('reports.html',
                         cycle_name=cycle_name,
                         project_stats=project_stats,
                         hourly_stats=hourly_stats,
                         weekly_stats=weekly_stats,
                         daily_totals=daily_totals,
                         project_daily_totals=project_daily_totals,
                         total_hours=total_hours,
                         monthly_goal=monthly_goal,
                         decimal_to_hours_minutes=decimal_to_hours_minutes)

@app.route('/projects')
@login_required
def projects():
    """List all projects for management"""
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('projects.html', projects=projects)

@app.route('/project/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project_page(project_id):
    """Render and process editing a project"""
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Project name is required.', 'error')
            return redirect(url_for('edit_project_page', project_id=project_id))
        
        # Check for duplicate names
        existing_project = Project.query.filter(Project.name == name, Project.id != project_id).first()
        if existing_project:
            flash('A project with this name already exists.', 'error')
            return redirect(url_for('edit_project_page', project_id=project_id))
        
    try:
        project.name = name
        project.description = description
        # Handle missing updated_at column gracefully
        if hasattr(project, 'updated_at'):
            project.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('projects'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating project: {str(e)}', 'error')
        return redirect(url_for('edit_project_page', project_id=project_id))
    
    return render_template('edit_project.html', project=project)

@app.route('/project/add', methods=['GET', 'POST'])
def add_project_page():
    """Add a new project via dedicated page"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not name:
            flash('Project name is required.', 'error')
            return redirect(url_for('add_project_page'))
        
        # Check if project already exists
        existing_project = Project.query.filter_by(name=name).first()
        if existing_project:
            flash('A project with this name already exists.', 'error')
            return redirect(url_for('add_project_page'))
        
        try:
            new_project = Project()
            new_project.name = name
            new_project.description = description
            db.session.add(new_project)
            db.session.commit()
            flash(f'Project "{name}" added successfully!', 'success')
            return redirect(url_for('projects'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding project: {str(e)}', 'error')
            return redirect(url_for('add_project_page'))
    
    return render_template('add_project.html')

@app.route('/api/cycle_stats/<cycle_date>')
@login_required
def api_cycle_stats(cycle_date):
    """API endpoint to get cycle statistics"""
    try:
        target_date = datetime.strptime(cycle_date, '%Y-%m-%d').date()
        start_date, end_date, cycle_name = get_monthly_cycle_for_date(target_date)
        
        # Calculate total hours for the cycle
        total_hours = db.session.query(func.sum(TimeEntry.hours)).filter(
            and_(
                TimeEntry.date >= start_date,
                TimeEntry.date <= end_date
            )
        ).scalar() or 0.0
        
        # Get monthly goal
        monthly_goal = float(get_setting('monthly_goal_hours', '160'))
        
        return jsonify({
            'cycle_name': cycle_name,
            'total_hours': total_hours,
            'monthly_goal': monthly_goal,
            'remaining_hours': max(0, monthly_goal - total_hours),
            'progress_percentage': min(100, (total_hours / monthly_goal) * 100) if monthly_goal > 0 else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 Not Found: {request.path}")
    if request.path.startswith('/entries'):
        return redirect(url_for('entries'))
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"500 Internal Server Error: {error}")
    return render_template('base.html'), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('login'))
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['username'] = username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.pop('username', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return redirect(url_for('signup'))
        
        if len(username) < 3:
            flash('Username must be at least 3 characters', 'error')
            return redirect(url_for('signup'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('signup'))
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
            return redirect(url_for('signup'))
        
        # Create new user
        try:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating account: {str(e)}', 'error')
            return redirect(url_for('signup'))
    
    return render_template('signup.html')
