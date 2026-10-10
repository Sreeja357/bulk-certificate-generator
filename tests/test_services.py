
from unittest.mock import MagicMock, call

from app.services import process_job


def test_one_certificate_failure_does_not_stop_others(mocker):
    # Mock the database
    mock_db = MagicMock()
    mock_cursor = MagicMock()

    mock_db.cursor.return_value = mock_cursor
    # Simulate successfully claiming the pending job
    mock_cursor.rowcount = 1
    # First fetchone() returns the job.
    # Second fetchone() returns final counts.
    mock_cursor.fetchone.side_effect = [
        {
            "jobid": 101,
            "event_name": "Python Workshop",
            "certificate_title": "Certificate of Completion",
            "certificate_date": "2026-10-09",
        },
        {
            "total_recipients": 3,
            "successful_count": 2,
            "failed_count": 1,
        },
    ]

    # Simulate three recipients
    mock_cursor.fetchall.return_value = [
        {
            "certificateid": 201,
            "recipient_name": "Sreeja",
            "recipient_email": "sreeja@example.com",
        },
        {
            "certificateid": 202,
            "recipient_name": "Fail User",
            "recipient_email": "fail@example.com",
        },
        {
            "certificateid": 203,
            "recipient_name": "Chinna",
            "recipient_email": "chinna@example.com",
        },
    ]

    mocker.patch(
        "app.services.DatabaseConnection",
        return_value=mock_db
    )

    # The second certificate fails, but the third succeeds.
    mock_generate = mocker.patch(
        "app.services.generate_certificate",
        side_effect=[
            "certificates/generated/certificate_201.pdf",
            Exception("Simulated PDF generation failure"),
            "certificates/generated/certificate_203.pdf",
        ],
    )

    process_job(101)

    # All three certificates must be attempted.
    assert mock_generate.call_count == 3

    attempted_names = [
        item.kwargs["recipient_name"]
        for item in mock_generate.call_args_list
    ]

    assert attempted_names == [
        "Sreeja",
        "Fail User",
        "Chinna",
    ]

    # The job should finish with partial success.
    final_job_update = mock_cursor.execute.call_args_list[-1]

    assert "UPDATE jobs" in final_job_update.args[0]
    assert "status = %s" in final_job_update.args[0]
    assert final_job_update.args[1] == ("completed_with_errors", 101)

    mock_db.close.assert_called_once()