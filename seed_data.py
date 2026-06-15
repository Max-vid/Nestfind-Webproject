"""
Seeds only users — NO properties.
Properties are added exclusively by owners through the platform.
"""
from app import create_app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()

    users = [
        User(name='Admin',        email='admin@nestfind.com',
             password=generate_password_hash('admin123'),  role='admin'),
        User(name='Demo Owner',   email='owner@nestfind.com',
             password=generate_password_hash('owner123'),  role='owner'),
        User(name='Demo Tenant',  email='tenant@nestfind.com',
             password=generate_password_hash('tenant123'), role='tenant'),
    ]
    db.session.add_all(users)
    db.session.commit()

    print("\n✅ Users created. NO demo properties added.")
    print("   Owners must list their own properties through the platform.\n")
    print("   Super Admin : username = admin   |  password = nestfind123")
    print("   Super Admin URL : http://localhost:5000/superadmin/login")
    print("   Admin   : admin@nestfind.com  / admin123")
    print("   Owner   : owner@nestfind.com  / owner123")
    print("   Tenant  : tenant@nestfind.com / tenant123")
