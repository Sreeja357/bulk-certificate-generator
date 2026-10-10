import sys
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).resolve().parent.parent

# Add the project root to Python's import path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()