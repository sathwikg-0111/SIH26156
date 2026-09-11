import hashlib
import re

class DataProtector:
    """
    Provides cryptographic integrity hashing for raw logs (zero data loss proof)
    and optional IP masking for sensitive internal subnets.
    """
    @staticmethod
    def generate_sha256(raw_log: str) -> str:
        return hashlib.sha256(raw_log.encode('utf-8')).hexdigest()

    @staticmethod
    def mask_sensitive_ip(ip_str: str) -> str:
        # Mask last two octets for privacy (e.g., 10.0.1.50 -> 10.0.x.x)
        octets = ip_str.split('.')
        if len(octets) == 4 and octets[0] in ['10', '172', '192']:
            return f"{octets[0]}.{octets[1]}.x.x"
        return ip_str
