from flask import render_template, request, redirect, url_for, flash, jsonify, Response, make_response
from app import app, db
from models import TimeEntry, Project, Settings, get_setting, set_setting
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

@app.route('/')
def dashboard():
    """Main dashboard showing current cycle statistics"""
    # Get current monthly cycle
    start_date, end_date, cycle_name = get_current_monthly_cycle()
    
    # Get monthly goal
    monthly_goal = float(get_setting('monthly_goal_hours', '160'))
    
    # Calculate total billable hours for current cycle
    total_hours = db.session.query(func.sum(TimeEntry.hours)).filter(
        and_(
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date
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
            TimeEntry.date <= end_date
        )
    ).order_by(TimeEntry.date.desc(), TimeEntry.created_at.desc()).limit(10).all()
    
    # Get daily totals for current cycle
    daily_totals = db.session.query(
        TimeEntry.date,
        func.sum(TimeEntry.hours).label('total_hours')
    ).filter(
        and_(
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date
        )
    ).group_by(TimeEntry.date).order_by(TimeEntry.date.desc()).all()
    
    # Calculate working days in cycle and working days completed
    total_days = (end_date - start_date).days + 1
    days_completed = (date.today() - start_date).days + 1 if date.today() >= start_date else 0
    days_completed = min(days_completed, total_days)
    
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
                         decimal_to_hours_minutes=decimal_to_hours_minutes)

@app.route('/entries')
@app.route('/entries/<cycle_date>')
def entries(cycle_date=None):
    """View all entries for a specific cycle"""
    if cycle_date:
        try:
            target_date = datetime.strptime(cycle_date, '%Y-%m-%d').date()
            start_date, end_date, cycle_name = get_monthly_cycle_for_date(target_date)
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('entries'))
    else:
        start_date, end_date, cycle_name = get_current_monthly_cycle()
    
    # Get all entries for the cycle
    entries = TimeEntry.query.filter(
        and_(
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date
        )
    ).order_by(TimeEntry.date.desc(), TimeEntry.created_at.desc()).all()
    
    # Calculate total hours for the cycle
    total_hours = sum(entry.hours for entry in entries)
    
    # Group entries by date for better display
    entries_by_date = {}
    for entry in entries:
        date_key = entry.date
        if date_key not in entries_by_date:
            entries_by_date[date_key] = []
        entries_by_date[date_key].append(entry)
    
    # Get available cycles for navigation
    available_cycles = get_previous_cycles(12)
    
    return render_template('entries.html',
                         entries_by_date=entries_by_date,
                         cycle_name=cycle_name,
                         start_date=start_date,
                         end_date=end_date,
                         total_hours=total_hours,
                         available_cycles=available_cycles,
                         current_cycle_date=start_date,
                         decimal_to_hours_minutes=decimal_to_hours_minutes)

@app.route('/add_entry', methods=['GET', 'POST'])
def add_entry():
    """Add a new time entry"""
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

@app.route('/export')
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

@app.route('/export_data', methods=['GET', 'POST'])
def export_data():
    """Export time tracking data to CSV"""
    
    # Handle quick export via GET
    if request.method == 'GET':
        quick_type = request.args.get('quick')
        
        if quick_type == 'current_month':
            start_date, end_date, cycle_name = get_current_monthly_cycle()
            project_ids = None
            include_descriptions = True
            include_totals = True
        elif quick_type == 'all_data':
            start_date = None
            end_date = None
            project_ids = None
            include_descriptions = True
            include_totals = True
        else:
            return redirect(url_for('export_page'))
    else:
        # Handle form submission via POST
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        project_ids = request.form.getlist('project_ids')
        include_descriptions = 'include_descriptions' in request.form
        include_totals = 'include_totals' in request.form
        
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
def reports():
    """Advanced reports and analytics"""
    # Get current cycle data
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
    
    # Calculate efficiency metrics
    total_hours = sum(stat.total_hours for stat in project_stats)
    monthly_goal = float(get_setting('monthly_goal_hours', '160'))
    
    return render_template('reports.html',
                         cycle_name=cycle_name,
                         project_stats=project_stats,
                         hourly_stats=hourly_stats,
                         weekly_stats=weekly_stats,
                         total_hours=total_hours,
                         monthly_goal=monthly_goal,
                         decimal_to_hours_minutes=decimal_to_hours_minutes)

@app.route('/api/cycle_stats/<cycle_date>')
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
    return render_template('base.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('base.html'), 500
