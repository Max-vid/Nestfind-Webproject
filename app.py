from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'nestfind-v3-secret-2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nestfind.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # ── Superadmin hardcoded credentials (only you know these) ──
    app.config['SA_USERNAME'] = 'admin'
    app.config['SA_PASSWORD'] = 'nestfind123'

    from extensions import db, login_manager, bcrypt
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    with app.app_context():
        from models import (User, Property, PropertyFeature, PropertyImage,
                            TenantPreference, Wishlist, Review, ContactInquiry)
        db.create_all()
        # Migrate: add area column if missing
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        cols = [c['name'] for c in inspector.get_columns('properties')]
        if 'area' not in cols:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE properties ADD COLUMN area VARCHAR(150)"))
                conn.commit()

    from routes.auth import auth
    from routes.main import main
    from routes.owner import owner
    from routes.admin import admin
    from routes.superadmin import superadmin
    from routes.api import api

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(owner)
    app.register_blueprint(admin)
    app.register_blueprint(superadmin)
    app.register_blueprint(api)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
