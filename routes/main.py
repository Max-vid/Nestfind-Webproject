from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import current_user, login_required
from extensions import db
from models import Property, Wishlist, Review, TenantPreference
from utils.data_mining import get_content_based_recommendations, get_preference_based_recommendations

main = Blueprint('main', __name__)

def prop_dict(p):
    feat = p.features
    avg = sum(r.rating for r in p.reviews) / len(p.reviews) if p.reviews else 0
    return {
        'id': p.id, 'title': p.title, 'description': p.description or '',
        'location': p.location, 'city': p.city, 'area': p.area or '', 'price': p.price,
        'bhk': p.bhk, 'property_type': p.property_type or '',
        'furnishing': p.furnishing or '',
        'area_sqft': p.area_sqft, 'is_verified': p.is_verified,
        'created_at': p.created_at.strftime('%d %b %Y') if p.created_at else '',
        'avg_rating': round(avg, 1), 'review_count': len(p.reviews),
        'balcony': feat.balcony if feat else False,
        'parking': feat.parking if feat else False,
        'gym': feat.gym if feat else False,
        'wifi': feat.wifi if feat else False,
        'ac': feat.ac if feat else False,
        'lift': feat.lift if feat else False,
        'security': feat.security if feat else False,
        'water_supply': feat.water_supply if feat else False,
        'swimming_pool': feat.swimming_pool if feat else False,
        'power_backup': feat.power_backup if feat else False,
        'family_allowed': feat.family_allowed if feat else True,
        'bachelor_allowed': feat.bachelor_allowed if feat else True,
        'pets_allowed': feat.pets_allowed if feat else False,
        'veg_only': feat.veg_only if feat else False,
        'flooring': feat.flooring if feat else '',
        'images': [{'url': i.image_url, 'caption': i.caption} for i in p.images],
        'owner_name': p.owner.name if p.owner else 'Unknown',
        'owner_id': p.owner_id,
    }

@main.route('/')
def index():
    # Only show properties that owners have actively listed (verified + active + not hidden)
    featured = Property.query.filter_by(
        is_active=True, is_verified=True, is_hidden=False
    ).order_by(Property.created_at.desc()).limit(6).all()
    cities = [c[0] for c in db.session.query(Property.city).filter_by(
        is_active=True, is_verified=True, is_hidden=False).distinct().all()]
    total_listed = Property.query.filter_by(is_active=True, is_verified=True, is_hidden=False).count()
    # Build city->areas mapping for dynamic area dropdown
    city_areas = {}
    for p in Property.query.filter(
        Property.is_active==True, Property.is_hidden==False, Property.area != None, Property.area != ''
    ).all():
        city_areas.setdefault(p.city, set()).add(p.area)
    city_areas = {k: sorted(v) for k, v in city_areas.items()}
    return render_template('main/index.html',
                           featured=[prop_dict(p) for p in featured],
                           cities=cities,
                           city_areas=city_areas,
                           total_listed=total_listed)

@main.route('/search')
def search():
    city = request.args.get('city','').strip()
    area = request.args.get('area','').strip()
    min_p = request.args.get('min_price','').strip()
    max_p = request.args.get('max_price','').strip()
    bhk   = request.args.get('bhk','').strip()
    ptype = request.args.get('property_type','').strip()
    furn  = request.args.get('furnishing','').strip()
    amenities = request.args.getlist('amenities')
    sort_by   = request.args.get('sort_by','newest')

    has_filters = any([city, area, min_p, max_p, bhk, ptype, furn, amenities])
    cities = [c[0] for c in db.session.query(Property.city).filter_by(
        is_active=True, is_hidden=False).distinct().all()]
    # Build city->areas mapping
    city_areas = {}
    for p in Property.query.filter(
        Property.is_active==True, Property.is_hidden==False, Property.area != None, Property.area != ''
    ).all():
        city_areas.setdefault(p.city, set()).add(p.area)
    city_areas = {k: sorted(v) for k, v in city_areas.items()}

    if not has_filters:
        return render_template('main/search.html',
                               properties=[], searched=False,
                               cities=cities, city_areas=city_areas, filters=request.args,
                               recommendations=[])

    # Only show owner-listed, active, not hidden properties
    q = Property.query.filter_by(is_active=True, is_hidden=False)
    if city:
        q = q.filter(Property.city.ilike(f'%{city}%'))
    if area:
        # Match exact area or nearby (area name appears in location or area field)
        q = q.filter(
            db.or_(
                Property.area.ilike(f'%{area}%'),
                Property.location.ilike(f'%{area}%')
            )
        )
    if min_p:
        try: q = q.filter(Property.price >= float(min_p))
        except: pass
    if max_p:
        try: q = q.filter(Property.price <= float(max_p))
        except: pass
    if bhk:
        try: q = q.filter(Property.bhk == int(bhk))
        except: pass
    if ptype:
        q = q.filter(Property.property_type == ptype)
    if furn:
        q = q.filter(Property.furnishing == furn)

    if sort_by == 'price_asc':
        q = q.order_by(Property.price.asc())
    elif sort_by == 'price_desc':
        q = q.order_by(Property.price.desc())
    else:
        q = q.order_by(Property.created_at.desc())

    props = q.all()
    if amenities:
        props = [p for p in props if p.features and
                 all(getattr(p.features, a, False) for a in amenities)]

    props_data = [prop_dict(p) for p in props]

    recommendations = []
    if current_user.is_authenticated and current_user.preferences:
        pref = current_user.preferences
        up = {'city': pref.preferred_city, 'min_budget': pref.min_budget,
              'max_budget': pref.max_budget, 'bhk': pref.preferred_bhk,
              'property_type': pref.preferred_type,
              'is_family': pref.is_family, 'has_pets': pref.has_pets}
        rec_ids = get_preference_based_recommendations(up, props_data)
        recommendations = [p for p in props_data if p['id'] in rec_ids][:4]

    return render_template('main/search.html',
                           properties=props_data, searched=True,
                           recommendations=recommendations,
                           cities=cities, city_areas=city_areas, filters=request.args)

@main.route('/property/<int:pid>')
def property_detail(pid):
    p = Property.query.get_or_404(pid)
    if p.is_hidden or not p.is_active:
        flash('This property is not available.', 'warning')
        return redirect(url_for('main.index'))
    pd = prop_dict(p)
    all_props = [prop_dict(x) for x in
                 Property.query.filter_by(is_active=True, is_hidden=False).all()]
    similar_ids = get_content_based_recommendations(pid, all_props, top_n=4)
    similar = [x for x in all_props if x['id'] in similar_ids]
    in_wishlist = False
    if current_user.is_authenticated:
        in_wishlist = bool(Wishlist.query.filter_by(
            user_id=current_user.id, property_id=pid).first())
    reviews = Review.query.filter_by(property_id=pid)\
        .order_by(Review.created_at.desc()).all()
    reviews_data = [{'user_name': r.user.name, 'rating': r.rating,
                     'comment': r.comment,
                     'date': r.created_at.strftime('%d %b %Y')} for r in reviews]
    return render_template('main/property_detail.html',
                           property=pd, similar=similar,
                           reviews=reviews_data, in_wishlist=in_wishlist)

@main.route('/wishlist/toggle/<int:pid>', methods=['POST'])
@login_required
def toggle_wishlist(pid):
    ex = Wishlist.query.filter_by(user_id=current_user.id, property_id=pid).first()
    if ex:
        db.session.delete(ex)
        db.session.commit()
        return jsonify({'status': 'removed'})
    db.session.add(Wishlist(user_id=current_user.id, property_id=pid))
    db.session.commit()
    return jsonify({'status': 'added'})

@main.route('/wishlist')
@login_required
def wishlist():
    items = Wishlist.query.filter_by(user_id=current_user.id).all()
    props = [prop_dict(w.property) for w in items
             if w.property and not w.property.is_hidden and w.property.is_active]
    return render_template('main/wishlist.html', properties=props)

@main.route('/review/<int:pid>', methods=['POST'])
@login_required
def add_review(pid):
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment','').strip()
    if not rating:
        flash('Please select a rating.', 'danger')
        return redirect(url_for('main.property_detail', pid=pid))
    ex = Review.query.filter_by(user_id=current_user.id, property_id=pid).first()
    if ex:
        ex.rating = rating; ex.comment = comment
    else:
        db.session.add(Review(user_id=current_user.id, property_id=pid,
                              rating=rating, comment=comment))
    db.session.commit()
    flash('Review submitted!', 'success')
    return redirect(url_for('main.property_detail', pid=pid))
