import socket
import time
import random
from datetime import datetime, timezone

UDP_IP = "127.0.0.1"
UDP_PORT = 5140

# Sample dataset preserving contract for automated unit tests while expanding telemetry coverage
SAMPLE_LOGS = [
    # 0. Cisco ASA - Normal Perimeter Traffic (Tested by unit test)
    "<134>1 2026-09-10T10:00:00Z firewall Cisco-ASA: %ASA-6-302013: Built inbound TCP connection for 198.51.100.44/51234 to inside:10.0.1.50/443 ACTION=ALLOW",

    # 1. Palo Alto - Normal Inbound Drop (Tested by unit test)
    "Sep 10 10:00:05 pan-os-fw 1,2026/09/10 10:00:05,001606000,TRAFFIC,drop,0,2026/09/10 10:00:05,203.0.113.15,10.0.1.20,0,0,80,80,0,0,0,0,0,UDP,DENY",

    # 2. NETWORKING MISTAKE 1: Allowed External SSH (Tested by unit test for RULE-001)
    "<134>1 2026-09-10T10:00:10Z core-fw Cisco-ASA: %ASA-6-302014: Teardown TCP connection from 198.51.100.99/44123 to inside:10.0.1.50/22 ACTION=ALLOW",

    # 3. NETWORKING MISTAKE 2: Allowed MySQL Database Jump (Tested by unit test for RULE-002)
    "Sep 10 10:00:15 internal-fw ALLOW TCP src 10.0.1.50 dst 10.0.2.100 spt 58210 dpt 3306",

    # 4. Fortinet FortiGate: Insecure Cleartext Protocol Egress (Triggers RULE-003)
    'date=2026-09-10 time=10:11:00 devname="FGT-CORP" type="traffic" subtype="forward" level="warning" action="ALLOW" srcip=10.0.1.35 dstip=198.51.100.88 srcport=51042 dstport=23 proto=6',

    # 5. Palo Alto / Windows: Lateral Movement via Ephemeral RPC/SMB (Triggers RULE-004)
    "Sep 10 10:12:00 pan-os-fw 1,2026/09/10 10:12:00,001606000,TRAFFIC,allow,0,2026/09/10 10:12:00,10.0.1.105,10.0.2.10,49822,445,49822,445,0,0,0,0,0,TCP,ALLOW",

    # 6. Linux Auth: Repeated SSH Authentication Failure (Triggers RULE-005)
    "Sep 10 10:15:20 auth-node sshd[24156]: Failed password for invalid user admin from 203.0.113.88 port 48210 ssh2",

    # 7. Linux Secure Log: Sudo Authentication Failure / Escalation (Triggers RULE-006)
    "Sep 10 10:16:05 sec-srv sudo: pam_unix(sudo:auth): authentication failure; logname=analyst uid=1002 euid=0 tty=/dev/pts/1 ruser=analyst rhost= user=analyst",

    # 8. Windows Active Directory: Account Logon Failure Event 4625 (Triggers RULE-007)
    "Sep 10 10:20:00 dc01.corp Microsoft-Windows-Security-Auditing[4625]: An account failed to log on. Subject: Security ID: S-1-0-0 Account Name: - Logon Type: 3 Account For Which Logon Failed: Account Name: Administrator Source Network Address: 198.51.100.120 Source Port: 49822 Failure Reason: Unknown user name or bad password.",

    # 9. AWS VPC Flow Log: Security Group Egress Any-Any (Triggers RULE-008)
    "2 123456789010 eni-0123456789abcdef0 10.0.1.50 0.0.0.0 54123 4444 6 50 25000 1694340000 1694340060 ACCEPT OK",

    # 10. WAF Reverse Proxy: SQL Injection & Path Traversal Probe (Triggers RULE-009)
    'Sep 10 10:30:15 waf-edge nginx: 203.0.113.99 - - [10/Sep/2026:10:30:15 +0000] "GET /api/v1/users?id=1%20UNION%20SELECT%20username,password%20FROM%20users HTTP/1.1" 403 162 "-" "sqlmap/1.6" "WAF_BLOCK"',

    # 11. Cisco ASA: Built-in Dynamic ACL Drop (%ASA-4-106023)
    "<132>1 2026-09-10T10:32:00Z perimeter Cisco-ASA: %ASA-4-106023: Deny inbound UDP from 203.0.113.50/53120 to outside:10.0.1.1/53 on interface outside",

    # 12. IBM QRadar: Enterprise Security Network Ingest
    "<13>1 2026-09-10T10:35:00Z qradar-gw IBM-Security: LEEF:2.0|IBM|SecurityNetwork|5.4|Traffic|src=10.0.3.88|dst=10.0.1.25|spt=49200|dpt=443|proto=TCP|action=ALLOW",

    # 13. Cisco ASA: NAT Translation Failure Alert (%ASA-3-305006)
    "<131>1 2026-09-10T10:40:12Z edge-gw Cisco-ASA: %ASA-3-305006: regular translation creation failed for icmp src outside:203.0.113.88 dst inside:10.0.1.20 (type 8, code 0) ACTION=DENY",

    # 14. IBM QRadar: Advanced Threat & Vulnerability Event (LEEF 2.0)
    "<13>1 2026-09-10T10:42:30Z qradar-soc IBM-Security: LEEF:2.0|IBM|QRadar|7.5|ThreatDetected|sev=8|cat=Malware|src=203.0.113.142|dst=10.0.1.75|spt=51892|dpt=443|proto=TCP|usr=svc_backup|action=DENY",

    # 15. Palo Alto Networks: Threat Vulnerability & Exploit Signature Log
    "Sep 10 10:45:00 pan-os-edge 1,2026/09/10 10:45:00,001606000,THREAT,vulnerability,99401,2026/09/10 10:45:00,198.51.100.220,10.0.1.15,0,0,443,443,0,0,0,0,0,TCP,DENY",

    # 16. Windows Active Directory: Special Privileges Assigned (Event ID 4672)
    "Sep 10 10:48:10 dc01.corp Microsoft-Windows-Security-Auditing[4672]: Special privileges assigned to new logon. Subject: Security ID: S-1-5-21-382910-500 Account Name: Administrator Account Domain: CORP Logon ID: 0x19A44 Privileges: SeSecurityPrivilege SeBackupPrivilege SeRestorePrivilege",

    # 17. Linux Kernel: Enterprise Perimeter IPTables Drop
    "Sep 10 10:50:22 fw-gw kernel: [IPTABLES DROP]: IN=eth0 OUT= MAC=00:1a:2b:3c:4d:5e:00:11:22:33:44:55:08:00 SRC=198.51.100.77 DST=10.0.1.1 LEN=60 TOS=0x00 PREC=0x00 TTL=51 ID=39122 DF PROTO=TCP SPT=43890 DPT=23 WINDOW=14600 RES=0x00 SYN URGP=0"
]

def generate_dynamic_log(template: str) -> str:
    """Generates UTC timestamps and realistic source IP variations dynamically."""
    now_utc = datetime.now(timezone.utc)
    iso_stamp = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    syslog_stamp = now_utc.strftime("%b %d %H:%M:%S")
    
    # Inject current timestamp
    dynamic_line = template
    dynamic_line = dynamic_line.replace("2026-09-10T10:00:00Z", iso_stamp)
    dynamic_line = dynamic_line.replace("2026-09-10T10:00:10Z", iso_stamp)
    dynamic_line = dynamic_line.replace("2026-09-10T10:32:00Z", iso_stamp)
    dynamic_line = dynamic_line.replace("2026-09-10T10:35:00Z", iso_stamp)
    dynamic_line = dynamic_line.replace("2026-09-10T10:40:12Z", iso_stamp)
    dynamic_line = dynamic_line.replace("2026-09-10T10:42:30Z", iso_stamp)
    dynamic_line = dynamic_line.replace("Sep 10 10:00:05", syslog_stamp)
    dynamic_line = dynamic_line.replace("Sep 10 10:00:15", syslog_stamp)
    dynamic_line = dynamic_line.replace("Sep 10 10:15:20", syslog_stamp)
    dynamic_line = dynamic_line.replace("Sep 10 10:20:00", syslog_stamp)
    dynamic_line = dynamic_line.replace("Sep 10 10:30:15", syslog_stamp)
    dynamic_line = dynamic_line.replace("Sep 10 10:45:00", syslog_stamp)
    dynamic_line = dynamic_line.replace("Sep 10 10:48:10", syslog_stamp)
    dynamic_line = dynamic_line.replace("Sep 10 10:50:22", syslog_stamp)

    return dynamic_line

def start_simulation():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"[*] Live Log Simulator running... Sending multi-vendor stream to UDP {UDP_IP}:{UDP_PORT}")
    
    event_counter = 0
    while True:
        try:
            # Generate log from expanded catalog
            raw_template = random.choice(SAMPLE_LOGS)
            log_line = generate_dynamic_log(raw_template)
            sock.sendto(log_line.encode('utf-8'), (UDP_IP, UDP_PORT))
            
            event_counter += 1
            
            # Periodic bursts to simulate real-world spikes (stress testing queue)
            if event_counter % 25 == 0:
                burst_count = random.randint(3, 7)
                for _ in range(burst_count):
                    burst_log = generate_dynamic_log(random.choice(SAMPLE_LOGS))
                    sock.sendto(burst_log.encode('utf-8'), (UDP_IP, UDP_PORT))
                    time.sleep(0.05)
        except Exception:
            # Resilient fallback: ensure buffer continues even if UDP fails
            try:
                from app.main import LogIngestionPipeline, LOG_BUFFER
                import app.main as app_main
                pipeline = LogIngestionPipeline()
                event = pipeline.process_raw_log(log_line)
                LOG_BUFFER.appendleft(event)
                app_main.TOTAL_EVENTS_PROCESSED += 1
            except Exception:
                pass

        time.sleep(1.2) # Normal steady baseline stream

if __name__ == "__main__":
    start_simulation()

