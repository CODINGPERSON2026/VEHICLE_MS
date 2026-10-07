from models.user import User, Role
from database.db_init import db

def test_first_time_setup(client, app):
    # Initial setup when 0 users exist
    with app.app_context():
        assert User.query.count() == 0

    resp = client.post('/first-time-setup', data={
        'username': 'superadmin',
        'full_name': 'Super Administrator',
        'email': 'super@gate.local',
        'password': 'SecurePassword123',
        'confirm_password': 'SecurePassword123'
    }, follow_redirects=True)

    assert resp.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username='superadmin').first()
        assert user is not None
        assert user.role == Role.ADMIN
        assert user.check_password('SecurePassword123')

def test_login_success(client, admin_user):
    resp = client.post('/login', data={
        'username': 'admin',
        'password': 'AdminPass123!'
    }, follow_redirects=True)
    
    assert resp.status_code == 200
    assert b"Welcome back" not in resp.data

def test_login_invalid_credentials(client, admin_user):
    resp = client.post('/login', data={
        'username': 'admin',
        'password': 'WrongPassword'
    }, follow_redirects=True)
    
    assert resp.status_code == 200
    assert b"Invalid username or password." in resp.data

def test_logout(client, admin_user):
    client.post('/login', data={'username': 'admin', 'password': 'AdminPass123!'})
    resp = client.get('/logout', follow_redirects=True)
    assert resp.status_code == 200
    assert b"You have been logged out successfully." in resp.data
