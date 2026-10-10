from app.validators import validate_email, validate_job_data

def test_valid_email():
    assert validate_email("sreeja@example.com") is True

def test_invalid_email():
    assert validate_email("sreeja@example") is False

def test_valid_job_data():
    data = {
        "event_name": "Python Workshop",
        "certificate_title": "Certificate of Completion",
        "date": "2026-10-08",
        "recipients": [
            {
                "name": "Sreeja",
                "email": "sreeja@example.com"
            }
        ]
    }
    errors = validate_job_data(data)
    assert errors == []

def test_missing_event_name():
    data = {
        "certificate_title": "Certificate of Completion",
        "date": "2026-10-08",
        "recipients": [
            {
                "name": "Sreeja",
                "email": "sreeja@example.com"
            }
        ]
    }
    errors = validate_job_data(data)
    assert "event_name is required." in errors

def test_invalid_recipient_email():
    data = {
        "event_name": "Python Workshop",
        "certificate_title": "Certificate of Completion",
        "date": "2026-10-08",
        "recipients": [
            {
                "name": "Sreeja",
                "email": "invalid-email"
            }
        ]
    }
    errors = validate_job_data(data)
    assert "Recipient 1: invalid email." in errors

def test_valid_date():
    from app.validators import validate_date
    assert validate_date("2026-10-09") is True

def test_invalid_date_format():
    from app.validators import validate_date
    assert validate_date("09-10-2026") is False

def test_impossible_calendar_date():
    from app.validators import validate_date
    assert validate_date("2026-02-30") is False

def test_missing_date():
    from app.validators import validate_date
    assert validate_date("") is False


def test_job_data_with_invalid_date():
    from app.validators import validate_job_data

    data = {
        "event_name": "Python Workshop",
        "certificate_title": "Certificate of Completion",
        "date": "not-a-date",
        "recipients": [
            {
                "name": "Sreeja",
                "email": "sreeja@example.com"
            }
        ]
    }
    errors = validate_job_data(data)
    assert (
        "date must be a valid date in YYYY-MM-DD format."
        in errors
    )


# from app.validators import validate_job_data


def test_blank_recipient_name():
    data = {
        "event_name": "Python Workshop",
        "certificate_title": "Certificate of Completion",
        "date": "2026-10-09",
        "recipients": [
            {
                "name": "   ",
                "email": "sreeja@example.com"
            }
        ]
    }

    errors = validate_job_data(data)

    assert "Recipient 1: name is required." in errors


def test_wrong_event_name_type():
    data = {
        "event_name": 123,
        "certificate_title": "Certificate of Completion",
        "date": "2026-10-09",
        "recipients": [
            {
                "name": "Sreeja",
                "email": "sreeja@example.com"
            }
        ]
    }

    errors = validate_job_data(data)

    assert "event_name is required." in errors


def test_recipient_limit_exceeded():
    recipients = [
        {
            "name": f"User {i}",
            "email": f"user{i}@example.com"
        }
        for i in range(501)
    ]

    data = {
        "event_name": "Python Workshop",
        "certificate_title": "Certificate of Completion",
        "date": "2026-10-09",
        "recipients": recipients
    }

    errors = validate_job_data(data)

    assert (
        "A maximum of 500 recipients is allowed."
        in errors
    )


def test_recipient_must_be_object():
    data = {
        "event_name": "Python Workshop",
        "certificate_title": "Certificate of Completion",
        "date": "2026-10-09",
        "recipients": ["Sreeja"]
    }

    errors = validate_job_data(data)

    assert "Recipient 1 must be an object." in errors
