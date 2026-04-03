import mysql.connector
from mysql.connector import Error

class DatabaseManager:
    """
    Database manager for HemoScan.
    Applies the Single Responsibility Principle (SRP). This module
    handles solely data persistence, isolated from UI or camera logic.
    """
    
    def __init__(self, host="localhost", user="root", password="", database="hemoscan_db"):
        # Initialize credentials. In production, these should load from environment variables (.env)
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def save_history(self, scan_date, patient_name, red_percentage, diagnosis, digital_signature, yellow_percentage, liver_diagnosis):
        """Opens connection, saves the dual biometric record, and safely closes the connection."""
        try:
            # 1. Establish isolated connection
            connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            cursor = connection.cursor()
            
            # 2. Prepare clean SQL command (Prevents SQL injection)
            # Note: Database schema names kept in original language for backward compatibility
            sql_command = (
                "INSERT INTO historial_clinico "
                "(fecha_escaneo, nombre, porcentaje_rojo, diagnostico, firma_digital, porcentaje_amarillo, diagnostico_higado) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
            )
            
            # 3. Assign values received from the sensor
            values = (scan_date, patient_name, red_percentage, diagnosis, digital_signature, yellow_percentage, liver_diagnosis)
            
            # 4. Execute and commit
            cursor.execute(sql_command, values)
            connection.commit()
            print("INFO [DB_MANAGER]: Biometric record successfully secured in MySQL.")
            
        except Error as e:
            # Fault tolerance: Log the error without crashing the visual pipeline
            print(f"CRITICAL ERROR [DB_MANAGER]: MySQL persistence failure -> {e}")
        finally:
            # Cleanup watchdog: Ensures the port is closed even if a failure occurs
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()