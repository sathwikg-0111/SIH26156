from datetime import datetime, timezone
from app.anonymizer import DataProtector

class OCSFNormalizer:
    """
    Normalizes parsed vendor data into the Open Cybersecurity Schema Framework (OCSF v1.1.0) format.
    Ensures rich telemetry mapping across firewalls, identity providers, cloud flows, and WAF events.
    """
    @staticmethod
    def normalize(parsed_data: dict, raw_log: str) -> dict:
        log_hash = DataProtector.generate_sha256(raw_log)
        iso_timestamp = datetime.now(timezone.utc).isoformat()
        
        vendor = parsed_data.get("vendor", "LINUX")
        
        class_uid = 4001  # Network Activity Class UID in OCSF
        category_uid = 4   # Network Activity Category

        ocsf_event = {
            "metadata": {
                "version": "1.1.0",
                "product": {
                    "name": "Universal Log Pre-processor",
                    "vendor_name": "NTRO"
                },
                "log_hash": log_hash,
                "original_vendor": vendor
            },
            "time": iso_timestamp,
            "class_uid": class_uid,
            "category_uid": category_uid,
            "src_endpoint": {
                "ip": parsed_data.get("src_ip", "0.0.0.0"),
                "port": parsed_data.get("src_port", 0)
            },
            "dst_endpoint": {
                "ip": parsed_data.get("dst_ip", "0.0.0.0"),
                "port": parsed_data.get("dst_port", 0)
            },
            "connection_info": {
                "protocol_name": parsed_data.get("protocol", "TCP")
            },
            "disposition": parsed_data.get("action", "ALLOW"),
            "unmapped": {
                "raw_payload": raw_log
            }
        }

        # Optional Contextual Fields
        if parsed_data.get("http_url"):
            ocsf_event["http_request"] = {
                "url": parsed_data["http_url"]
            }

        if parsed_data.get("actor_user"):
            ocsf_event["actor"] = {
                "user": {
                    "name": parsed_data["actor_user"]
                }
            }

        if parsed_data.get("event_id"):
            ocsf_event["event_id"] = parsed_data["event_id"]

        return ocsf_event
