from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Family, Meeting, Decision, Vote, VoteResponse, Contribution, Payment, Notification, MeetingAttendance
from datetime import datetime, date, timedelta
from forms import ProfileForm
import json

main = Blueprint('main', __name__)


@main.route('/dashboard')
@login_required
def dashboard():
    if not current_user.family_id:
        return redirect(url_for('auth.create_family'))
    
    family = Family.query.get(current_user.family_id)
    
    upcoming_meetings = Meeting.query.filter(
        Meeting.family_id == current_user.family_id,
        Meeting.date_time >= datetime.now()
    ).order_by(Meeting.date_time).limit(5).all()
    
    active_votes = Vote.query.filter(
        Vote.family_id == current_user.family_id,
        Vote.is_active == True
    ).order_by(Vote.created_at.desc()).limit(5).all()
    
    recent_decisions = Decision.query.filter(
        Decision.family_id == current_user.family_id
    ).order_by(Decision.created_at.desc()).limit(5).all()
    
    contributions = Contribution.query.filter(
        Contribution.family_id == current_user.family_id
    ).all()
    
    payments = Payment.query.filter(
        Payment.user_id == current_user.id
    ).all()
    
    total_collected = sum(float(p.amount) for p in payments if p.status == 'paid')
    pending = sum(float(c.amount) for c in contributions if c.frequency == 'one_time')
    overdue = 0
    
    for c in contributions:
        if c.frequency != 'one_time' or c.due_date < date.today():
            paid = any(p.contribution_id == c.id and p.status == 'paid' for p in payments)
            if not paid:
                overdue += float(c.amount)
    
    member_count = User.query.filter_by(family_id=current_user.family_id).count()
    meeting_count = Meeting.query.filter_by(family_id=current_user.family_id).count()
    
    total_votes = Vote.query.filter_by(family_id=current_user.family_id).count()
    
    attendance_records = MeetingAttendance.query.join(Meeting).filter(
        Meeting.family_id == current_user.family_id,
        MeetingAttendance.user_id == current_user.id,
        MeetingAttendance.present == True
    ).count()
    
    user_votes = VoteResponse.query.filter_by(user_id=current_user.id).count()
    
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    unread_count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return render_template('dashboard.html',
                         family=family,
                         upcoming_meetings=upcoming_meetings,
                         active_votes=active_votes,
                         recent_decisions=recent_decisions,
                         total_collected=total_collected,
                         pending=pending,
                         overdue=overdue,
                         member_count=member_count,
                         meeting_count=meeting_count,
                         total_votes=total_votes,
                         attendance_records=attendance_records,
                         user_votes=user_votes,
                         notifications=notifications,
                         unread_count=unread_count)


@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    
    if request.method == 'POST':
        current_user.name = form.name.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        current_user.family_role = form.family_role.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.profile'))
    
    form.name.data = current_user.name
    form.email.data = current_user.email
    form.phone.data = current_user.phone
    form.family_role.data = current_user.family_role
    
    return render_template('profile.html', form=form)


@main.route('/notifications')
@login_required
def notifications():
    all_notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=all_notifications)


@main.route('/mark-notification-read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get(notification_id)
    if notification and notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
    return redirect(url_for('main.notifications'))


@main.route('/mark-all-notifications-read')
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read', 'success')
    return redirect(url_for('main.notifications'))


@main.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    if not query:
        return render_template('search.html', results=None, query='')
    
    meetings = Meeting.query.filter(
        Meeting.family_id == current_user.family_id,
        Meeting.title.ilike(f'%{query}%')
    ).all()
    
    decisions = Decision.query.filter(
        Decision.family_id == current_user.family_id,
        Decision.title.ilike(f'%{query}%')
    ).all()
    
    votes = Vote.query.filter(
        Vote.family_id == current_user.family_id,
        Vote.title.ilike(f'%{query}%')
    ).all()
    
    contributions = Contribution.query.filter(
        Contribution.family_id == current_user.family_id,
        Contribution.title.ilike(f'%{query}%')
    ).all()
    
    results = {
        'meetings': meetings,
        'decisions': decisions,
        'votes': votes,
        'contributions': contributions
    }
    
    return render_template('search.html', results=results, query=query)


def create_notification(user_id, title, message, notification_type):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type
    )
    db.session.add(notification)
    db.session.commit()


def notify_family(family_id, title, message, notification_type):
    members = User.query.filter_by(family_id=family_id).all()
    for member in members:
        create_notification(member.id, title, message, notification_type)
