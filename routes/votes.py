from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Vote, VoteResponse, Decision, User
from forms import VoteForm
from datetime import datetime
from routes.main import notify_family
import json

votes = Blueprint('votes', __name__)


@votes.route('/votes')
@login_required
def index():
    if not current_user.family_id:
        flash('You need to create or join a family first', 'warning')
        return redirect(url_for('auth.create_family'))
    
    status_filter = request.args.get('status')
    query = Vote.query.filter_by(family_id=current_user.family_id)
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'closed':
        query = query.filter_by(is_active=False)
    
    all_votes = query.order_by(Vote.created_at.desc()).all()
    
    for vote in all_votes:
        if vote.deadline and vote.deadline < datetime.now() and vote.is_active:
            vote.is_active = False
            db.session.commit()
    
    return render_template('votes/index.html', votes=all_votes)


@votes.route('/votes/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.family_id:
        flash('You need to join a family first', 'warning')
        return redirect(url_for('main.dashboard'))
    
    form = VoteForm()
    decisions = Decision.query.filter_by(family_id=current_user.family_id).all()
    form.decision_id.choices = [(0, 'No Decision')] + [(d.id, d.title) for d in decisions]
    
    if form.validate_on_submit():
        options_list = []
        if form.vote_type.data == 'multiple_choice' and form.options.data:
            options_list = [opt.strip() for opt in form.options.data.split(',')]
        elif form.vote_type.data == 'yes_no':
            options_list = ['Yes', 'No']
        
        vote = Vote(
            family_id=current_user.family_id,
            decision_id=form.decision_id.data if form.decision_id.data != 0 else None,
            title=form.title.data,
            vote_type=form.vote_type.data,
            options=json.dumps(options_list),
            deadline=form.deadline.data,
            is_active=True,
            created_by=current_user.id
        )
        db.session.add(vote)
        db.session.commit()
        
        notify_family(
            current_user.family_id,
            'New Vote Created',
            f'A new vote "{vote.title}" has been created. Cast your vote now!',
            'vote'
        )
        
        flash('Vote created successfully!', 'success')
        return redirect(url_for('votes.index'))
    
    return render_template('votes/create.html', form=form)


@votes.route('/votes/<int:vote_id>')
@login_required
def view(vote_id):
    vote = Vote.query.get_or_404(vote_id)
    if vote.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('votes.index'))
    
    decision = Decision.query.get(vote.decision_id) if vote.decision_id else None
    
    user_vote = VoteResponse.query.filter_by(vote_id=vote_id, user_id=current_user.id).first()
    
    show_results = True
    if vote.vote_type == 'secret' and vote.is_active:
        show_results = False
    
    results = vote.get_results() if show_results else None
    total_votes = sum(results.values()) if results else 0
    
    responses = VoteResponse.query.filter_by(vote_id=vote_id).all() if show_results else []
    
    return render_template('votes/view.html', 
                         vote=vote, 
                         decision=decision,
                         user_vote=user_vote,
                         results=results,
                         total_votes=total_votes,
                         show_results=show_results,
                         responses=responses)


@votes.route('/votes/<int:vote_id>/vote', methods=['POST'])
@login_required
def cast_vote(vote_id):
    vote = Vote.query.get_or_404(vote_id)
    if vote.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('votes.index'))
    
    if not vote.is_active:
        flash('This vote is closed', 'danger')
        return redirect(url_for('votes.view', vote_id=vote_id))
    
    if vote.deadline and vote.deadline < datetime.now():
        flash('Voting deadline has passed', 'danger')
        return redirect(url_for('votes.view', vote_id=vote_id))
    
    existing_vote = VoteResponse.query.filter_by(vote_id=vote_id, user_id=current_user.id).first()
    if existing_vote:
        flash('You have already voted', 'warning')
        return redirect(url_for('votes.view', vote_id=vote_id))
    
    response = request.form.get('response')
    if not response:
        flash('Please select an option', 'danger')
        return redirect(url_for('votes.view', vote_id=vote_id))
    
    vote_response = VoteResponse(
        vote_id=vote_id,
        user_id=current_user.id,
        response=response
    )
    db.session.add(vote_response)
    db.session.commit()
    
    flash('Vote cast successfully!', 'success')
    return redirect(url_for('votes.view', vote_id=vote_id))


@votes.route('/votes/<int:vote_id>/close')
@login_required
def close_vote(vote_id):
    if not current_user.is_admin:
        flash('Only family admins can close votes', 'danger')
        return redirect(url_for('votes.index'))
    
    vote = Vote.query.get_or_404(vote_id)
    if vote.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('votes.index'))
    
    vote.is_active = False
    db.session.commit()
    
    flash('Vote closed successfully!', 'success')
    return redirect(url_for('votes.view', vote_id=vote_id))


@votes.route('/votes/<int:vote_id>/delete')
@login_required
def delete(vote_id):
    if not current_user.is_admin:
        flash('Only family admins can delete votes', 'danger')
        return redirect(url_for('votes.index'))
    
    vote = Vote.query.get_or_404(vote_id)
    if vote.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('votes.index'))
    
    db.session.delete(vote)
    db.session.commit()
    flash('Vote deleted successfully!', 'success')
    return redirect(url_for('votes.index'))
