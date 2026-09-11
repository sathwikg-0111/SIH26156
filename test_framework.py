import json
import unittest
from app.parsers import MultiVendorParser
from app.anonymizer import DataProtector
from app.normalizer import OCSFNormalizer
from app.rules_engine import PolicyEngine
from simulator.log_generator import SAMPLE_LOGS

class TestLogProcessingFramework(unittest.TestCase):
    def setUp(self):
        self.policy_engine = PolicyEngine()

    def test_multi_vendor_parser(self):
        # Test Cisco ASA Log
        cisco_log = SAMPLE_LOGS[0]
        cisco_res = MultiVendorParser.parse(cisco_log)
        self.assertEqual(cisco_res["vendor"], "CISCO_ASA")
        self.assertEqual(cisco_res["src_ip"], "198.51.100.44")
        self.assertEqual(cisco_res["dst_ip"], "10.0.1.50")
        self.assertEqual(cisco_res["src_port"], 51234)
        self.assertEqual(cisco_res["dst_port"], 443)
        self.assertEqual(cisco_res["protocol"], "TCP")
        self.assertEqual(cisco_res["action"], "ALLOW")

        # Test Palo Alto Log
        palo_log = SAMPLE_LOGS[1]
        palo_res = MultiVendorParser.parse(palo_log)
        self.assertEqual(palo_res["vendor"], "PALO_ALTO")
        self.assertEqual(palo_res["src_ip"], "203.0.113.15")
        self.assertEqual(palo_res["dst_ip"], "10.0.1.20")
        self.assertEqual(palo_res["protocol"], "UDP")
        self.assertEqual(palo_res["action"], "DENY")

    def test_anonymizer(self):
        sample_log = SAMPLE_LOGS[0]
        hash_val = DataProtector.generate_sha256(sample_log)
        self.assertEqual(len(hash_val), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in hash_val))
        
        # Test masking
        masked = DataProtector.mask_sensitive_ip("10.0.1.50")
        self.assertEqual(masked, "10.0.x.x")
        unmasked = DataProtector.mask_sensitive_ip("8.8.8.8")
        self.assertEqual(unmasked, "8.8.8.8")

    def test_ocsf_normalization_and_json_format(self):
        for raw_log in SAMPLE_LOGS:
            parsed = MultiVendorParser.parse(raw_log)
            ocsf_event = OCSFNormalizer.normalize(parsed, raw_log)
            
            # Check OCSF schema fields
            self.assertEqual(ocsf_event["metadata"]["version"], "1.1.0")
            self.assertEqual(ocsf_event["metadata"]["product"]["name"], "Universal Log Pre-processor")
            self.assertEqual(ocsf_event["class_uid"], 4001)
            self.assertEqual(ocsf_event["category_uid"], 4)
            self.assertIn("log_hash", ocsf_event["metadata"])
            self.assertIn("src_endpoint", ocsf_event)
            self.assertIn("dst_endpoint", ocsf_event)
            self.assertIn("connection_info", ocsf_event)
            self.assertIn("disposition", ocsf_event)
            self.assertEqual(ocsf_event["unmapped"]["raw_payload"], raw_log)
            
            # Evaluate rules
            processed = self.policy_engine.evaluate(ocsf_event)
            self.assertIn("security_highlights", processed)
            self.assertIn("has_mistake_flag", processed)
            
            # Verify JSON serializability
            json_str = json.dumps(processed, indent=2)
            self.assertIsInstance(json_str, str)
            reloaded = json.loads(json_str)
            self.assertEqual(reloaded["class_uid"], 4001)

    def test_rules_engine_detections(self):
        # Test RULE-001: SSH port 22 ALLOW
        ssh_log = SAMPLE_LOGS[2]
        parsed = MultiVendorParser.parse(ssh_log)
        ocsf_event = OCSFNormalizer.normalize(parsed, ssh_log)
        evaluated = self.policy_engine.evaluate(ocsf_event)
        self.assertTrue(evaluated["has_mistake_flag"])
        rule_ids = [flag["rule_id"] for flag in evaluated["security_highlights"]]
        self.assertIn("RULE-001", rule_ids)
        self.assertEqual(evaluated["security_highlights"][0]["severity"], "CRITICAL")

        # Test RULE-002: MySQL port 3306 ALLOW
        mysql_log = SAMPLE_LOGS[3]
        parsed = MultiVendorParser.parse(mysql_log)
        ocsf_event = OCSFNormalizer.normalize(parsed, mysql_log)
        evaluated = self.policy_engine.evaluate(ocsf_event)
        self.assertTrue(evaluated["has_mistake_flag"])
        rule_ids = [flag["rule_id"] for flag in evaluated["security_highlights"]]
        self.assertIn("RULE-002", rule_ids)
        self.assertEqual(evaluated["security_highlights"][0]["severity"], "HIGH")

if __name__ == "__main__":
    unittest.main()
