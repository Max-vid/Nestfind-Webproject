from flask_login import UserMixin
from datetime import datetime
from extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='tenant')  # tenant / owner / admin
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    preferences = db.relationship('TenantPreference', backref='user', uselist=False, lazy=True)
    properties = db.relationship('Property', backref='owner', lazy=True, foreign_keys='Property.owner_id')
    wishlist = db.relationship('Wishlist', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='user', lazy=True)

class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    area = db.Column(db.String(150))  # area/locality within the city
    price = db.Column(db.Float, nullable=False)
    bhk = db.Column(db.Integer, nullable=False)
    property_type = db.Column(db.String(50))
    furnishing = db.Column(db.String(50))
    area_sqft = db.Column(db.Float)
    available_from = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    is_hidden = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    features = db.relationship('PropertyFeature', backref='property', uselist=False, lazy=True)
    images = db.relationship('PropertyImage', backref='property', lazy=True)
    wishlist_items = db.relationship('Wishlist', backref='property', lazy=True)
    reviews = db.relationship('Review', backref='property', lazy=True)

class PropertyFeature(db.Model):
    __tablename__ = 'property_features'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    balcony = db.Column(db.Boolean, default=False)
    parking = db.Column(db.Boolean, default=False)
    lift = db.Column(db.Boolean, default=False)
    security = db.Column(db.Boolean, default=False)
    water_supply = db.Column(db.Boolean, default=False)
    gym = db.Column(db.Boolean, default=False)
    swimming_pool = db.Column(db.Boolean, default=False)
    wifi = db.Column(db.Boolean, default=False)
    ac = db.Column(db.Boolean, default=False)
    power_backup = db.Column(db.Boolean, default=False)
    flooring = db.Column(db.String(50))
    ventilation = db.Column(db.String(50))
    family_allowed = db.Column(db.Boolean, default=True)
    bachelor_allowed = db.Column(db.Boolean, default=True)
    pets_allowed = db.Column(db.Boolean, default=False)
    veg_only = db.Column(db.Boolean, default=False)

class PropertyImage(db.Model):
    __tablename__ = 'property_images'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    image_url = db.Column(db.String(300), nullable=False)
    caption = db.Column(db.String(100))

class TenantPreference(db.Model):
    __tablename__ = 'tenant_preferences'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    preferred_city = db.Column(db.String(100))
    min_budget = db.Column(db.Float)
    max_budget = db.Column(db.Float)
    preferred_bhk = db.Column(db.String(50))
    preferred_type = db.Column(db.String(50))
    is_family = db.Column(db.Boolean, default=False)
    has_pets = db.Column(db.Boolean, default=False)
    is_veg = db.Column(db.Boolean, default=False)

class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContactInquiry(db.Model):
    __tablename__ = 'contact_inquiries'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    prop = db.relationship('Property', foreign_keys=[property_id])
    tenant = db.relationship('User', foreign_keys=[tenant_id])
