from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import User, Family, Meeting, Decision, Vote, VoteResponse, Contribution, Payment, Notification, MeetingAttendance
from datetime import datetime, date, timedelta
from forms import ProfileForm

main = Blueprint('main', __name__)


@main.route('/dashboard')
@login_required
def dashboard():
    if not current_user.family_id:
        return redirect(url_for('auth.create_family'))
    
    family = Family.objects.get(id=current_user.family_id)
    
    upcoming_meetings = Meeting.objects(
        family_id=current_user.family_id,
        date_time__gte=datetime.now()
    ).order_by('date_time').limit(5)
    
    active_votes = Vote.objects(
        family_id=current_user.family_id,
        is_active=True
    ).order_by('-created_at').limit(5)
    
    recent_decisions = Decision.objects(
        family_id=current_user.family_id
    ).order_by('-created_at').limit(5)
    
    contributions = Contribution.objects(family_id=current_user.family_id)
    
    payments = Payment.objects(user_id=current_user.id)
    
    total_collected = sum(float(p.amount) for p in payments if p.status == 'paid')
    pending = sum(float(c.amount) for c in contributions if c.frequency == 'one_time')
    overdue = 0
    
    for c in contributions:
        if c.frequency != 'one_time' or c.due_date < date.today():
            paid = any(p.contribution_id == c.id and p.status == 'paid' for p in payments)
            if not paid:
                overdue += float(c.amount)
    
    member_count = User.objects(family_id=current_user.family_id).count()
    meeting_count = Meeting.objects(family_id=current_user.family_id).count()
    
    total_votes = Vote.objects(family_id=current_user.family_id).count()
    
    attendance_records = MeetingAttendance.objects(
        meeting_id__in=Meeting.objects(family_id=current_user.family_id).scalar('id'),
        user_id=current_user.id,
        present=True
    ).count()
    
    user_votes = VoteResponse.objects(user_id=current_user.id).count()
    
    notifications = Notification.objects(
        user_id=current_user.id,
        is_read=False
    ).order_by('-created_at').limit(10)
    
    unread_count = Notification.objects(
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
        current_user.save()
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
    all_notifications = Notification.objects(
        user_id=current_user.id
    ).order_by('-created_at')
    return render_template('notifications.html', notifications=all_notifications)


@main.route('/mark-notification-read/<notification_id>')
@login_required
def mark_notification_read(notification_id):
    from bson import ObjectId
    notification = Notification.objects(id=ObjectId(notification_id)).first()
    if notification and notification.user_id == current_user.id:
        notification.is_read = True
        notification.save()
    return redirect(url_for('main.notifications'))


@main.route('/mark-all-notifications-read')
@login_required
def mark_all_notifications_read():
    Notification.objects(user_id=current_user.id, is_read=False).update(set__is_read=True)
    flash('All notifications marked as read', 'success')
    return redirect(url_for('main.notifications'))


@main.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    if not query:
        return render_template('search.html', results=None, query='')
    
    meetings = Meeting.objects(
        family_id=current_user.family_id,
        title__icontains=query
    )
    
    decisions = Decision.objects(
        family_id=current_user.family_id,
        title__icontains=query
    )
    
    votes = Vote.objects(
        family_id=current_user.family_id,
        title__icontains=query
    )
    
    contributions = Contribution.objects(
        family_id=current_user.family_id,
        title__icontains=query
    )
    
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
    notification.save()


def notify_family(family_id, title, message, notification_type):
    members = User.objects(family_id=family_id)
    for member in members:
        create_notification(member.id, title, message, notification_type)
