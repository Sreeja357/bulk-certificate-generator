
from unittest.mock import MagicMock

from app import create_app
import os

def test_create_job_validation_error():
    app = create_app()
    app.config["TESTING"] = True

    client = app.test_client()

    response = client.post(
        "/api/jobs",
        json={
            "event_name": "",
            "certificate_title": "Certificate of Completion",
            "date": "2026-10-09",
            "recipients": [
                {
                    "name": "Sreeja",
                    "email": "sreeja@example.com"
                }
            ]
        }
    )

    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_create_job_success(mocker):
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    # Mock the database connection
    mock_db = MagicMock()
    mock_cursor = MagicMock()

    mock_db.cursor.return_value = mock_cursor
    mock_cursor.lastrowid = 101

    mocker.patch(
        "app.routes.DatabaseConnection",
        return_value=mock_db
    )

    # Prevent a real background thread from starting
    mock_thread = mocker.patch("app.routes.threading.Thread")

    response = client.post(
        "/api/jobs",
        json={
            "event_name": "Python Workshop",
            "certificate_title": "Certificate of Completion",
            "date": "2026-10-09",
            "recipients": [
                {
                    "name": "Sreeja",
                    "email": "sreeja@example.com"
                },
                {
                    "name": "Rahul Kumar",
                    "email": "rahul@example.com"
                }
            ]
        }
    )

    # Check the API response
    assert response.status_code == 201

    data = response.get_json()

    assert data["success"] is True
    assert data["job_id"] == 101
    assert data["total_recipients"] == 2
    assert data["status"] == "pending"

    # Check that SQL was executed and committed
    assert mock_cursor.execute.call_count == 3
    mock_db.commit.assert_called_once()

    # Check that background processing was started
    mock_thread.assert_called_once()
    mock_thread.return_value.start.assert_called_once()



def test_get_job_status_success(mocker):
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    mock_db = MagicMock()
    mock_cursor = MagicMock()

    mock_db.cursor.return_value = mock_cursor

    # Simulate a job retrieved from MySQL
    mock_cursor.fetchone.return_value = {
        "jobid": 101,
        "event_name": "Python Workshop",
        "certificate_title": "Certificate of Completion",
        "certificate_date": "2026-10-09",
        "status": "processing",
        "total_recipients": 5,
        "completed_count": 3,
        "successful_count": 2,
        "failed_count": 1,
    }

    mocker.patch(
        "app.routes.DatabaseConnection",
        return_value=mock_db
    )

    response = client.get("/api/jobs/101")

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["job_id"] == 101
    assert data["status"] == "processing"
    assert data["total_recipients"] == 5
    assert data["completed"] == 3
    assert data["successful"] == 2
    assert data["failed"] == 1

    mock_cursor.execute.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_db.close.assert_called_once()


def test_get_job_status_not_found(mocker):
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    mock_db = MagicMock()
    mock_cursor = MagicMock()

    mock_db.cursor.return_value = mock_cursor

    # Simulate a job ID that does not exist
    mock_cursor.fetchone.return_value = None

    mocker.patch(
        "app.routes.DatabaseConnection",
        return_value=mock_db
    )

    response = client.get("/api/jobs/999999")

    assert response.status_code == 404

    data = response.get_json()

    assert data["success"] is False
    assert data["message"] == "Job not found."


def test_get_job_results_success(mocker):
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    mock_db = MagicMock()
    mock_cursor = MagicMock()

    mock_db.cursor.return_value = mock_cursor

    # First fetchone() checks whether the job exists.
    mock_cursor.fetchone.return_value = {"jobid": 101}

    # Simulate two certificate results.
    mock_cursor.fetchall.return_value = [
        {
            "certificateid": 201,
            "recipient_name": "Sreeja",
            "recipient_email": "sreeja@example.com",
            "status": "success",
            "file_path": "certificates/generated/certificate_201.pdf",
            "error_message": None,
        },
        {
            "certificateid": 202,
            "recipient_name": "Rahul",
            "recipient_email": "rahul@example.com",
            "status": "failed",
            "file_path": None,
            "error_message": "Test generation failure",
        },
    ]

    mocker.patch(
        "app.routes.DatabaseConnection",
        return_value=mock_db
    )

    response = client.get("/api/jobs/101/results")

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["job_id"] == 101
    assert len(data["results"]) == 2

    assert data["results"][0]["recipient_name"] == "Sreeja"
    assert data["results"][0]["status"] == "success"
    assert data["results"][0]["error_message"] is None

    assert data["results"][1]["recipient_name"] == "Rahul"
    assert data["results"][1]["status"] == "failed"
    assert data["results"][1]["error_message"] == (
        "Test generation failure"
    )

    assert mock_cursor.execute.call_count == 2

    mock_cursor.close.assert_called_once()
    mock_db.close.assert_called_once()


def test_get_job_results_not_found(mocker):
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    mock_db = MagicMock()
    mock_cursor = MagicMock()

    mock_db.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    mocker.patch(
        "app.routes.DatabaseConnection",
        return_value=mock_db
    )

    response = client.get("/api/jobs/999999/results")

    assert response.status_code == 404

    data = response.get_json()

    assert data["success"] is False
    assert data["message"] == "Job not found."


def test_get_certificate_success(client, mocker, tmp_path):
    from pathlib import Path

    # Create the same folder structure as the actual project
    app_folder = tmp_path / "app"
    app_folder.mkdir()

    generated_folder = tmp_path / "certificates" / "generated"
    generated_folder.mkdir(parents=True)

    pdf_file = generated_folder / "test_certificate.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 test certificate content")

    # Make the route calculate tmp_path as the project root
    mocker.patch(
        "app.routes.__file__",
        str(app_folder / "routes.py")
    )

    mock_db = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()

    mock_db.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {
        "certificateid": 201,
        "recipient_name": "Test User",
        "recipient_email": "test@example.com",
        "status": "success",
        "file_path": str(pdf_file),
        "error_message": None,
    }

    mocker.patch(
        "app.routes.DatabaseConnection",
        return_value=mock_db
    )

    response = client.get("/api/certificates/201")

    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF-1.4")


def test_get_certificate_not_found(mocker):
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_db.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    mocker.patch(
        "app.routes.DatabaseConnection",
        return_value=mock_db
    )

    response = client.get("/api/certificates/999999")

    assert response.status_code == 404

    data = response.get_json()
    assert data["success"] is False
    assert data["message"] == "Certificate not found."


def test_get_certificate_not_ready(mocker):
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_db.cursor.return_value = mock_cursor

    mock_cursor.fetchone.return_value = {
        "certificateid": 202,
        "recipient_name": "Rahul",
        "recipient_email": "rahul@example.com",
        "status": "failed",
        "file_path": None,
        "error_message": "Test generation failure",
    }

    mocker.patch(
        "app.routes.DatabaseConnection",
        return_value=mock_db
    )

    response = client.get("/api/certificates/202")

    assert response.status_code == 404

    data = response.get_json()
    assert data["success"] is False
    assert data["message"] == "Certificate is not available."
    assert data["status"] == "failed"
