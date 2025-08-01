import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import TimeEntry, Project, db
from datetime import datetime

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return redirect(url_for('main.entries'))

@bp.route('/entries')
def entries():
    try:
        projects = Project.query.all()
        project_filter = request.args.get('project')
        if project_filter:
            entries = TimeEntry.query.filter_by(project_id=project_filter).all()
        else:
            entries = TimeEntry.query.all()
        return render_template('entries.html', entries=entries, projects=projects)
    except Exception as e:
        logging.error(f"Error in entries route: {e}", exc_info=True)
        flash('An error occurred while loading entries.', 'error')
        return render_template('entries.html', entries=[], projects=[])

@bp.route('/add_entry', methods=['GET', 'POST'])
def add_entry():
    if request.method == 'POST':
        project_id = request.form['project']
        description = request.form['description']
        hours = float(request.form['hours'])
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')

        entry = TimeEntry(project_id=project_id, description=description, hours=hours, date=date)
        db.session.add(entry)
        db.session.commit()

        flash('Entry added successfully.', 'success')
        return redirect(url_for('main.entries'))

    projects = Project.query.all()
    return render_template('add_entry.html', projects=projects)

@bp.route('/edit_entry/<int:id>', methods=['GET', 'POST'])
def edit_entry(id):
    entry = TimeEntry.query.get_or_404(id)
    if request.method == 'POST':
        entry.project_id = request.form['project']
        entry.description = request.form['description']
        entry.hours = float(request.form['hours'])
        entry.date = datetime.strptime(request.form['date'], '%Y-%m-%d')

        db.session.commit()
        flash('Entry updated successfully.', 'success')
        return redirect(url_for('main.entries'))

    projects = Project.query.all()
    return render_template('edit_entry.html', entry=entry, projects=projects)

@bp.route('/delete_entry/<int:id>')
def delete_entry(id):
    entry = TimeEntry.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted successfully.', 'success')
    return redirect(url_for('main.entries'))

@bp.route('/projects')
def projects():
    projects = Project.query.all()
    return render_template('projects.html', projects=projects)

@bp.route('/add_project', methods=['POST'])
def add_project():
    name = request.form['name']
    project = Project(name=name)
    db.session.add(project)
    db.session.commit()
    flash('Project added successfully.', 'success')
    return redirect(url_for('main.projects'))

@bp.route('/edit_project/<int:id>', methods=['POST'])
def edit_project(id):
    project = Project.query.get_or_404(id)
    project.name = request.form['name']
    db.session.commit()
    flash('Project updated successfully.', 'success')
    return redirect(url_for('main.projects'))

@bp.route('/toggle_project/<int:id>')
def toggle_project(id):
    project = Project.query.get_or_404(id)
    project.active = not project.active
    db.session.commit()
    return redirect(url_for('main.projects'))

@bp.route('/settings')
def settings():
    return render_template('settings.html')

@bp.route('/export')
def export():
    # Placeholder for export logic
    return "Export functionality not implemented yet."

@bp.route('/report')
def report():
    # Placeholder for report generation
    return "Report functionality not implemented yet."
