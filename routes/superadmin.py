"""
Super Admin Panel — uses simple session, NOT Flask-Login.
Username and password are stored in app.config only.
No database lookup needed.
"""
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, session, current_app)
from extensions import db
from models import User, Property
from functools import wraps

superadmin = Blueprint('superadmin', __name__, url_prefix='/superadmin')

SA_SESSION_KEY = 'sa_logged_in'

def sa_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get(SA_SESSION_KEY):
            flash('Please log in to access the Super Admin panel.', 'danger')
            return redirect(url_for('superadmin.login'))
        return f(*args, **kwargs)
    return decorated

# ── LOGIN / LOGOUT ──────────────────────────────────────────────────────────

@superadmin.route('/login', methods=['GET', 'POST'])
def login():
    if session.get(SA_SESSION_KEY):
        return redirect(url_for('superadmin.dashboard'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if (username == current_app.config['SA_USERNAME'] and
                password == current_app.config['SA_PASSWORD']):
            session[SA_SESSION_KEY] = True
            session.permanent = True
            return redirect(url_for('superadmin.dashboard'))
        else:
            error = 'Wrong username or password.'

    return render_template('superadmin/login.html', error=error)


@superadmin.route('/logout')
def logout():
    session.pop(SA_SESSION_KEY, None)
    flash('Logged out of Super Admin panel.', 'info')
    return redirect(url_for('superadmin.login'))


# ── DASHBOARD ────────────────────────────────────────────────────────────────

@superadmin.route('/dashboard')
@sa_login_required
def dashboard():
    stats = {
        'total_users':       User.query.count(),
        'blocked_users':     User.query.filter_by(is_blocked=True).count(),
        'owners':            User.query.filter_by(role='owner').count(),
        'tenants':           User.query.filter_by(role='tenant').count(),
        'total_properties':  Property.query.count(),
        'hidden_properties': Property.query.filter_by(is_hidden=True).count(),
        'active_properties': Property.query.filter_by(is_active=True, is_hidden=False).count(),
        'unverified':        Property.query.filter_by(is_verified=False, is_active=True).count(),
    }
    recent_users  = User.query.order_by(User.created_at.desc()).limit(6).all()
    recent_props  = Property.query.order_by(Property.created_at.desc()).limit(6).all()
    return render_template('superadmin/dashboard.html',
                           stats=stats,
                           recent_users=recent_users,
                           recent_props=recent_props)


# ── USERS ────────────────────────────────────────────────────────────────────

@superadmin.route('/users')
@sa_login_required
def users():
    role_filter = request.args.get('role', '')
    q = User.query
    if role_filter:
        q = q.filter_by(role=role_filter)
    all_users = q.order_by(User.created_at.desc()).all()
    return render_template('superadmin/users.html',
                           users=all_users, role_filter=role_filter)


@superadmin.route('/user/block/<int:uid>', methods=['POST'])
@sa_login_required
def block_user(uid):
    user = User.query.get_or_404(uid)
    user.is_blocked = not user.is_blocked
    db.session.commit()
    action = 'blocked' if user.is_blocked else 'unblocked'
    flash(f'User "{user.name}" has been {action}.', 'success')
    return redirect(url_for('superadmin.users'))


@superadmin.route('/user/delete/<int:uid>', methods=['POST'])
@sa_login_required
def delete_user(uid):
    user = User.query.get_or_404(uid)
    for p in user.properties:
        p.is_active = False
        p.is_hidden = True
    db.session.commit()
    flash(f'User "{user.name}" removed and properties hidden.', 'success')
    return redirect(url_for('superadmin.users'))


# ── PROPERTIES ───────────────────────────────────────────────────────────────

@superadmin.route('/properties')
@sa_login_required
def properties():
    f = request.args.get('filter', 'all')
    q = Property.query
    if f == 'hidden':
        q = q.filter_by(is_hidden=True)
    elif f == 'active':
        q = q.filter_by(is_active=True, is_hidden=False)
    elif f == 'unverified':
        q = q.filter_by(is_verified=False, is_active=True, is_hidden=False)
    props = q.order_by(Property.created_at.desc()).all()
    return render_template('superadmin/properties.html',
                           properties=props, filter_by=f)


@superadmin.route('/property/hide/<int:pid>', methods=['POST'])
@sa_login_required
def hide_property(pid):
    prop = Property.query.get_or_404(pid)
    prop.is_hidden = not prop.is_hidden
    db.session.commit()
    flash(f'Property is now {"hidden" if prop.is_hidden else "visible"}.', 'success')
    return redirect(url_for('superadmin.properties'))


@superadmin.route('/property/remove/<int:pid>', methods=['POST'])
@sa_login_required
def remove_property(pid):
    prop = Property.query.get_or_404(pid)
    prop.is_active = False
    prop.is_hidden = True
    db.session.commit()
    flash(f'Property "{prop.title}" removed.', 'success')
    return redirect(url_for('superadmin.properties'))


@superadmin.route('/property/verify/<int:pid>', methods=['POST'])
@sa_login_required
def verify_property(pid):
    prop = Property.query.get_or_404(pid)
    prop.is_verified = True
    db.session.commit()
    flash(f'Property "{prop.title}" verified.', 'success')
    return redirect(url_for('superadmin.properties'))
