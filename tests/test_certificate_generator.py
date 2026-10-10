import os

from app.certificate_generator import generate_certificate


def test_generate_certificate():

    file_path = generate_certificate(
        recipient_name="Test User",
        event_name="Python Workshop",
        certificate_title="Certificate of Completion",
        certificate_date="2026-10-09",
        certificate_id=99999
    )

    # Check that the PDF file exists
    assert os.path.exists(file_path)

    # Check that it is a PDF file
    assert file_path.endswith(".pdf")

    # Check that the PDF is not empty
    assert os.path.getsize(file_path) > 0

    # Remove the test PDF after testing
    os.remove(file_path)