from flask import Blueprint

def register_routes(app):
    from .page_routes import page_bp
    from .auth_routes import auth_bp
    
    app.register_blueprint(page_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
