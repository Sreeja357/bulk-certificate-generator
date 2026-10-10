import re
from datetime import date

def validate_email(email):
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email) is not None

def validate_date(value):
    if not isinstance(value, str):
        return False
    try:
        parsed_date = date.fromisoformat(value)
        return parsed_date.isoformat() == value
    except ValueError:
        return False


def validate_job_data(data):
    errors = []

    if not isinstance(data, dict):
        return ["Request body must be a JSON object."]

    # Validate event name
    event_name = data.get("event_name")

    if not isinstance(event_name, str) or not event_name.strip():
        errors.append("event_name is required.")
    elif len(event_name.strip()) > 200:
        errors.append("event_name must not exceed 200 characters.")

    # Validate certificate title
    certificate_title = data.get("certificate_title")

    if (
        not isinstance(certificate_title, str)
        or not certificate_title.strip()
    ):
        errors.append("certificate_title is required.")
    elif len(certificate_title.strip()) > 200:
        errors.append(
            "certificate_title must not exceed 200 characters."
        )

    # Validate date
    certificate_date = data.get("date")

    if not certificate_date:
        errors.append("date is required.")
    elif not validate_date(certificate_date):
        errors.append(
            "date must be a valid date in YYYY-MM-DD format."
        )

    # Validate recipients
    recipients = data.get("recipients")

    if not isinstance(recipients, list) or not recipients:
        errors.append("At least one recipient is required.")
        return errors

    # Prevent excessively large requests
    max_recipients = 500

    if len(recipients) > max_recipients:
        errors.append(
            f"A maximum of {max_recipients} recipients is allowed."
        )
        return errors

    for index, recipient in enumerate(recipients):

        if not isinstance(recipient, dict):
            errors.append(
                f"Recipient {index + 1} must be an object."
            )
            continue

        # Validate recipient name
        name = recipient.get("name")

        if not isinstance(name, str) or not name.strip():
            errors.append(
                f"Recipient {index + 1}: name is required."
            )
        elif len(name.strip()) > 200:
            errors.append(
                f"Recipient {index + 1}: name must not exceed "
                "200 characters."
            )

        # Validate recipient email
        email = recipient.get("email")

        if not isinstance(email, str) or not email.strip():
            errors.append(
                f"Recipient {index + 1}: email is required."
            )
        elif len(email) > 255 or not validate_email(email.strip()):
            errors.append(
                f"Recipient {index + 1}: invalid email."
            )

    return errors