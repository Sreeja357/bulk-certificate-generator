# Bulk Certificate Generator

A Flask-based backend API that accepts a single request containing
multiple recipients, generates a PDF certificate for each recipient from
one predefined template, tracks job progress, and provides endpoints to
retrieve job results and generated certificates.

This project was developed for the **Bulk Certificate Generator**
backend assignment.

## 1. Objectives

The application is designed to:

-   Accept certificate-generation requests for multiple recipients in
    one API call.
-   Validate event, certificate, date, and recipient information before
    creating a job.
-   Generate an individual PDF certificate for each recipient.
-   Track job status and per-certificate success or failure.
-   Continue processing other recipients when an individual certificate
    fails.
-   Allow clients to check job status, view recipient-level results, and
    retrieve generated PDFs.

The application uses one predefined navy-blue and gold certificate
template. A template editor and multiple template designs are outside
the scope of this assignment.

## 2. Technology Stack

-   **Language:** Python
-   **Web framework:** Flask
-   **Database:** MySQL
-   **Database access:** `mysql-connector-python` with SQL queries
-   **PDF generation:** ReportLab
-   **Testing:** pytest and pytest-mock
-   **API testing:** Postman
-   **PDF verification:** Google Chrome or any PDF viewer

## 3. Project Structure

``` text
bulk-certificate-generator/
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── tables.py
│   ├── routes.py
│   ├── validators.py
│   ├── services.py
│   └── certificate_generator.py
├── certificates/
│   └── generated/
├── tests/
│   ├── conftest.py
│   ├── test_validators.py
│   ├── test_certificate_generator.py
│   ├── test_routes.py
│   └── test_services.py
├── config.py
├── run.py
├── requirements.txt
├── README.md
└── .gitignore
```

Generated certificate PDFs are saved in `certificates/generated/`. The
database stores job information and individual certificate-generation
results.

## 4. Prerequisites

Install the following before running the project:

-   Python 3.10 or a compatible Python version supported by the
    installed dependencies
-   MySQL Server
-   pip
-   Postman (recommended for testing POST requests)

Check your Python and pip installations:

``` bash
python --version
python -m pip --version
```

## 5. Setup and Installation

### Step 1: Open the project folder

Open a terminal in the root directory, `bulk-certificate-generator/`.

### Step 2: Create and activate a virtual environment

On Windows PowerShell:

``` powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell prevents activation, use Command Prompt instead:

``` bat
venv\Scripts\activate.bat
```

### Step 3: Install dependencies

``` bash
python -m pip install -r requirements.txt
```

### Step 4: Configure MySQL

Start MySQL Server and create the project database:

``` sql
CREATE DATABASE bulk_certificate_db;
```

Configure the database connection in `config.py` or through the
environment variables supported by the project:

-   `DB_HOST` --- MySQL host (default: `localhost`)
-   `DB_USER` --- MySQL username (default: `root`)
-   `DB_PASSWORD` --- MySQL password (configure this for your
    environment)
-   `DB_NAME` --- database name (default: `bulk_certificate_db`)

For example, in PowerShell for the current terminal session:

``` powershell
$env:DB_HOST = "localhost"
$env:DB_USER = "root"
$env:DB_PASSWORD = "your_actual_password"
$env:DB_NAME = "bulk_certificate_db"
```

Replace `your_actual_password` with your local MySQL password. Do not
commit real database passwords or other secrets to version control.

### Step 5: Create the database tables

Use the SQL statements or table-creation procedure defined in
`app/tables.py` and the project database setup. Ensure the required
`jobs` and `certificates` tables exist before submitting requests. If
your project creates tables through a setup function, run that setup as
intended by your implementation.

### Step 6: Start the Flask application

``` bash
python run.py
```

The development server is expected to be available at:

``` text
http://127.0.0.1:5000/
```

Opening the root URL in a browser should return the application's health
message, for example:

``` json
{
  "message": "Bulk Certificate Generator API is running"
}
```

Keep the terminal running while testing the API.

## 6. API Endpoints

All endpoints use the local base URL:

``` text
http://127.0.0.1:5000
```

### 6.1 Health check

**Request**

``` http
GET /
```

Checks whether the Flask application is running.

### 6.2 Create a bulk certificate job

**Request**

``` http
POST /api/jobs
Content-Type: application/json
```

Submit all recipients in one request rather than sending one
job-creation request per certificate.

**Example request body**

``` json
{
  "event_name": "Python Workshop",
  "certificate_title": "Certificate of Completion",
  "date": "2026-10-10",
  "recipients": [
    {
      "name": "Hanuman",
      "email": "hanuman@example.com"
    },
    {
      "name": "Shree Ram",
      "email": "ram@example.com"
    },
    {
      "name": "Shree Krishna",
      "email": "krishna@example.com"
    }
  ]
}
```

The date must use the `YYYY-MM-DD` format. The API validates the request
before creating a job. A successful request returns a job identifier and
a success response; use the actual `job_id` returned by your running
application in subsequent requests.

**Expected validation behavior:** Invalid request data should be
rejected with HTTP `400 Bad Request` and validation details.

### 6.3 Check job status and progress

**Request**

``` http
GET /api/jobs/<job_id>
```

Returns the status and progress information for the specified job.
Replace `<job_id>` with the ID returned by the job-creation endpoint.

Job status values used by the application include:

-   `pending` --- waiting to be processed
-   `processing` --- generation is in progress
-   `completed` --- all certificates were generated successfully
-   `completed_with_errors` --- the job finished but one or more
    certificates failed
-   `failed` --- the overall job failed

The exact JSON response fields are defined by `app/routes.py`.

### 6.4 Retrieve individual results for a job

**Request**

``` http
GET /api/jobs/<job_id>/results
```

Returns the individual certificate-generation results associated with
the job, including each recipient's generation status and relevant
result information.

### 6.5 Retrieve a generated certificate

**Request**

``` http
GET /api/certificates/<certificate_id>
```

Returns the generated PDF for the specified certificate ID when the
certificate is available. Use a valid `certificate_id` from the job
results.

The PDF endpoint can be opened in Google Chrome. Chrome's address bar
sends a GET request, so use Postman for the job-creation POST request.

## 7. Testing with Postman

1.  Start the Flask application with `python run.py`.
2.  Create a `POST` request to `http://127.0.0.1:5000/api/jobs`.
3.  Select **Body → raw → JSON** and submit the example request.
4.  Copy the `job_id` from the response.
5.  Check progress using `GET /api/jobs/<job_id>`.
6.  Inspect individual results using `GET /api/jobs/<job_id>/results`.
7.  Copy a successful `certificate_id` and retrieve its PDF using
    `GET /api/certificates/<certificate_id>`.
8.  Test invalid input, such as an invalid email, a missing recipient
    name, or an empty recipient list. These requests should be rejected
    by validation.

A request to `POST /api/jobs` entered directly into a browser address
bar will not work as intended because the browser sends GET by default.
Use Postman or another HTTP client to send POST requests.

## 8. Running Automated Tests

From the project root, activate the virtual environment and run:

``` bash
pytest -v
```

To run a specific test module:

``` bash
pytest -v tests/test_validators.py
pytest -v tests/test_certificate_generator.py
pytest -v tests/test_routes.py
pytest -v tests/test_services.py
```

The test suite has previously reported **25 passing tests** in the
development environment. Run the tests again after making changes and
include the current result when submitting.

The assignment's important test areas are:

-   Job creation
-   Input validation
-   Certificate PDF generation
-   Job status and progress
-   Handling an individual certificate-generation failure
-   Retrieving generated certificates

## 9. Implementation and Design Decisions

### Bulk request

The client submits the event details and recipient list in a single
request. The application creates a job and individual certificate
records for the recipients.

### Background processing

Certificate generation is started in a background thread so the
job-creation request does not need to wait for every PDF to be
generated. The client can check progress through the job-status
endpoint.

This is a lightweight approach suitable for this assignment. A
production deployment with multiple workers or high-volume workloads
would normally use a durable task queue and worker system.

### Validation

The application validates required event and certificate fields, date
format, recipient names, and email addresses before starting a job. The
implementation also limits the number of recipients per request.

### Failure isolation

Individual certificate generation is handled separately so a failure for
one recipient can be recorded without unnecessarily stopping processing
for other recipients. Job and per-certificate statuses allow the client
to identify successful and failed results.

### Certificate generation

ReportLab generates a PDF from a single predefined navy-blue and gold
template. Recipient-specific information is inserted into each generated
certificate, and the PDF is saved in `certificates/generated/`.

### Database

MySQL stores job-level information and individual certificate records.
Database access is implemented using `mysql-connector-python` and SQL
queries.

### Certificate retrieval

The API retrieves a certificate using its ID and serves the generated
PDF when the file is available. The route checks the file path to
prevent serving files outside the generated-certificate directory.

## 10. Limitations and Future Improvements

Potential improvements for a production-ready system include:

-   Replace in-process background threads with a durable task queue.
-   Add authentication and authorization to the API.
-   Add configurable rate limits and request-size limits.
-   Store generated files in object storage for larger deployments.
-   Add structured logging and operational monitoring.
-   Add integration tests against a dedicated test database.

These are future enhancements and are not required to demonstrate the
core assignment functionality.

## 11\. Submission Checklist

Before submitting, verify that:

- [ ] The project installs from `requirements.txt`.
- [ ] MySQL configuration is documented and no real credentials are committed.
- [ ] The required database tables can be created from the submitted setup instructions.
- [ ] The Flask application starts successfully.
- [ ] Bulk job creation and input validation work.
- [ ] Job status and individual results can be retrieved.
- [ ] Generated PDF certificates can be retrieved.
- [ ] Individual certificate failures are tested and do not stop other recipients unnecessarily.
- [ ] `pytest -v` passes in the submission environment.
- [ ] The README matches the final code and its actual API response fields.

------------------------------------------------------------------------

**Assignment:** Bulk Certificate Generator\
**Framework:** Flask\
**Database:** MySQL\
**PDF library:** ReportLab\
**Testing:** pytest
