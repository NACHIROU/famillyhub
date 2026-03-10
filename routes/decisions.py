from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Decision, Meeting, User
from forms import DecisionForm
from routes.main import notify_family

decisions = Blueprint('decisions', __name__)


@decisions.route('/decisions')
@login_required
def index():
    if not current_user.family_id:
        flash('You need to create or join a family first', 'warning')
        return redirect(url_for('auth.create_family'))
    
    status_filter = request.args.get('status')
    query = Decision.query.filter_by(family_id=current_user.family_id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    all_decisions = query.order_by(Decision.created_at.desc()).all()
    
    return render_template('decisions/index.html', decisions=all_decisions)


@decisions.route('/decisions/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.family_id:
        flash('You need to join a family first', 'warning')
        return redirect(url_for('main.dashboard'))
    
    form = DecisionForm()
    meetings = Meeting.query.filter_by(family_id=current_user.family_id).all()
    form.meeting_id.choices = [(0, 'No Meeting')] + [(m.id, m.title) for m in meetings]
    
    if form.validate_on_submit():
        decision = Decision(
            family_id=current_user.family_id,
            meeting_id=form.meeting_id.data if form.meeting_id.data != 0 else None,
            title=form.title.data,
            description=form.description.data,
            status=form.status.data,
            created_by=current_user.id
        )
        db.session.add(decision)
        db.session.commit()
        
        notify_family(
            current_user.family_id,
            'New Decision Recorded',
            f'A new decision "{decision.title}" has been recorded with status: {decision.status}',
            'decision'
        )
        
        flash('Decision created successfully!', 'success')
        return redirect(url_for('decisions.index'))
    
    return render_template('decisions/create.html', form=form)


@decisions.route('/decisions/<int:decision_id>')
@login_required
def view(decision_id):
    decision = Decision.query.get_or_404(decision_id)
    if decision.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('decisions.index'))
    
    meeting = Meeting.query.get(decision.meeting_id) if decision.meeting_id else None
    
    return render_template('decisions/view.html', decision=decision, meeting=meeting)


@decisions.route('/decisions/<int:decision_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(decision_id):
    if not current_user.is_admin:
        flash('Only family admins can edit decisions', 'danger')
        return redirect(url_for('decisions.index'))
    
    decision = Decision.query.get_or_404(decision_id)
    if decision.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('decisions.index'))
    
    form = DecisionForm()
    meetings = Meeting.query.filter_by(family_id=current_user.family_id).all()
    form.meeting_id.choices = [(0, 'No Meeting')] + [(m.id, m.title) for m in meetings]
    
    if form.validate_on_submit():
        decision.title = form.title.data
        decision.description = form.description.data
        decision.meeting_id = form.meeting_id.data if form.meeting_id.data != 0 else None
        decision.status = form.status.data
        db.session.commit()
        
        notify_family(
            current_user.family_id,
            'Decision Updated',
            f'Decision "{decision.title}" status changed to: {decision.status}',
            'decision'
        )
        
        flash('Decision updated successfully!', 'success')
        return redirect(url_for('decisions.view', decision_id=decision_id))
    
    form.title.data = decision.title
    form.description.data = decision.description
    form.meeting_id.data = decision.meeting_id or 0
    form.status.data = decision.status
    
    return render_template('decisions/edit.html', form=form, decision=decision)


@decisions.route('/decisions/<int:decision_id>/delete')
@login_required
def delete(decision_id):
    if not current_user.is_admin:
        flash('Only family admins can delete decisions', 'danger')
        return redirect(url_for('decisions.index'))
    
    decision = Decision.query.get_or_404(decision_id)
    if decision.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('decisions.index'))
    
    db.session.delete(decision)
    db.session.commit()
    flash('Decision deleted successfully!', 'success')
    return redirect(url_for('decisions.index'))
