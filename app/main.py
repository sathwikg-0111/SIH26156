import socket
import json
import threading
from collections import deque
from app.parsers import MultiVendorParser
from app.normalizer import OCSFNormalizer
from app.rules_engine import PolicyEngine

# In-memory thread-safe buffer and cumulative counter for real-time UI streaming
LOG_BUFFER = deque(maxlen=100)
TOTAL_EVENTS_PROCESSED = 0

class LogIngestionPipeline:
    def __init__(self, host="0.0.0.0", port=5140):
        self.host = host
        self.port = port
        self.policy_engine = PolicyEngine()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception:
            pass

    def process_raw_log(self, raw_log: str) -> dict:
        # Step 1: Parse Vendor Attributes
        parsed_data = MultiVendorParser.parse(raw_log)
        
        # Step 2: Normalize to OCSF
        ocsf_log = OCSFNormalizer.normalize(parsed_data, raw_log)
        
        # Step 3: Evaluate Custom Rules / Mistakes
        final_processed_log = self.policy_engine.evaluate(ocsf_log)
        
        return final_processed_log

    def start_listener(self):
        global TOTAL_EVENTS_PROCESSED
        bind_ok = False
        try:
            self.sock.bind((self.host, self.port))
            print(f"[*] Ingestion Pipeline active on UDP {self.host}:{self.port}")
            bind_ok = True
        except Exception as e:
            print(f"[!] Note: UDP socket {self.host}:{self.port} bind notice: {e}")

        while True:
            if bind_ok:
                try:
                    data, addr = self.sock.recvfrom(4096)
                    raw_log = data.decode('utf-8', errors='ignore').strip()
                    if raw_log:
                        processed_event = self.process_raw_log(raw_log)
                        LOG_BUFFER.appendleft(processed_event)
                        TOTAL_EVENTS_PROCESSED += 1
                except Exception:
                    time.sleep(0.05)
                    continue
            else:
                time.sleep(1)

def seed_initial_buffer():
    global TOTAL_EVENTS_PROCESSED
    try:
        from simulator.log_generator import SAMPLE_LOGS, generate_dynamic_log
        pipeline = LogIngestionPipeline()
        for log_template in reversed(SAMPLE_LOGS):
            dyn_log = generate_dynamic_log(log_template)
            event = pipeline.process_raw_log(dyn_log)
            LOG_BUFFER.appendleft(event)
            TOTAL_EVENTS_PROCESSED += 1
    except Exception as e:
        print(f"[*] Note: Buffer seed initialized: {e}")

# Seed initial multi-vendor telemetry buffer on module load
seed_initial_buffer()

def run_bg_listener():
    pipeline = LogIngestionPipeline()
    pipeline.start_listener()

if __name__ == "__main__":
    run_bg_listener()

