import json
import os
import re

class PolicyEngine:
    """
    Evaluates normalized OCSF logs against company-specific custom JSON rules
    spanning perimeter firewalls, identity authentication, cloud flows, and WAF telemetry.
    """
    def __init__(self, config_path: str = "config/rules.json"):
        self.rules = []
        if not os.path.exists(config_path):
            fallback_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'rules.json')
            if os.path.exists(fallback_path):
                config_path = fallback_path
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = json.load(f)
                self.rules = data.get("custom_rules", [])

    @staticmethod
    def is_rfc1918(ip: str) -> bool:
        if not ip or ip == "0.0.0.0":
            return False
        if ip.startswith("10.") or ip.startswith("192.168."):
            return True
        if ip.startswith("172."):
            parts = ip.split(".")
            if len(parts) >= 2 and parts[1].isdigit():
                second_octet = int(parts[1])
                return 16 <= second_octet <= 31
        return False

    def evaluate(self, ocsf_log: dict) -> dict:
        dst_port = ocsf_log.get("dst_endpoint", {}).get("port", 0)
        src_ip = ocsf_log.get("src_endpoint", {}).get("ip", "")
        dst_ip = ocsf_log.get("dst_endpoint", {}).get("ip", "")
        action = ocsf_log.get("disposition", "UNKNOWN")
        raw_payload = ocsf_log.get("unmapped", {}).get("raw_payload", "")
        http_url = ocsf_log.get("http_request", {}).get("url", "")
        event_id = ocsf_log.get("event_id", 0)
        
        security_flags = []
        
        for rule in self.rules:
            matched = False
            rule_id = rule.get("id")

            # Check port matching (both single port and list of ports)
            ports = rule.get("dst_ports", [])
            if "dst_port" in rule and rule["dst_port"] not in ports:
                ports.append(rule["dst_port"])
            port_match = (dst_port in ports) if ports else True

            # Check action matching
            action_match = (rule.get("action") == action) if "action" in rule else True

            # Rule 001: Direct External Management Exposure
            if rule_id == "RULE-001":
                if port_match and action_match:
                    matched = True

            # Rule 002: Direct Database Access
            elif rule_id == "RULE-002":
                if port_match and action_match:
                    matched = True

            # Rule 003: Insecure Cleartext Protocol Egress (FTP/Telnet)
            elif rule_id == "RULE-003":
                if port_match and action_match:
                    matched = True

            # Rule 004: Lateral Movement via SMB/RPC
            elif rule_id == "RULE-004":
                if port_match and action_match:
                    matched = True

            # Rule 005: SSH Brute Force Threshold Exceeded
            elif rule_id == "RULE-005":
                if "Failed password" in raw_payload or (dst_port == 22 and action == "DENY"):
                    matched = True

            # Rule 006: Unauthorized Sudo Execution Attempt
            elif rule_id == "RULE-006":
                if "authentication failure" in raw_payload or "sudo:auth" in raw_payload:
                    matched = True

            # Rule 007: Windows Event Log / AD Tampering
            elif rule_id == "RULE-007":
                event_ids = rule.get("event_ids", [4625, 4720, 4672])
                if any(f"[{eid}]" in raw_payload or f"EventID {eid}" in raw_payload or f"Event ID: {eid}" in raw_payload or f" {eid} " in raw_payload for eid in event_ids):
                    matched = True
                elif event_id in event_ids:
                    matched = True

            # Rule 008: Cloud SG Egress Any-Any
            elif rule_id == "RULE-008":
                if (dst_ip == "0.0.0.0" or "0.0.0.0" in raw_payload) and action == "ALLOW":
                    matched = True

            # Rule 009: WAF Path Traversal / Injection
            elif rule_id == "RULE-009":
                regex = rule.get("regex_pattern", r"(\.\./|etc/passwd|<script|UNION\s+SELECT)")
                target_text = http_url if http_url else raw_payload
                if re.search(regex, target_text, re.IGNORECASE):
                    matched = True

            # Generic fallback check
            elif "dst_port" in rule and "action" in rule:
                if rule["dst_port"] == dst_port and rule["action"] == action:
                    matched = True

            if matched:
                evidence = {
                    "dst_endpoint": ocsf_log.get("dst_endpoint"),
                    "disposition": action,
                    "target_vendor": rule.get("target_vendor", ocsf_log.get("metadata", {}).get("original_vendor", "UNKNOWN")),
                    "rule_id": rule_id
                }
                if http_url:
                    evidence["http_url"] = http_url
                if event_id:
                    evidence["event_id"] = event_id

                security_flags.append({
                    "rule_id": rule_id,
                    "severity": rule.get("severity", "HIGH"),
                    "alert_message": rule.get("message", "Security Policy Violation"),
                    "target_vendor": rule.get("target_vendor", "Generic"),
                    "evidence_snippet": evidence
                })
                
        ocsf_log["security_highlights"] = security_flags
        ocsf_log["has_mistake_flag"] = len(security_flags) > 0
        return ocsf_log
