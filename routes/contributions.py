from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Contribution, Payment, User
from forms import ContributionForm, PaymentForm
from datetime import date, datetime, timedelta
from routes.main import notify_family

contributions = Blueprint('contributions', __name__)


@contributions.route('/contributions')
@login_required
def index():
    if not current_user.family_id:
        flash('You need to create or join a family first', 'warning')
        return redirect(url_for('auth.create_family'))
    
    all_contributions = Contribution.objects(
        family_id=current_user.family_id
    ).order_by('-due_date')
    
    payments = Payment.objects()
    
    members = User.objects(family_id=current_user.family_id)
    
    contribution_status = []
    for contrib in all_contributions:
        contrib_payments = [p for p in payments if p.contribution_id == contrib.id]
        total_paid = sum(float(p.amount) for p in contrib_payments if p.status == 'paid')
        status = 'paid' if total_paid >= float(contrib.amount) else ('overdue' if contrib.due_date < date.today() else 'pending')
        
        member_payments = {}
        for member in members:
            member_pay = next((p for p in contrib_payments if p.user_id == member.id and p.status == 'paid'), None)
            member_payments[member.id] = member_pay
        
        contribution_status.append({
            'contribution': contrib,
            'status': status,
            'total_paid': total_paid,
            'member_payments': member_payments
        })
    
    total_expected = sum(float(c.amount) for c in all_contributions if c.frequency == 'one_time')
    total_collected = sum(float(p.amount) for p in payments if p.status == 'paid')
    total_pending = total_expected - total_collected
    
    return render_template('contributions/index.html', 
                         contribution_status=contribution_status,
                         members=members,
                         total_expected=total_expected,
                         total_collected=total_collected,
                         total_pending=total_pending)


@contributions.route('/contributions/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_admin:
        flash('Only family admins can create contributions', 'danger')
        return redirect(url_for('contributions.index'))
    
    form = ContributionForm()
    
    if form.validate_on_submit():
        contribution = Contribution(
            family_id=current_user.family_id,
            title=form.title.data,
            amount=form.amount.data,
            frequency=form.frequency.data,
            due_date=form.due_date.data,
            created_by=current_user.id
        )
        contribution.save()
        
        notify_family(
            current_user.family_id,
            'New Contribution Created',
            f'A new contribution "{contribution.title}" of {contribution.amount} CFA has been created. Due date: {contribution.due_date}',
            'contribution'
        )
        
        flash('Contribution created successfully!', 'success')
        return redirect(url_for('contributions.index'))
    
    return render_template('contributions/create.html', form=form)


@contributions.route('/contributions/<contribution_id>')
@login_required
def view(contribution_id):
    from bson import ObjectId
    contribution = Contribution.objects(id=ObjectId(contribution_id)).first()
    if not contribution or contribution.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('contributions.index'))
    
    payments = Payment.objects(contribution_id=contribution.id)
    members = User.objects(family_id=current_user.family_id)
    
    return render_template('contributions/view.html', 
                         contribution=contribution, 
                         payments=payments,
                         members=members)


@contributions.route('/contributions/<contribution_id>/payment', methods=['POST'])
@login_required
def add_payment(contribution_id):
    from bson import ObjectId
    contribution = Contribution.objects(id=ObjectId(contribution_id)).first()
    if not contribution or contribution.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('contributions.index'))
    
    user_id = request.form.get('user_id')
    amount = float(request.form.get('amount'))
    payment_date = request.form.get('payment_date')
    status = request.form.get('status')
    
    payment = Payment(
        contribution_id=contribution.id,
        user_id=user_id,
        amount=amount,
        payment_date=datetime.strptime(payment_date, '%Y-%m-%d').date(),
        status=status
    )
    payment.save()
    
    flash('Payment recorded successfully!', 'success')
    return redirect(url_for('contributions.view', contribution_id=contribution_id))


@contributions.route('/contributions/<contribution_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(contribution_id):
    from bson import ObjectId
    if not current_user.is_admin:
        flash('Only family admins can edit contributions', 'danger')
        return redirect(url_for('contributions.index'))
    
    contribution = Contribution.objects(id=ObjectId(contribution_id)).first()
    if not contribution or contribution.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('contributions.index'))
    
    form = ContributionForm()
    
    if form.validate_on_submit():
        contribution.title = form.title.data
        contribution.amount = form.amount.data
        contribution.frequency = form.frequency.data
        contribution.due_date = form.due_date.data
        contribution.save()
        
        flash('Contribution updated successfully!', 'success')
        return redirect(url_for('contributions.view', contribution_id=contribution_id))
    
    form.title.data = contribution.title
    form.amount.data = float(contribution.amount)
    form.frequency.data = contribution.frequency
    form.due_date.data = contribution.due_date
    
    return render_template('contributions/edit.html', form=form, contribution=contribution)


@contributions.route('/contributions/<contribution_id>/delete')
@login_required
def delete(contribution_id):
    from bson import ObjectId
    if not current_user.is_admin:
        flash('Only family admins can delete contributions', 'danger')
        return redirect(url_for('contributions.index'))
    
    contribution = Contribution.objects(id=ObjectId(contribution_id)).first()
    if not contribution or contribution.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('contributions.index'))
    
    contribution.delete()
    flash('Contribution deleted successfully!', 'success')
    return redirect(url_for('contributions.index'))


@contributions.route('/my-contributions')
@login_required
def my_contributions():
    contributions = Contribution.objects(family_id=current_user.family_id)
    
    my_status = []
    for contrib in contributions:
        payment = Payment.objects(
            contribution_id=contrib.id,
            user_id=current_user.id
        ).first()
        
        status = 'unpaid'
        if payment:
            status = payment.status
        elif contrib.due_date < date.today():
            status = 'overdue'
        
        my_status.append({
            'contribution': contrib,
            'payment': payment,
            'status': status
        })
    
    return render_template('contributions/my_contributions.html', my_status=my_status)


def check_contribution_reminders():
    today = date.today()
    reminder_date = today + timedelta(days=3)
    
    contributions = Contribution.objects(due_date=reminder_date)
    
    for contrib in contributions:
        if contrib.frequency != 'one_time':
            continue
        
        already_paid = Payment.objects(
            contribution_id=contrib.id,
            status='paid'
        ).first()
        
        if not already_paid:
            notify_family(
                contrib.family_id,
                'Contribution Reminder',
                f'Reminder: "{contrib.title}" is due on {contrib.due_date}. Amount: {contrib.amount} CFA',
                'contribution'
            )
