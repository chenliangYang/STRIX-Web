"""Fake STRIX script for non-interactive mode testing."""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Fake STRIX CLI")
    parser.add_argument("-n", "--non-interactive", action="store_true", help="Non-interactive mode")
    parser.add_argument("--target", type=str, help="Target URL or IP")
    parser.add_argument("--scan-mode", type=str, default="standard", help="Scan mode: quick, standard, deep")
    parser.add_argument("--run-id", type=str, required=True, help="STRIX run ID")
    parser.add_argument("--output-dir", type=str, required=True, help="Output directory")
    parser.add_argument("--fail", action="store_true", help="Simulate failure")
    args = parser.parse_args()

    if not args.non_interactive:
        print("Fake STRIX interactive mode - use -n for non-interactive")
        sys.exit(0)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # strix_run_dir is directly under output_dir (storage/runs/<task_id>/<run_id>)
    strix_run_dir = output_dir / args.run_id
    strix_run_dir.mkdir(parents=True, exist_ok=True)

    events_file = strix_run_dir / "events.jsonl"
    artifacts_dir = strix_run_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    start_time = datetime.utcnow()

    events = [
        {
            "type": "scan_start",
            "time": start_time.isoformat() + "Z",
            "data": {
                "target": args.target,
                "scan_mode": args.scan_mode,
                "run_id": args.run_id,
            }
        },
        {
            "type": "port_scan",
            "time": (start_time.replace(second=1)).isoformat() + "Z",
            "data": {
                "port": 80,
                "state": "open",
                "service": "http"
            }
        },
        {
            "type": "port_scan",
            "time": (start_time.replace(second=2)).isoformat() + "Z",
            "data": {
                "port": 443,
                "state": "open",
                "service": "https"
            }
        },
        {
            "type": "port_scan",
            "time": (start_time.replace(second=3)).isoformat() + "Z",
            "data": {
                "port": 22,
                "state": "open",
                "service": "ssh"
            }
        },
        {
            "type": "scan_phase",
            "time": (start_time.replace(second=4)).isoformat() + "Z",
            "data": {
                "phase": "vulnerability_detection",
                "message": "Starting vulnerability detection..."
            }
        },
        {
            "type": "vulnerability_found",
            "time": (start_time.replace(second=5)).isoformat() + "Z",
            "data": {
                "vuln_id": "vuln-001",
                "title": "SQL Injection in Login Form",
                "severity": "high",
                "url": f"{args.target}/login",
                "method": "POST",
                "parameter": "username"
            }
        },
        {
            "type": "vulnerability_found",
            "time": (start_time.replace(second=6)).isoformat() + "Z",
            "data": {
                "vuln_id": "vuln-002",
                "title": "Reflected XSS in Search Parameter",
                "severity": "medium",
                "url": f"{args.target}/search",
                "parameter": "q"
            }
        },
        {
            "type": "vulnerability_found",
            "time": (start_time.replace(second=7)).isoformat() + "Z",
            "data": {
                "vuln_id": "vuln-003",
                "title": "Missing X-Frame-Options Header",
                "severity": "low",
                "url": f"{args.target}/",
                "header": "X-Frame-Options"
            }
        },
        {
            "type": "scan_progress",
            "time": (start_time.replace(second=8)).isoformat() + "Z",
            "data": {
                "progress": 75,
                "message": "Scanning complete, generating report..."
            }
        },
        {
            "type": "scan_complete",
            "time": (start_time.replace(second=9)).isoformat() + "Z",
            "data": {
                "summary": {
                    "total_vulnerabilities": 3,
                    "high": 1,
                    "medium": 1,
                    "low": 1,
                    "duration_seconds": 9
                }
            }
        }
    ]

    if args.fail:
        events = [
            {
                "type": "scan_start",
                "time": start_time.isoformat() + "Z",
                "data": {"target": args.target}
            },
            {
                "type": "scan_error",
                "time": (start_time.replace(second=1)).isoformat() + "Z",
                "data": {
                    "error": "Connection timeout",
                    "message": "Failed to connect to target"
                }
            }
        ]

    with open(events_file, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    vuln_md = artifacts_dir / "vuln-001.md"
    vuln_md.write_text(f"""# SQL Injection in Login Form

## Vulnerability Details

**Severity:** High
**URL:** {args.target}/login
**Parameter:** username
**Method:** POST

## Summary

The login form at `{args.target}/login` is vulnerable to SQL injection in the `username` parameter. An attacker can bypass authentication by using SQL injection payloads.

## Proof of Concept

```http
POST /login HTTP/1.1
Host: {args.target.replace("http://", "").replace("https://", "")}
Content-Type: application/x-www-form-urlencoded

username=admin' OR '1'='1&password=anything
```

## Impact

An attacker can:
- Bypass authentication
- Extract sensitive data from the database
- Potentially execute operating system commands (depending on database configuration)

## Remediation

1. Use parameterized queries (prepared statements)
2. Implement input validation
3. Apply principle of least privilege to database accounts
4. Use a Web Application Firewall (WAF)

## References

- OWASP SQL Injection
- CWE-89: SQL Injection
""", encoding="utf-8")

    vuln2_md = artifacts_dir / "vuln-002.md"
    vuln2_md.write_text(f"""# Reflected XSS in Search Parameter

## Vulnerability Details

**Severity:** Medium
**URL:** {args.target}/search
**Parameter:** q
**Type:** Reflected XSS

## Summary

The search functionality reflects user-supplied input without proper sanitization, allowing injection of arbitrary JavaScript code.

## Proof of Concept

```
{args.target}/search?q=<script>alert(document.cookie)</script>
```

## Impact

An attacker can:
- Steal session cookies
- Redirect users to malicious sites
- Modify page content
- Keylog user input

## Remediation

1. Implement output encoding
2. Use Content Security Policy (CSP)
3. Validate and sanitize all user input
4. Use HTTPOnly and Secure flags for cookies
""", encoding="utf-8")

    print(f"[STRIX] Scan completed: {args.target}")
    print(f"[STRIX] Found 3 vulnerabilities (1 high, 1 medium, 1 low)")
    print(f"[STRIX] Results saved to: {strix_run_dir}")

    if args.fail:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
