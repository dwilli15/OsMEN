#!/usr/bin/env python3
"""
OsMEN Interactive Setup Wizard
Guides users through first-time configuration
"""

import os
import secrets
import subprocess
import sys
from pathlib import Path
from typing import Optional


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class SetupWizard:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.env_file = self.project_root / ".env"
        self.env_example = self.project_root / ".env.example"
        
    def print_header(self, text: str):
        """Print a styled header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")
    
    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.GREEN}✅ {text}{Colors.END}")
    
    def print_warning(self, text: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")
    
    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.RED}❌ {text}{Colors.END}")
    
    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")
    
    def ask_yes_no(self, question: str, default: bool = True) -> bool:
        """Ask a yes/no question"""
        default_str = "Y/n" if default else "y/N"
        response = input(f"{Colors.CYAN}{question} [{default_str}]: {Colors.END}").strip().lower()
        
        if not response:
            return default
        return response in ['y', 'yes']
    
    def ask_input(self, question: str, default: str = "") -> str:
        """Ask for user input"""
        if default:
            response = input(f"{Colors.CYAN}{question} [{default}]: {Colors.END}").strip()
            return response if response else default
        return input(f"{Colors.CYAN}{question}: {Colors.END}").strip()
    
    def generate_secret_key(self) -> str:
        """Generate a secure secret key"""
        return secrets.token_hex(32)
    
    def check_prerequisites(self) -> bool:
        """Check if prerequisites are installed"""
        self.print_header("Checking Prerequisites")
        
        all_good = True
        
        # Check Docker
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.print_success(f"Docker: {result.stdout.strip()}")
            else:
                self.print_error("Docker not found")
                all_good = False
        except Exception as e:
            self.print_error(f"Docker not found: {e}")
            all_good = False
        
        # Check Docker Compose
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.print_success(f"Docker Compose: {result.stdout.strip()}")
            else:
                self.print_error("Docker Compose not found")
                all_good = False
        except Exception as e:
            self.print_error(f"Docker Compose not found: {e}")
            all_good = False
        
        # Check Python version
        version = sys.version_info
        if version >= (3, 12):
            self.print_success(f"Python: {version.major}.{version.minor}.{version.micro}")
        else:
            self.print_warning(f"Python {version.major}.{version.minor}.{version.micro} - Recommend 3.12+")
        
        return all_good
    
    def setup_environment(self):
        """Set up .env file"""
        self.print_header("Environment Configuration")
        
        if self.env_file.exists():
            if not self.ask_yes_no("Existing .env found. Overwrite?", default=False):
                self.print_info("Keeping existing .env file")
                return
        
        # Copy from example
        with open(self.env_example) as f:
            env_content = f.read()
        
        # Configure security settings
        print("\n" + Colors.BOLD + "Security Configuration" + Colors.END)
        
        n8n_password = self.ask_input("n8n password (for http://localhost:5678)", "changeme")
        web_secret = self.ask_input(
            "Web secret key (press Enter to auto-generate)", 
            ""
        )
        if not web_secret:
            web_secret = self.generate_secret_key()
            self.print_info(f"Generated secret key: {web_secret[:16]}...")
        
        session_secret = self.ask_input(
            "Session secret key (press Enter to auto-generate)",
            ""
        )
        if not session_secret:
            session_secret = self.generate_secret_key()
            self.print_info(f"Generated session key: {session_secret[:16]}...")
        
        # Configure LLM provider
        print("\n" + Colors.BOLD + "LLM Provider Configuration" + Colors.END)
        print("You need at least ONE LLM provider:")
        print("  1. OpenAI (recommended - easiest)")
        print("  2. LM Studio (local - privacy-focused)")
        print("  3. Ollama (local - will download models)")
        print("  4. Other (GitHub Copilot, Amazon Q, Claude)")
        
        llm_choice = self.ask_input("Choose provider [1-4]", "1")
        
        openai_key = ""
        if llm_choice == "1":
            openai_key = self.ask_input("OpenAI API key (from platform.openai.com)")
            if not openai_key or openai_key.startswith("your_"):
                self.print_warning("No API key provided - you'll need to add it later")
        elif llm_choice == "2":
            self.print_info("Using LM Studio - make sure it's running on port 1234")
        elif llm_choice == "3":
            self.print_info("Using Ollama - will start with --profile ollama")
        else:
            self.print_info("Configure other providers manually in .env file")
        
        # Update environment content
        replacements = {
            "changeme": n8n_password,
            "dev-secret-key-change-in-production": web_secret,
            "dev-session-secret-change-me": session_secret,
        }
        
        if openai_key:
            replacements["your_openai_api_key_here"] = openai_key
        
        for old, new in replacements.items():
            env_content = env_content.replace(old, new)
        
        # Write .env file
        with open(self.env_file, 'w') as f:
            f.write(env_content)
        
        self.print_success(f"Created {self.env_file}")
    
    def install_dependencies(self):
        """Install Python dependencies"""
        self.print_header("Installing Dependencies")
        
        requirements_file = self.project_root / "requirements.txt"
        
        if not requirements_file.exists():
            self.print_error("requirements.txt not found")
            return False
        
        if self.ask_yes_no("Install Python dependencies?", default=True):
            print("Installing packages (this may take a minute)...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user", "-q", "-r", str(requirements_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.print_success("Dependencies installed successfully")
                return True
            else:
                self.print_error(f"Installation failed: {result.stderr}")
                return False
        return True
    
    def start_services(self):
        """Start Docker services"""
        self.print_header("Starting Services")
        
        if not self.ask_yes_no("Start Docker services?", default=True):
            self.print_info("Skipping service start")
            return
        
        # Determine if using Ollama
        use_ollama = False
        with open(self.env_file) as f:
            content = f.read()
            # Check if OpenAI key is configured
            has_openai = "OPENAI_API_KEY=sk-" in content
            if not has_openai:
                use_ollama = self.ask_yes_no("Use Ollama for local LLM?", default=False)
        
        print("Starting services (this may take 2-3 minutes on first run)...")
        
        cmd = ["docker-compose", "up", "-d"]
        if use_ollama:
            cmd = ["docker-compose", "--profile", "ollama", "up", "-d"]
        
        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            self.print_success("Services started successfully")
            print("\nWaiting for services to initialize (30 seconds)...")
            import time
            time.sleep(30)
        else:
            self.print_error(f"Failed to start services: {result.stderr}")
    
    def verify_installation(self):
        """Verify the installation"""
        self.print_header("Verifying Installation")
        
        check_script = self.project_root / "check_operational.py"
        
        if not check_script.exists():
            self.print_warning("Verification script not found")
            return
        
        print("Running comprehensive verification...")
        result = subprocess.run(
            [sys.executable, str(check_script)],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        if "All tests passed" in result.stdout:
            self.print_success("All checks passed!")
        else:
            self.print_warning("Some checks failed - review output above")
        
        print(result.stdout)
    
    def show_next_steps(self):
        """Show next steps to the user"""
        self.print_header("Setup Complete!")
        
        print(f"{Colors.GREEN}✅ OsMEN is ready to use!{Colors.END}\n")
        
        print(f"{Colors.BOLD}Access your system:{Colors.END}")
        print(f"  • Langflow:  http://localhost:7860")
        print(f"  • n8n:       http://localhost:5678 (admin/[your-password])")
        print(f"  • Qdrant:    http://localhost:6333/dashboard\n")
        
        print(f"{Colors.BOLD}Test your first agent:{Colors.END}")
        print(f"  python3 agents/daily_brief/daily_brief_agent.py\n")
        
        print(f"{Colors.BOLD}Next steps:{Colors.END}")
        print(f"  1. Read {Colors.CYAN}1stsetup.md{Colors.END} for detailed guide")
        print(f"  2. Import workflows from {Colors.CYAN}n8n/workflows/{Colors.END}")
        print(f"  3. Customize agent configs in {Colors.CYAN}config/{Colors.END}")
        print(f"  4. Check out {Colors.CYAN}docs/{Colors.END} for full documentation\n")
        
        print(f"{Colors.BOLD}Get help:{Colors.END}")
        print(f"  • Troubleshooting: docs/TROUBLESHOOTING.md")
        print(f"  • Issues: https://github.com/dwilli15/OsMEN/issues")
        print(f"  • Discussions: https://github.com/dwilli15/OsMEN/discussions\n")
    
    def run(self):
        """Run the setup wizard"""
        print(f"""
{Colors.BOLD}{Colors.CYAN}
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║                   OsMEN Setup Wizard                              ║
║                                                                   ║
║     Get your first agent team running in 10 minutes!             ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
{Colors.END}
""")
        
        # Check prerequisites
        if not self.check_prerequisites():
            self.print_error("Please install missing prerequisites and try again")
            sys.exit(1)
        
        # Setup environment
        self.setup_environment()
        
        # Install dependencies
        if not self.install_dependencies():
            self.print_warning("Continue anyway? Some features may not work.")
            if not self.ask_yes_no("Continue?", default=True):
                sys.exit(1)
        
        # Start services
        self.start_services()
        
        # Verify installation
        self.verify_installation()
        
        # Show next steps
        self.show_next_steps()


def main():
    try:
        wizard = SetupWizard()
        wizard.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup cancelled by user{Colors.END}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
