from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User, Family, Notification
from forms import LoginForm, RegisterForm, CreateFamilyForm, AddMemberForm
from datetime import datetime

auth = Blueprint('auth', __name__)


@auth.route('/')
def index():
    return render_template('landing.html')


@auth.route('/home')
def home():
    return render_template('landing.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and current_user.family_id:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Invalid email or password', 'danger')
    return render_template('auth/login.html', form=form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated and current_user.family_id:
        return redirect(url_for('main.dashboard'))
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.objects(email=form.email.data).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))
        
        user = User(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        user.save()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/create-family', methods=['GET', 'POST'])
@login_required
def create_family():
    if current_user.family_id:
        flash('You are already part of a family', 'warning')
        return redirect(url_for('main.dashboard'))
    
    form = CreateFamilyForm()
    if form.validate_on_submit():
        family = Family(
            name=form.family_name.data,
            admin_id=current_user.id
        )
        family.save()
        
        current_user.family_id = family.id
        current_user.is_admin = True
        current_user.family_role = 'admin'
        current_user.save()
        
        flash('Family created successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('auth/create_family.html', form=form)


@auth.route('/join-family', methods=['GET', 'POST'])
@login_required
def join_family():
    if current_user.family_id:
        flash('You are already part of a family', 'warning')
        return redirect(url_for('main.dashboard'))
    return render_template('auth/join_family.html')


@auth.route('/add-member', methods=['GET', 'POST'])
@login_required
def add_member():
    if not current_user.is_admin:
        flash('Only family admins can add members', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = AddMemberForm()
    if form.validate_on_submit():
        existing_user = User.objects(email=form.email.data).first()
        
        if existing_user:
            existing_user.family_id = current_user.family_id
            existing_user.family_role = form.family_role.data or 'member'
            existing_user.save()
            flash(f'{existing_user.name} has been added to the family!', 'success')
        else:
            user = User(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                family_role=form.family_role.data or 'member',
                family_id=current_user.family_id,
                is_admin=False
            )
            user.set_password(form.password.data)
            user.save()
            flash(f'{user.name} has been invited to the family!', 'success')
        
        return redirect(url_for('main.members'))
    
    return render_template('auth/add_member.html', form=form)


@auth.route('/members')
@login_required
def members():
    if not current_user.family_id:
        flash('You need to create or join a family first', 'warning')
        return redirect(url_for('auth.create_family'))
    
    family = Family.objects.get(id=current_user.family_id)
    all_users = User.objects(family_id=current_user.family_id)
    return render_template('auth/members.html', members=all_users, family=family)


@auth.route('/remove-member/<user_id>')
@login_required
def remove_member(user_id):
    if not current_user.is_admin:
        flash('Only family admins can remove members', 'danger')
        return redirect(url_for('main.dashboard'))
    
    from bson import ObjectId
    user = User.objects(id=ObjectId(user_id)).first()
    if user and user.family_id == current_user.family_id:
        if user.id == current_user.id:
            flash('You cannot remove yourself', 'danger')
        else:
            user.family_id = None
            user.family_role = None
            user.save()
            flash(f'{user.name} has been removed from the family', 'success')
    return redirect(url_for('auth.members'))
