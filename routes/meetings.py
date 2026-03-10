from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Meeting, MeetingAttendance, User, Family, Notification
from forms import MeetingForm
from datetime import datetime
from routes.main import notify_family

meetings = Blueprint('meetings', __name__)


@meetings.route('/meetings')
@login_required
def index():
    if not current_user.family_id:
        flash('You need to create or join a family first', 'warning')
        return redirect(url_for('auth.create_family'))
    
    all_meetings = Meeting.query.filter_by(
        family_id=current_user.family_id
    ).order_by(Meeting.date_time.desc()).all()
    
    return render_template('meetings/index.html', meetings=all_meetings)


@meetings.route('/meetings/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_admin:
        flash('Only family admins can create meetings', 'danger')
        return redirect(url_for('meetings.index'))
    
    form = MeetingForm()
    
    if form.validate_on_submit():
        meeting_datetime = datetime.combine(form.date.data, datetime.strptime(form.time.data, '%H:%M').time())
        
        meeting = Meeting(
            family_id=current_user.family_id,
            title=form.title.data,
            date_time=meeting_datetime,
            location=form.location.data,
            agenda=form.agenda.data,
            themes_discussed=form.themes_discussed.data,
            minutes=form.minutes.data,
            created_by=current_user.id
        )
        db.session.add(meeting)
        db.session.commit()
        
        family_members = User.query.filter_by(family_id=current_user.family_id).all()
        for member in family_members:
            attendance = MeetingAttendance(
                meeting_id=meeting.id,
                user_id=member.id,
                present=False
            )
            db.session.add(attendance)
        db.session.commit()
        
        notify_family(
            current_user.family_id,
            'New Meeting Scheduled',
            f'A new meeting "{meeting.title}" has been scheduled for {meeting.date_time.strftime("%B %d, %Y at %H:%M")}',
            'meeting'
        )
        
        flash('Meeting created successfully!', 'success')
        return redirect(url_for('meetings.index'))
    
    return render_template('meetings/create.html', form=form)


@meetings.route('/meetings/<int:meeting_id>')
@login_required
def view(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    if meeting.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('meetings.index'))
    
    attendance = MeetingAttendance.query.filter_by(meeting_id=meeting_id).all()
    members = User.query.filter_by(family_id=current_user.family_id).all()
    
    return render_template('meetings/view.html', meeting=meeting, attendance=attendance, members=members)


@meetings.route('/meetings/<int:meeting_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(meeting_id):
    if not current_user.is_admin:
        flash('Only family admins can edit meetings', 'danger')
        return redirect(url_for('meetings.index'))
    
    meeting = Meeting.query.get_or_404(meeting_id)
    if meeting.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('meetings.index'))
    
    form = MeetingForm()
    
    if form.validate_on_submit():
        meeting_datetime = datetime.combine(form.date.data, datetime.strptime(form.time.data, '%H:%M').time())
        
        meeting.title = form.title.data
        meeting.date_time = meeting_datetime
        meeting.location = form.location.data
        meeting.agenda = form.agenda.data
        meeting.themes_discussed = form.themes_discussed.data
        meeting.minutes = form.minutes.data
        
        db.session.commit()
        flash('Meeting updated successfully!', 'success')
        return redirect(url_for('meetings.view', meeting_id=meeting_id))
    
    form.title.data = meeting.title
    form.date.data = meeting.date_time.date()
    form.time.data = meeting.date_time.strftime('%H:%M')
    form.location.data = meeting.location
    form.agenda.data = meeting.agenda
    form.themes_discussed.data = meeting.themes_discussed
    form.minutes.data = meeting.minutes
    
    return render_template('meetings/edit.html', form=form, meeting=meeting)


@meetings.route('/meetings/<int:meeting_id>/delete')
@login_required
def delete(meeting_id):
    if not current_user.is_admin:
        flash('Only family admins can delete meetings', 'danger')
        return redirect(url_for('meetings.index'))
    
    meeting = Meeting.query.get_or_404(meeting_id)
    if meeting.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('meetings.index'))
    
    db.session.delete(meeting)
    db.session.commit()
    flash('Meeting deleted successfully!', 'success')
    return redirect(url_for('meetings.index'))


@meetings.route('/meetings/<int:meeting_id>/attendance', methods=['POST'])
@login_required
def update_attendance(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    if meeting.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('meetings.index'))
    
    user_id = request.form.get('user_id')
    present = request.form.get('present') == 'true'
    
    attendance = MeetingAttendance.query.filter_by(
        meeting_id=meeting_id,
        user_id=user_id
    ).first()
    
    if attendance:
        attendance.present = present
        db.session.commit()
    
    flash('Attendance updated!', 'success')
    return redirect(url_for('meetings.view', meeting_id=meeting_id))
