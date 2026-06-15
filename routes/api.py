from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import Property, TenantPreference, ContactInquiry

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/save-preferences', methods=['POST'])
@login_required
def save_preferences():
    data = request.get_json() or {}
    pref = current_user.preferences
    if not pref:
        pref = TenantPreference(user_id=current_user.id)
        db.session.add(pref)
    pref.preferred_city = data.get('city')
    pref.min_budget = data.get('min_budget')
    pref.max_budget = data.get('max_budget')
    pref.preferred_bhk = data.get('bhk')
    pref.preferred_type = data.get('property_type')
    pref.is_family = data.get('is_family', False)
    pref.has_pets = data.get('has_pets', False)
    pref.is_veg = data.get('is_veg', False)
    db.session.commit()
    return jsonify({'status': 'saved'})

@api.route('/contact', methods=['POST'])
@login_required
def contact_owner():
    data = request.get_json() or {}
    db.session.add(ContactInquiry(property_id=data.get('property_id'),
                                   tenant_id=current_user.id,
                                   message=data.get('message','')))
    db.session.commit()
    return jsonify({'status': 'sent'})
