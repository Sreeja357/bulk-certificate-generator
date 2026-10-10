from flask import Blueprint, request, jsonify, send_file
import threading
from app.database import DatabaseConnection
from app.validators import validate_job_data
from app.services import process_job
import os

api = Blueprint("api", __name__)


@api.route("/api/jobs", methods=["POST"])
def create_job():
    # Get JSON data from Postman
    data = request.get_json(silent=True)

    # Validate request
    errors = validate_job_data(data)

    if errors:
        return jsonify({
            "success": False,
            "errors": errors
        }), 400

    db = None
    cursor = None

    try:
        # Connect to database
        db = DatabaseConnection()
        cursor = db.cursor()

        # Read request data
        event_name = data["event_name"].strip()
        certificate_title = data["certificate_title"].strip()
        certificate_date = data["date"]
        recipients = data["recipients"]

        total_recipients = len(recipients)

        # 1. Insert the job
        job_query = """
        INSERT INTO jobs (
            event_name,
            certificate_title,
            certificate_date,
            status,
            total_recipients
        )
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            job_query,
            (
                event_name,
                certificate_title,
                certificate_date,
                "pending",
                total_recipients
            )
        )

        job_id = cursor.lastrowid

        # 2. Define the certificate insertion query
        certificate_query = """
        INSERT INTO certificates (
            jobid,
            recipient_name,
            recipient_email,
            status
        )
        VALUES (%s, %s, %s, %s)
        """

        # 3. Insert each recipient exactly once
        for recipient in recipients:
            cursor.execute(
                certificate_query,
                (
                    job_id,
                    recipient["name"].strip(),
                    recipient["email"].strip(),
                    "pending"
                )
            )

        # 4. Save the job and all recipients together
        db.commit()

        # 5. Start background processing
        thread = threading.Thread(
            target=process_job,
            args=(job_id,)
        )
        thread.start()

        # 6. Return response
        return jsonify({
            "success": True,
            "message": "Certificate generation job created.",
            "job_id": job_id,
            "total_recipients": total_recipients,
            "status": "pending"
        }), 201

    except Exception as e:
        if db:
            try:
                db.connection.rollback()
            except Exception as rollback_error:
                print(
                    f"Database rollback failed: {rollback_error}"
                )

        print(f"Error creating certificate job: {e}")

        return jsonify({
            "success": False,
            "message": "Unable to create certificate job."
        }), 500

    finally:
        if cursor:
            cursor.close()

        if db:
            db.close()


# Get job status
@api.route("/api/jobs/<int:job_id>", methods=["GET"])
def get_job_status(job_id):

    db = None
    cursor = None

    try:
        # Connect to database
        db = DatabaseConnection()

        # Dictionary cursor
        cursor = db.cursor(dictionary=True)

        # Get job information
        job_query = """
        SELECT
            jobid,
            event_name,
            certificate_title,
            certificate_date,
            status,
            total_recipients,
            completed_count,
            successful_count,
            failed_count,
            created_at,
            updated_at
        FROM jobs
        WHERE jobid = %s"""
        cursor.execute(
            job_query,
            (job_id,)
        )
        job = cursor.fetchone()

        # Job doesn't exist
        if not job:
            return jsonify({
                "success": False,
                "message": "Job not found."
            }), 404

        # Return job information
        return jsonify({
            "success": True,
            "job_id": job["jobid"],
            "event_name": job["event_name"],
            "certificate_title": job["certificate_title"],
            "date": str(job["certificate_date"]),
            "status": job["status"],
            "total_recipients": job["total_recipients"],
            "completed": job["completed_count"],
            "successful": job["successful_count"],
            "failed": job["failed_count"]
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

# Get job results
@api.route("/api/jobs/<int:job_id>/results", methods=["GET"])
def get_job_results(job_id):

    db = None
    cursor = None

    try:

        # Connect to database
        db = DatabaseConnection()

        # Dictionary cursor
        cursor = db.cursor(dictionary=True)

        # First check whether the job exists
        job_query = """
        SELECT jobid
        FROM jobs
        WHERE jobid = %s
        """

        cursor.execute(
            job_query,
            (job_id,)
        )

        job = cursor.fetchone()

        # Job doesn't exist
        if not job:

            return jsonify({
                "success": False,
                "message": "Job not found."
            }), 404

        # Get certificate results
        results_query = """
        SELECT
            certificateid,
            recipient_name,
            recipient_email,
            status,
            file_path,
            error_message
        FROM certificates
        WHERE jobid = %s
        ORDER BY certificateid
        """

        cursor.execute(
            results_query,
            (job_id,)
        )

        results = cursor.fetchall()

        # Convert database rows into API response
        certificate_results = []

        for result in results:

            certificate_results.append({
                "certificate_id": result["certificateid"],
                "recipient_name": result["recipient_name"],
                "recipient_email": result["recipient_email"],
                "status": result["status"],
                "file_path": result["file_path"],
                "error_message": result["error_message"]
            })

        return jsonify({
            "success": True,
            "job_id": job_id,
            "results": certificate_results
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()

# Get a specific certificate by ID
@api.route("/api/certificates/<int:certificate_id>",methods=["GET"])
def get_certificate(certificate_id):

    db = None
    cursor = None

    try:

        # Connect to database
        db = DatabaseConnection()

        # Dictionary cursor
        cursor = db.cursor(dictionary=True)

        # Find certificate
        certificate_query = """
        SELECT
            certificateid,
            recipient_name,
            recipient_email,
            status,
            file_path,
            error_message
        FROM certificates
        WHERE certificateid = %s
        """

        cursor.execute(
            certificate_query,
            (certificate_id,)
        )

        certificate = cursor.fetchone()

        # Certificate doesn't exist
        if not certificate:

            return jsonify({
                "success": False,
                "message": "Certificate not found."
            }), 404

        # Certificate generation failed
        if certificate["status"] != "success":

            return jsonify({
                "success": False,
                "message": "Certificate is not available.",
                "status": certificate["status"],
                "error_message": certificate["error_message"]
            }), 404

        # Get the stored file path
        file_path = certificate["file_path"]

        if not file_path:
            return jsonify({
                "success": False,
                "message": "Certificate file is not available."
            }), 404

        # Resolve the project root directory
        project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        # Resolve the permitted certificate directory
        certificate_directory = os.path.realpath(
            os.path.join(
                project_root,
                "certificates",
                "generated"
            )
        )

        # Resolve the requested file path
        resolved_file_path = os.path.realpath(file_path)

        # Ensure the file is inside the permitted directory
        if not os.path.isfile(resolved_file_path):
            return jsonify({
                "success": False,
                "message": "Certificate file not found."
            }), 404

        if os.path.commonpath([
            certificate_directory,
            resolved_file_path
        ]) != certificate_directory:
            return jsonify({
                "success": False,
                "message": "Invalid certificate file path."
            }), 403

        # Return the PDF
        return send_file(
            resolved_file_path,
            mimetype="application/pdf",
            as_attachment=False
        )

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()