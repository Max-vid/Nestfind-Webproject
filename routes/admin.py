from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import User, Property, Review, ContactInquiry, Wishlist
from utils.data_mining import cluster_users, find_association_rules
from functools import wraps

admin = Blueprint('admin', __name__, url_prefix='/admin')

def require_admin(f):
    @wraps(f)
    def dec(*a, **kw):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*a, **kw)
    return dec

@admin.route('/dashboard')
@login_required
@require_admin
def dashboard():
    stats = {
        'total_users': User.query.count(),
        'tenants': User.query.filter_by(role='tenant').count(),
        'owners': User.query.filter_by(role='owner').count(),
        'total_properties': Property.query.count(),
        'active_properties': Property.query.filter_by(is_active=True).count(),
        'pending_verification': Property.query.filter_by(is_verified=False, is_active=True).count(),
        'total_reviews': Review.query.count(),
        'total_inquiries': ContactInquiry.query.count(),
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    pending_props = Property.query.filter_by(is_verified=False, is_active=True).order_by(Property.created_at.desc()).limit(5).all()
    users_data = []
    for u in User.query.filter_by(role='tenant').all():
        pref = u.preferences
        users_data.append({'id': u.id, 'name': u.name,
            'min_budget': pref.min_budget if pref else 5000,
            'max_budget': pref.max_budget if pref else 20000,
            'preferred_bhk': int(pref.preferred_bhk) if pref and pref.preferred_bhk else 2})
    clusters = cluster_users(users_data) if len(users_data) >= 4 else []
    wishlists = [{'user_id': w.user_id, 'property_id': w.property_id} for w in Wishlist.query.all()]
    assoc_rules = find_association_rules(wishlists)
    return render_template('admin/dashboard.html', stats=stats, recent_users=recent_users,
                           pending_props=pending_props, clusters=clusters, assoc_rules=assoc_rules[:5])

@admin.route('/properties')
@login_required
@require_admin
def properties():
    props = Property.query.order_by(Property.created_at.desc()).all()
    return render_template('admin/properties.html', properties=props)

@admin.route('/property/verify/<int:pid>', methods=['POST'])
@login_required
@require_admin
def verify_property(pid):
    prop = Property.query.get_or_404(pid)
    prop.is_verified = True
    db.session.commit()
    flash(f'"{prop.title}" verified!', 'success')
    return redirect(url_for('admin.properties'))

@admin.route('/property/toggle/<int:pid>', methods=['POST'])
@login_required
@require_admin
def toggle_property(pid):
    prop = Property.query.get_or_404(pid)
    prop.is_active = not prop.is_active
    db.session.commit()
    flash(f'Property {"activated" if prop.is_active else "deactivated"}.', 'info')
    return redirect(url_for('admin.properties'))

@admin.route('/users')
@login_required
@require_admin
def users():
    all_users = User.query.filter(User.role != 'superadmin').order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)

@admin.route('/analytics')
@login_required
@require_admin
def analytics():
    props = Property.query.filter_by(is_active=True).all()
    price_buckets = {'<5K':0,'5K-10K':0,'10K-20K':0,'20K-50K':0,'>50K':0}
    bhk_dist = {'1':0,'2':0,'3':0,'4+':0}
    city_dist = {}
    for p in props:
        if p.price < 5000: price_buckets['<5K'] += 1
        elif p.price < 10000: price_buckets['5K-10K'] += 1
        elif p.price < 20000: price_buckets['10K-20K'] += 1
        elif p.price < 50000: price_buckets['20K-50K'] += 1
        else: price_buckets['>50K'] += 1
        bhk_dist[str(p.bhk) if p.bhk <= 3 else '4+'] = bhk_dist.get(str(p.bhk) if p.bhk <= 3 else '4+', 0) + 1
        city_dist[p.city] = city_dist.get(p.city, 0) + 1
    top_cities = sorted(city_dist.items(), key=lambda x: x[1], reverse=True)[:8]
    return render_template('admin/analytics.html', price_buckets=price_buckets,
                           bhk_dist=bhk_dist, top_cities=top_cities, total_props=len(props))
