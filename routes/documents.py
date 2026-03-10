from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory
from flask_login import login_required, current_user
from models import Document
from werkzeug.utils import secure_filename
from config import Config
import os
from datetime import datetime

documents = Blueprint('documents', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@documents.route('/documents')
@login_required
def index():
    if not current_user.family_id:
        flash('You need to create or join a family first', 'warning')
        return redirect(url_for('auth.create_family'))
    
    category = request.args.get('category')
    query = Document.objects(family_id=current_user.family_id)
    
    if category:
        query = query.filter(file_type=category)
    
    all_documents = query.order_by('-created_at')
    
    all_docs = Document.objects(family_id=current_user.family_id)
    categories = list(set(d.file_type for d in all_docs if d.file_type))
    
    return render_template('documents/index.html', documents=all_documents, categories=categories)


@documents.route('/documents/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if not current_user.family_id:
        flash('You need to join a family first', 'warning')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        title = request.form.get('title')
        
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            file_type = filename.rsplit('.', 1)[1].lower()
            
            document = Document(
                family_id=current_user.family_id,
                title=title or filename,
                filename=filename,
                file_path=f"/static/uploads/{filename}",
                file_type=file_type,
                uploaded_by=current_user.id
            )
            document.save()
            
            flash('Document uploaded successfully!', 'success')
            return redirect(url_for('documents.index'))
        else:
            flash('File type not allowed', 'danger')
            return redirect(request.url)
    
    return render_template('documents/upload.html')


@documents.route('/documents/<document_id>')
@login_required
def view(document_id):
    from bson import ObjectId
    document = Document.objects(id=ObjectId(document_id)).first()
    if not document or document.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('documents.index'))
    
    return render_template('documents/view.html', document=document)


@documents.route('/documents/<document_id>/download')
@login_required
def download(document_id):
    from bson import ObjectId
    document = Document.objects(id=ObjectId(document_id)).first()
    if not document or document.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('documents.index'))
    
    return redirect(document.file_path)


@documents.route('/documents/<document_id>/delete')
@login_required
def delete(document_id):
    from bson import ObjectId
    if not current_user.is_admin:
        flash('Only family admins can delete documents', 'danger')
        return redirect(url_for('documents.index'))
    
    document = Document.objects(id=ObjectId(document_id)).first()
    if not document or document.family_id != current_user.family_id:
        flash('Access denied', 'danger')
        return redirect(url_for('documents.index'))
    
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'uploads', document.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    document.delete()
    
    flash('Document deleted successfully!', 'success')
    return redirect(url_for('documents.index'))
