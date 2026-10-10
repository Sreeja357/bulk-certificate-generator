from app.database import DatabaseConnection
from app.certificate_generator import generate_certificate

def mark_job_failed(job_id, error_message):
    db = None
    cursor = None

    try:
        db = DatabaseConnection()
        cursor = db.cursor()

        query = """
        UPDATE jobs
        SET status = %s
        WHERE jobid = %s
        """

        cursor.execute(query, ("failed", job_id))
        db.commit()

        print(f"Job {job_id} marked as failed: {error_message}")

    except Exception as update_error:
        print(
            f"Could not mark job {job_id} as failed: "
            f"{update_error}"
        )

        if db:
            db.connection.rollback()

    finally:
        if cursor:
            cursor.close()

        if db:
            db.close()


def process_job(job_id):

    db = None
    cursor = None

    try:

        db = DatabaseConnection() 
        # Use dictionary cursor so database rows can be accessed using column names.
        cursor = db.cursor(dictionary=True)

        # -----------------------------------------
        # 1. Get job details
        # -----------------------------------------

        job_query = """
        SELECT
            jobid,
            event_name,
            certificate_title,
            certificate_date
        FROM jobs
        WHERE jobid = %s
        """

        # Get job details
        cursor.execute(job_query, (job_id,))
        job = cursor.fetchone()

        if not job:
            print(f"Job {job_id} not found.")
            return

        # Claim the job only if it is still pending
        claim_query = """
        UPDATE jobs
        SET status = %s
        WHERE jobid = %s
          AND status = %s
        """

        cursor.execute(
            claim_query,
            ("processing", job_id, "pending")
        )

        # Another worker may already have claimed this job
        if cursor.rowcount != 1:
            db.rollback()
            print(f"Job {job_id} is already being processed or finished.")
            return

        db.commit()

        # -----------------------------------------
        # 2. Change job status to processing
        # -----------------------------------------

        update_job_query = """
        UPDATE jobs
        SET status = %s
        WHERE jobid = %s
        """

        cursor.execute(
            update_job_query,
            ("processing", job_id)
        )

        db.commit()

        # -----------------------------------------
        # 3. Get all certificates for this job
        # -----------------------------------------

        certificates_query = """
        SELECT
            certificateid,
            recipient_name,
            recipient_email
        FROM certificates
        WHERE jobid = %s
        ORDER BY certificateid
        """

        cursor.execute(
            certificates_query,
            (job_id,)
        )

        certificates = cursor.fetchall()

        # -----------------------------------------
        # 4. Process each certificate
        # -----------------------------------------

        for certificate in certificates:

            certificate_id = certificate["certificateid"]

            try:

                print(
                    f"Generating certificate {certificate_id}..."
                )

                # Generate PDF
                file_path = generate_certificate(
                    recipient_name=certificate["recipient_name"],
                    event_name=job["event_name"],
                    certificate_title=job["certificate_title"],
                    certificate_date=str(
                        job["certificate_date"]
                    ),
                    certificate_id=certificate_id
                )

                # -----------------------------------------
                # Certificate generated successfully
                # -----------------------------------------

                update_certificate_query = """
                UPDATE certificates
                SET
                    status = %s,
                    file_path = %s,
                    error_message = NULL
                WHERE certificateid = %s
                """

                cursor.execute(
                    update_certificate_query,
                    (
                        "success",
                        file_path,
                        certificate_id
                    )
                )

                # Update successful + completed count
                progress_query = """
                UPDATE jobs
                SET
                    completed_count = completed_count + 1,
                    successful_count = successful_count + 1
                WHERE jobid = %s
                """

                cursor.execute(
                    progress_query,
                    (job_id,)
                )

                db.commit()

                print(
                    f"Certificate {certificate_id} "
                    f"generated successfully."
                )

            # -----------------------------------------
            # Certificate generation failed
            # -----------------------------------------

            except Exception as certificate_error:

                print(
                    f"Certificate {certificate_id} failed: "
                    f"{certificate_error}"
                )

                failure_query = """
                UPDATE certificates
                SET
                    status = %s,
                    error_message = %s
                WHERE certificateid = %s
                """

                cursor.execute(
                    failure_query,
                    (
                        "failed",
                        str(certificate_error),
                        certificate_id
                    )
                )

                # Update failed + completed count
                progress_query = """
                UPDATE jobs
                SET
                    completed_count = completed_count + 1,
                    failed_count = failed_count + 1
                WHERE jobid = %s
                """

                cursor.execute(
                    progress_query,
                    (job_id,)
                )

                db.commit()

                # Continue with next certificate
                continue

        # -----------------------------------------
        # 5. Determine final job status
        # -----------------------------------------

        count_query = """
        SELECT
            total_recipients,
            successful_count,
            failed_count
        FROM jobs
        WHERE jobid = %s
        """

        cursor.execute(
            count_query,
            (job_id,)
        )

        counts = cursor.fetchone()

        total = counts["total_recipients"]
        successful = counts["successful_count"]
        failed = counts["failed_count"]

        # -----------------------------------------
        # 6. Decide final status
        # -----------------------------------------

        if failed == 0:

            final_status = "completed"

        elif successful == 0:

            final_status = "failed"

        else:

            final_status = "completed_with_errors"

        # -----------------------------------------
        # 7. Update final job status
        # -----------------------------------------

        final_job_query = """
        UPDATE jobs
        SET status = %s
        WHERE jobid = %s
        """

        cursor.execute(
            final_job_query,
            (
                final_status,
                job_id
            )
        )

        db.commit()

        print(
            f"Job {job_id} completed."
        )

        print(
            f"Total: {total}, "
            f"Successful: {successful}, "
            f"Failed: {failed}"
        )

    except Exception as e:
        print(f"Error processing job {job_id}: {e}")

        if db:
            try:
                db.connection.rollback()
            except Exception as rollback_error:
                print(f"Rollback failed: {rollback_error}")

        mark_job_failed(job_id, str(e))

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()