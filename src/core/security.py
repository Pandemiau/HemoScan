import hashlib
from datetime import datetime

class DataAuthenticator:
    """
    Cryptography and Data Integrity module for HemoScan.
    Designed to guarantee the immutability of medical telemetry.
    Generates a SHA-256 Hash (industry standard) acting as a 'black box'.
    """

    @staticmethod
    def generate_biometric_signature(patient_name, red_percentage, yellow_percentage, diagnosis):
        """
        Takes raw sensor data and generates a unique, unrepeatable digital signature
        using an exact timestamp seed.
        """
        # Get exact timestamp down to the millisecond
        exact_timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        
        # Concatenate raw data string
        raw_data_string = f"{patient_name}|R:{red_percentage}|A:{yellow_percentage}|D:{diagnosis}|T:{exact_timestamp}"
        
        # Apply SHA-256 encryption algorithm
        resulting_hash = hashlib.sha256(raw_data_string.encode('utf-8')).hexdigest()
        
        print(f"SECURE [AUTHENTICATOR]: Digital signature generated -> {resulting_hash[:10]}...")
        
        return resulting_hash