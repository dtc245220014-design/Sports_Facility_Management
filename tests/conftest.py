import pytest
import os
from app import create_app
from extensions import db
from models.models import TimeSlot, Court, CourtType

@pytest.fixture(scope='session')
def app():
    app = create_app({
        'TESTING': True
    })
    return app

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    with app.app_context():
        yield db.session

