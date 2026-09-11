import re

class MultiVendorParser:
    """
    Extracts core network tuple attributes (Source IP, Destination IP, Ports, Protocol, Action)
    and optional contextual attributes (URL, Actor, Event ID) from heterogeneous enterprise vendor logs.
    """
    @staticmethod
    def parse(raw_log: str) -> dict:
        raw_upper = raw_log.upper()
        
        # 1. Vendor Detection
        vendor = "LINUX"
        if "CISCO" in raw_upper or "%ASA" in raw_upper:
            vendor = "CISCO_ASA"
        elif "PALOALTO" in raw_upper or "PAN-OS" in raw_upper:
            vendor = "PALO_ALTO"
        elif "FORTINET" in raw_upper or "FORTIGATE" in raw_upper or "FGT-" in raw_upper or 'DEVNAME="FGT' in raw_upper:
            vendor = "FORTINET"
        elif "MICROSOFT-WINDOWS" in raw_upper or "SECURITY-AUDITING" in raw_upper or "EVENT ID: 4" in raw_upper or "EVENTID 4" in raw_upper:
            vendor = "WINDOWS_AD"
        elif "ENI-" in raw_upper or "VPC" in raw_upper or "FLOWLOG" in raw_upper:
            vendor = "AWS_VPC"
        elif "WAF" in raw_upper or "CLOUDFLARE" in raw_upper or "NGINX" in raw_upper or "SQLMAP" in raw_upper:
            vendor = "CLOUDFLARE_WAF"
        elif "IBM" in raw_upper or "QRADAR" in raw_upper or "LEEF" in raw_upper:
            vendor = "IBM"
        elif "LINUX" in raw_upper or "INTERNAL-FW" in raw_upper or "SSHD" in raw_upper or "IPTABLES" in raw_upper or "KERNEL" in raw_upper or "SUDO" in raw_upper:
            vendor = "LINUX"

        # 2. Action / Disposition Detection
        action = "ALLOW"
        if any(keyword in raw_upper for keyword in ["DENY", "DROP", "REJECT", "FAILED", "BLOCK", "WAF_BLOCK", "FAILURE"]):
            action = "DENY"
        elif any(keyword in raw_upper for keyword in ["ALLOW", "PERMIT", "ACCEPTED", "ACCEPT", "SUCCESS", "BUILT", "OK"]):
            action = "ALLOW"

        # 3. Protocol Detection
        protocol = "TCP"
        if "UDP" in raw_upper:
            protocol = "UDP"
        elif "ICMP" in raw_upper:
            protocol = "ICMP"

        # Special Case: AWS VPC Flow Log positional parsing
        # Format: <version> <account-id> <interface-id> <srcaddr> <dstaddr> <srcport> <dstport> <protocol> ... <action> <status>
        vpc_parts = raw_log.strip().split()
        if len(vpc_parts) >= 14 and vpc_parts[0].isdigit() and vpc_parts[2].startswith("eni-"):
            vendor = "AWS_VPC"
            src_ip = vpc_parts[3]
            dst_ip = vpc_parts[4]
            src_port = int(vpc_parts[5]) if vpc_parts[5].isdigit() else 0
            dst_port = int(vpc_parts[6]) if vpc_parts[6].isdigit() else 0
            proto_num = vpc_parts[7]
            protocol = "TCP" if proto_num == "6" else ("UDP" if proto_num == "17" else ("ICMP" if proto_num == "1" else "TCP"))
            action = "ALLOW" if vpc_parts[12].upper() == "ACCEPT" else "DENY"
            return {
                "vendor": vendor,
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": src_port,
                "dst_port": dst_port,
                "protocol": protocol,
                "action": action
            }

        # 4. IP Extraction (Named key=value or regex)
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        src_ip_match = re.search(r'(?:srcip=|src=|SRC=|Source Network Address:\s*)([\d\.]+)', raw_log, re.IGNORECASE)
        dst_ip_match = re.search(r'(?:dstip=|dst=|DST=)([\d\.]+)', raw_log, re.IGNORECASE)
        
        if src_ip_match and dst_ip_match:
            src_ip = src_ip_match.group(1)
            dst_ip = dst_ip_match.group(1)
        else:
            ips = re.findall(ip_pattern, raw_log)
            src_ip = ips[0] if len(ips) > 0 else "0.0.0.0"
            dst_ip = ips[1] if len(ips) > 1 else ("0.0.0.0" if len(ips) <= 1 else ips[0])

        # 5. Port Extraction
        src_port_match = re.search(r'(?:srcport=|spt=|SPT[=\s]|Source Port:\s*)(\d{1,5})', raw_log, re.IGNORECASE)
        dst_port_match = re.search(r'(?:dstport=|dpt=|DPT[=\s]|inside:[\d\.]+/|to inside:[\d\.]+/|dest_port=|port\s+)(\d{1,5})', raw_log, re.IGNORECASE)

        if src_port_match:
            src_port = int(src_port_match.group(1))
        else:
            ports = re.findall(r'(?:port\s|DPT[=\s]|SPT[=\s]|/|PORT=)(\d{1,5})', raw_log, re.IGNORECASE)
            src_port = int(ports[0]) if len(ports) > 0 else 0

        if dst_port_match:
            dst_port = int(dst_port_match.group(1))
        else:
            ports = re.findall(r'(?:port\s|DPT[=\s]|SPT[=\s]|/|PORT=)(\d{1,5})', raw_log, re.IGNORECASE)
            dst_port = int(ports[1]) if len(ports) > 1 else (int(ports[0]) if len(ports) > 0 else 0)

        # 6. Contextual Fields: HTTP URL, Actor, Event ID
        http_match = re.search(r'"(?:GET|POST|PUT|DELETE)\s+([^\s]+)\s+HTTP', raw_log)
        http_url = http_match.group(1) if http_match else ""

        user_match = re.search(r'(?:user[=\s]|Account Name:\s*)([a-zA-Z0-9_\-\.]+)', raw_log)
        actor_user = user_match.group(1) if user_match else ""

        eid_match = re.search(r'(?:Event ID:?\s*|\[)(\d{4})(?:\]|\b)', raw_log)
        event_id = int(eid_match.group(1)) if eid_match else 0

        return {
            "vendor": vendor,
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "src_port": src_port,
            "dst_port": dst_port,
            "protocol": protocol,
            "action": action,
            "http_url": http_url,
            "actor_user": actor_user,
            "event_id": event_id
        }
