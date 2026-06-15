from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Property, PropertyFeature, PropertyImage, ContactInquiry

from werkzeug.utils import secure_filename
from functools import wraps
import os

owner = Blueprint('owner', __name__, url_prefix='/owner')
ALLOWED = {'png','jpg','jpeg','gif','webp'}

def allowed_file(f): return '.' in f and f.rsplit('.',1)[1].lower() in ALLOWED

def require_owner(f):
    @wraps(f)
    def dec(*a, **kw):
        if not current_user.is_authenticated or current_user.role not in ('owner','admin'):
            flash('Owner account required.', 'danger')
            return redirect(url_for('auth.login'))
        if current_user.is_blocked:
            flash('Your account is blocked.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*a, **kw)
    return dec

@owner.route('/dashboard')
@login_required
@require_owner
def dashboard():
    props = Property.query.filter_by(owner_id=current_user.id).order_by(Property.created_at.desc()).all()
    inquiries = (ContactInquiry.query.join(Property, ContactInquiry.property_id == Property.id)
                 .filter(Property.owner_id == current_user.id)
                 .order_by(ContactInquiry.created_at.desc()).limit(10).all())
    unread = sum(1 for i in inquiries if not i.is_read)
    stats = {
        'total': len(props), 'active': sum(1 for p in props if p.is_active),
        'verified': sum(1 for p in props if p.is_verified),
        'inquiries': len(inquiries), 'unread': unread
    }
    return render_template('owner/dashboard.html', properties=props, inquiries=inquiries, stats=stats)

@owner.route('/property/add', methods=['GET','POST'])
@login_required
@require_owner
def add_property():
    if request.method == 'POST':
        f = request.form
        prop = Property(owner_id=current_user.id,
            title=f.get('title'), description=f.get('description'),
            location=f.get('location'), city=f.get('city'),
            area=f.get('area'),
            price=float(f.get('price',0)), bhk=int(f.get('bhk',1)),
            property_type=f.get('property_type'), furnishing=f.get('furnishing'),
            area_sqft=float(f.get('area_sqft')) if f.get('area_sqft') else None)
        db.session.add(prop)
        db.session.flush()
        feat = PropertyFeature(property_id=prop.id,
            balcony='balcony' in f, parking='parking' in f, lift='lift' in f,
            security='security' in f, water_supply='water_supply' in f,
            gym='gym' in f, swimming_pool='swimming_pool' in f,
            wifi='wifi' in f, ac='ac' in f, power_backup='power_backup' in f,
            flooring=f.get('flooring'), ventilation=f.get('ventilation'),
            family_allowed='family_allowed' in f, bachelor_allowed='bachelor_allowed' in f,
            pets_allowed='pets_allowed' in f, veg_only='veg_only' in f)
        db.session.add(feat)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        for i, img in enumerate(request.files.getlist('images')):
            if img and allowed_file(img.filename):
                fname = secure_filename(f"{prop.id}_{i}_{img.filename}")
                img.save(os.path.join(upload_folder, fname))
                cap = request.form.getlist('captions')[i] if i < len(request.form.getlist('captions')) else ''
                db.session.add(PropertyImage(property_id=prop.id,
                    image_url=f'/static/images/{fname}', caption=cap))
        db.session.commit()
        flash('Property listed! Awaiting admin verification.', 'success')
        return redirect(url_for('owner.dashboard'))
    return render_template('owner/add_property.html')

@owner.route('/property/edit/<int:pid>', methods=['GET','POST'])
@login_required
@require_owner
def edit_property(pid):
    prop = Property.query.get_or_404(pid)
    if prop.owner_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('owner.dashboard'))
    if request.method == 'POST':
        f = request.form
        prop.title=f.get('title'); prop.description=f.get('description')
        prop.location=f.get('location'); prop.city=f.get('city')
        prop.area=f.get('area')
        prop.price=float(f.get('price',0)); prop.bhk=int(f.get('bhk',1))
        prop.property_type=f.get('property_type'); prop.furnishing=f.get('furnishing')
        prop.area_sqft=float(f.get('area_sqft')) if f.get('area_sqft') else None
        if prop.features:
            feat=prop.features
            for attr in ['balcony','parking','lift','security','water_supply','gym','ac','wifi','power_backup','family_allowed','bachelor_allowed','pets_allowed','veg_only']:
                setattr(feat, attr, attr in f)
        db.session.commit()
        flash('Property updated!', 'success')
        return redirect(url_for('owner.dashboard'))
    return render_template('owner/edit_property.html', property=prop)

@owner.route('/property/delete/<int:pid>', methods=['POST'])
@login_required
@require_owner
def delete_property(pid):
    prop = Property.query.get_or_404(pid)
    if prop.owner_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('owner.dashboard'))
    prop.is_active = False
    db.session.commit()
    flash('Property removed.', 'info')
    return redirect(url_for('owner.dashboard'))

@owner.route('/inquiry/<int:iid>/read', methods=['POST'])
@login_required
@require_owner
def mark_read(iid):
    inq = ContactInquiry.query.get_or_404(iid)
    inq.is_read = True
    db.session.commit()
    return redirect(url_for('owner.dashboard'))
