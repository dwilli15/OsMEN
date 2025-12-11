#!/usr/bin/env python3
"""
Simplewall Integration
Provides programmatic access to Simplewall firewall functionality

Simplewall uses Windows Filtering Platform (WFP) and stores rules in XML format.
This integration manipulates the rules file and interacts with the running application.
"""

import ctypes
import hashlib
import json
import os
import platform
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class SimplewallIntegration:
    """Integration with Simplewall firewall

    Simplewall stores its rules in an XML configuration file.
    This integration provides:
    - Direct XML manipulation for rule management
    - Windows Filtering Platform (WFP) interaction via netsh
    - Application blocking/allowing through hosts file modification
    """

    def __init__(self):
        self.simplewall_path = Path(
            os.getenv("SIMPLEWALL_PATH", "C:\\Program Files\\simplewall")
        )
        self.executable = self.simplewall_path / "simplewall.exe"
        self.config_path = (
            Path(os.getenv("APPDATA", "")) / "Henry++" / "simplewall" / "simplewall.xml"
        )
        self.hosts_path = Path("C:/Windows/System32/drivers/etc/hosts")
        self.is_windows = platform.system() == "Windows"
        self._blocked_domains_file = (
            Path(os.getenv("APPDATA", "")) / "OsMEN" / "blocked_domains.json"
        )

    def _is_admin(self) -> bool:
        """Check if running with administrator privileges"""
        if not self.is_windows:
            return os.geteuid() == 0
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

    def _check_simplewall_installed(self) -> bool:
        """Check if Simplewall is installed"""
        return self.executable.exists() if self.is_windows else False

    def _get_app_hash(self, app_path: str) -> str:
        """Generate SHA256 hash of application for rule identification"""
        try:
            with open(app_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except:
            return hashlib.sha256(app_path.encode()).hexdigest()

    def _load_blocked_domains(self) -> Dict:
        """Load OsMEN's blocked domains tracking file"""
        if self._blocked_domains_file.exists():
            try:
                with open(self._blocked_domains_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return {"domains": [], "updated": None}

    def _save_blocked_domains(self, data: Dict):
        """Save OsMEN's blocked domains tracking file"""
        self._blocked_domains_file.parent.mkdir(parents=True, exist_ok=True)
        data["updated"] = datetime.now().isoformat()
        with open(self._blocked_domains_file, "w") as f:
            json.dump(data, f, indent=2)

    def block_application(self, app_path: str) -> Dict:
        """Block an application from network access using Windows Firewall

        Uses netsh advfirewall to create blocking rules since Simplewall
        doesn't have a CLI. Creates both inbound and outbound rules.
        """
        result = {
            "application": app_path,
            "action": "blocked",
            "timestamp": datetime.now().isoformat(),
            "status": "failed",
            "error": None,
            "rule_names": [],
        }

        if not self.is_windows:
            result["error"] = "Firewall rules require Windows"
            return result

        if not os.path.exists(app_path):
            result["error"] = f"Application not found: {app_path}"
            return result

        if not self._is_admin():
            result["error"] = "Administrator privileges required"
            return result

        app_name = Path(app_path).stem
        rule_name_out = f"OsMEN_Block_{app_name}_Out"
        rule_name_in = f"OsMEN_Block_{app_name}_In"

        try:
            # Create outbound blocking rule
            cmd_out = [
                "netsh",
                "advfirewall",
                "firewall",
                "add",
                "rule",
                f"name={rule_name_out}",
                "dir=out",
                "action=block",
                f"program={app_path}",
                "enable=yes",
            ]

            # Create inbound blocking rule
            cmd_in = [
                "netsh",
                "advfirewall",
                "firewall",
                "add",
                "rule",
                f"name={rule_name_in}",
                "dir=in",
                "action=block",
                f"program={app_path}",
                "enable=yes",
            ]

            # Execute commands
            result_out = subprocess.run(cmd_out, capture_output=True, text=True)
            result_in = subprocess.run(cmd_in, capture_output=True, text=True)

            if result_out.returncode == 0 and result_in.returncode == 0:
                result["status"] = "success"
                result["rule_names"] = [rule_name_out, rule_name_in]
            else:
                result["error"] = result_out.stderr or result_in.stderr

        except Exception as e:
            result["error"] = str(e)

        return result

    def allow_application(self, app_path: str) -> Dict:
        """Remove blocking rules for an application"""
        result = {
            "application": app_path,
            "action": "allowed",
            "timestamp": datetime.now().isoformat(),
            "status": "failed",
            "error": None,
            "rules_removed": [],
        }

        if not self.is_windows:
            result["error"] = "Firewall rules require Windows"
            return result

        if not self._is_admin():
            result["error"] = "Administrator privileges required"
            return result

        app_name = Path(app_path).stem
        rule_name_out = f"OsMEN_Block_{app_name}_Out"
        rule_name_in = f"OsMEN_Block_{app_name}_In"

        try:
            # Remove outbound rule
            cmd_out = [
                "netsh",
                "advfirewall",
                "firewall",
                "delete",
                "rule",
                f"name={rule_name_out}",
            ]

            # Remove inbound rule
            cmd_in = [
                "netsh",
                "advfirewall",
                "firewall",
                "delete",
                "rule",
                f"name={rule_name_in}",
            ]

            result_out = subprocess.run(cmd_out, capture_output=True, text=True)
            result_in = subprocess.run(cmd_in, capture_output=True, text=True)

            result["status"] = "success"
            if "Ok" in result_out.stdout or result_out.returncode == 0:
                result["rules_removed"].append(rule_name_out)
            if "Ok" in result_in.stdout or result_in.returncode == 0:
                result["rules_removed"].append(rule_name_in)

        except Exception as e:
            result["error"] = str(e)

        return result

    def block_domain(self, domain: str) -> Dict:
        """Block a domain by adding it to the hosts file

        This is the most reliable cross-application method.
        Redirects the domain to 0.0.0.0 (null route).
        """
        result = {
            "domain": domain,
            "action": "blocked",
            "timestamp": datetime.now().isoformat(),
            "status": "failed",
            "method": "hosts_file",
            "error": None,
        }

        if not self.is_windows:
            result["error"] = (
                "Domain blocking via hosts requires Windows (or run as root on Linux)"
            )
            return result

        if not self._is_admin():
            result["error"] = "Administrator privileges required to modify hosts file"
            return result

        # Clean domain
        domain = domain.lower().strip()
        if domain.startswith("http://") or domain.startswith("https://"):
            domain = domain.split("://", 1)[1]
        domain = domain.split("/")[0]  # Remove path

        try:
            # Read current hosts file
            with open(self.hosts_path, "r", encoding="utf-8") as f:
                hosts_content = f.read()

            # Check if already blocked
            block_entry = f"0.0.0.0 {domain}"
            if block_entry in hosts_content:
                result["status"] = "already_blocked"
                return result

            # Add blocking entry
            with open(self.hosts_path, "a", encoding="utf-8") as f:
                f.write(f"\n# Blocked by OsMEN - {datetime.now().isoformat()}\n")
                f.write(f"{block_entry}\n")
                # Also block www subdomain
                if not domain.startswith("www."):
                    f.write(f"0.0.0.0 www.{domain}\n")

            # Track in our own file
            blocked = self._load_blocked_domains()
            if domain not in blocked["domains"]:
                blocked["domains"].append(domain)
                self._save_blocked_domains(blocked)

            # Flush DNS cache
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True)

            result["status"] = "success"

        except PermissionError:
            result["error"] = "Permission denied - run as Administrator"
        except Exception as e:
            result["error"] = str(e)

        return result

    def unblock_domain(self, domain: str) -> Dict:
        """Remove a domain from the hosts file"""
        result = {
            "domain": domain,
            "action": "unblocked",
            "timestamp": datetime.now().isoformat(),
            "status": "failed",
            "error": None,
        }

        if not self._is_admin():
            result["error"] = "Administrator privileges required"
            return result

        domain = domain.lower().strip()

        try:
            # Read hosts file
            with open(self.hosts_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Filter out blocking entries for this domain
            new_lines = []
            removed = False
            skip_next_comment = False

            for i, line in enumerate(lines):
                # Skip OsMEN comment and following block entries
                if f"0.0.0.0 {domain}" in line or f"0.0.0.0 www.{domain}" in line:
                    removed = True
                    continue
                if "Blocked by OsMEN" in line:
                    # Check if next line is for this domain
                    if i + 1 < len(lines) and domain in lines[i + 1]:
                        continue
                new_lines.append(line)

            # Write back
            with open(self.hosts_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            # Update tracking
            blocked = self._load_blocked_domains()
            if domain in blocked["domains"]:
                blocked["domains"].remove(domain)
                self._save_blocked_domains(blocked)

            # Flush DNS
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True)

            result["status"] = "success" if removed else "not_found"

        except Exception as e:
            result["error"] = str(e)

        return result

    def get_rules(self) -> List[Dict]:
        """Get current OsMEN firewall rules from Windows Firewall"""
        rules = []

        if not self.is_windows:
            return rules

        try:
            # Get OsMEN-created rules
            cmd = [
                "netsh",
                "advfirewall",
                "firewall",
                "show",
                "rule",
                "name=all",
                "verbose",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                current_rule = {}
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if line.startswith("Rule Name:"):
                        if current_rule and "OsMEN" in current_rule.get("name", ""):
                            rules.append(current_rule)
                        current_rule = {"name": line.split(":", 1)[1].strip()}
                    elif ":" in line and current_rule:
                        key, value = line.split(":", 1)
                        current_rule[key.strip().lower().replace(" ", "_")] = (
                            value.strip()
                        )

                if current_rule and "OsMEN" in current_rule.get("name", ""):
                    rules.append(current_rule)

            # Also include blocked domains
            blocked = self._load_blocked_domains()
            for domain in blocked.get("domains", []):
                rules.append(
                    {
                        "name": f"OsMEN_Domain_{domain}",
                        "type": "domain_block",
                        "target": domain,
                        "method": "hosts_file",
                    }
                )

        except Exception as e:
            rules.append({"error": str(e)})

        return rules

    def add_rule(self, rule: Dict) -> Dict:
        """Add a firewall rule based on rule type"""
        result = {
            "rule": rule,
            "timestamp": datetime.now().isoformat(),
            "status": "failed",
            "error": None,
        }

        rule_type = rule.get("type", "application")

        if rule_type == "application":
            return self.block_application(rule.get("path", ""))
        elif rule_type == "domain":
            return self.block_domain(rule.get("target", ""))
        else:
            result["error"] = f"Unknown rule type: {rule_type}"

        return result

    def remove_rule(self, rule_id: str) -> Dict:
        """Remove a firewall rule by name or ID"""
        result = {
            "rule_id": rule_id,
            "timestamp": datetime.now().isoformat(),
            "status": "failed",
            "error": None,
        }

        if not self._is_admin():
            result["error"] = "Administrator privileges required"
            return result

        try:
            # Check if it's a domain rule
            if rule_id.startswith("OsMEN_Domain_"):
                domain = rule_id.replace("OsMEN_Domain_", "")
                return self.unblock_domain(domain)

            # Otherwise try to delete firewall rule
            cmd = [
                "netsh",
                "advfirewall",
                "firewall",
                "delete",
                "rule",
                f"name={rule_id}",
            ]
            proc_result = subprocess.run(cmd, capture_output=True, text=True)

            if proc_result.returncode == 0 or "Ok" in proc_result.stdout:
                result["status"] = "removed"
            else:
                result["error"] = proc_result.stderr or "Rule not found"

        except Exception as e:
            result["error"] = str(e)

        return result

    def get_status(self) -> Dict:
        """Get comprehensive firewall status"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform.system(),
            "is_admin": self._is_admin(),
            "simplewall_installed": self._check_simplewall_installed(),
            "simplewall_path": str(self.simplewall_path),
            "windows_firewall": None,
            "osmen_rules_count": 0,
            "blocked_domains_count": 0,
        }

        if self.is_windows:
            try:
                # Check Windows Firewall status
                cmd = ["netsh", "advfirewall", "show", "allprofiles", "state"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                status["windows_firewall"] = (
                    "enabled" if "ON" in result.stdout else "disabled"
                )
            except:
                pass

            # Count OsMEN rules
            rules = self.get_rules()
            status["osmen_rules_count"] = len(
                [r for r in rules if "OsMEN" in r.get("name", "")]
            )

            # Count blocked domains
            blocked = self._load_blocked_domains()
            status["blocked_domains_count"] = len(blocked.get("domains", []))

        return status


def main():
    """Test the integration"""
    integration = SimplewallIntegration()

    print("=== Simplewall/Firewall Integration Test ===\n")

    # Get status
    print("--- Status ---")
    status = integration.get_status()
    print(json.dumps(status, indent=2))

    # Get rules
    print("\n--- Current OsMEN Rules ---")
    rules = integration.get_rules()
    print(json.dumps(rules, indent=2))


if __name__ == "__main__":
    main()
