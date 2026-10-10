from app.database import DatabaseConnection

def create_tables():
    db = None
    cursor = None

    try:
        db = DatabaseConnection()
        cursor = db.cursor()

        # Jobs table
        jobs_table = """
        CREATE TABLE IF NOT EXISTS jobs (
            jobid BIGINT AUTO_INCREMENT PRIMARY KEY,
            event_name VARCHAR(200) NOT NULL,
            certificate_title VARCHAR(200) NOT NULL,
            certificate_date DATE NOT NULL,
            status VARCHAR(30) DEFAULT 'pending',
            total_recipients INT DEFAULT 0,
            completed_count INT DEFAULT 0,
            successful_count INT DEFAULT 0,
            failed_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP
        ); """

        # Certificates table
        certificates_table = """
        CREATE TABLE IF NOT EXISTS certificates (
            certificateid BIGINT AUTO_INCREMENT PRIMARY KEY,
            jobid BIGINT NOT NULL,
            recipient_name VARCHAR(200) NOT NULL,
            recipient_email VARCHAR(255) NOT NULL,
            status VARCHAR(30) DEFAULT 'pending',
            file_path VARCHAR(500),
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (jobid)
                REFERENCES jobs(jobid)
                ON DELETE CASCADE
        ); """

        cursor.execute(jobs_table)
        cursor.execute(certificates_table)
        db.commit()

        print("Tables created successfully.")

    except Exception as e:
        if db:
            try:
                db.connection.rollback()
            except Exception as rollback_error:
                print(f"Rollback error: {rollback_error}")
        print(f"Error creating tables: {e}")
        raise

    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

if __name__ == "__main__":
    create_tables()