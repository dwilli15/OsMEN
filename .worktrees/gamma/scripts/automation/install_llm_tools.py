#!/usr/bin/env python3
"""
Automated LLM Tool Installation Assistant
Checks for and installs: LM Studio, Ollama, llama.cpp
"""

import os
import subprocess
import platform
from pathlib import Path

def prompt_install(tool_name, description):
    """Prompt user for installation permission"""
    print(f"\n{tool_name} is not installed.")
    print(f"Description: {description}")
    response = input(f"Would you like to install {tool_name}? [y/N]: ").strip().lower()
    return response in ['y', 'yes']

def install_lm_studio():
    """Guide LM Studio installation"""
    system = platform.system()
    
    print("\n" + "="*60)
    print("LM Studio Installation Guide")
    print("="*60)
    print("\nLM Studio must be installed manually:")
    print("1. Visit: https://lmstudio.ai/")
    print("2. Download the appropriate version for your OS")
    
    if system == "Darwin":  # macOS
        print("3. Open the DMG and drag LM Studio to Applications")
    elif system == "Windows":
        print("3. Run the installer and follow the prompts")
    elif system == "Linux":
        print("3. Extract the AppImage and make it executable")
    
    print("\nAfter installation:")
    print("1. Open LM Studio")
    print("2. Download a model (recommended: Mistral 7B or Llama 2)")
    print("3. Start the local server (enable in settings)")
    print("4. Note the server URL (usually http://localhost:1234)")
    
    input("\nPress Enter after installing LM Studio...")
    
    # Verify installation
    lm_studio_dirs = [
        "/Applications/LM Studio.app",
        os.path.expanduser("~/.lmstudio"),
        "C:\\Program Files\\LM Studio"
    ]
    
    for dir_path in lm_studio_dirs:
        if os.path.exists(dir_path):
            print("✅ LM Studio installation detected!")
            return True
    
    print("⚠️  Could not verify LM Studio installation")
    return False

def install_ollama():
    """Install Ollama"""
    system = platform.system()
    
    print("\n" + "="*60)
    print("Ollama Installation")
    print("="*60)
    
    try:
        if system == "Darwin":  # macOS
            print("Installing Ollama via Homebrew...")
            subprocess.run(["brew", "install", "ollama"], check=True)
        elif system == "Linux":
            print("Installing Ollama via curl script...")
            subprocess.run(
                "curl -fsSL https://ollama.com/install.sh | sh",
                shell=True,
                check=True
            )
        elif system == "Windows":
            print("Downloading Ollama for Windows...")
            print("Visit: https://ollama.com/download/windows")
            print("Run the installer after download completes")
            input("Press Enter after installing Ollama...")
        
        # Verify installation
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Ollama installed: {result.stdout.strip()}")
            return True
        else:
            print("⚠️  Could not verify Ollama installation")
            return False
            
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def install_llamacpp():
    """Install llama.cpp"""
    print("\n" + "="*60)
    print("llama.cpp Installation")
    print("="*60)
    
    home = Path.home()
    llamacpp_dir = home / "llama.cpp"
    
    if llamacpp_dir.exists():
        print("⚠️  llama.cpp directory already exists")
        return True
    
    try:
        print("Cloning llama.cpp repository...")
        subprocess.run(
            ["git", "clone", "https://github.com/ggerganov/llama.cpp.git", str(llamacpp_dir)],
            check=True
        )
        
        print("Building llama.cpp...")
        subprocess.run(
            ["make"],
            cwd=str(llamacpp_dir),
            check=True
        )
        
        print("✅ llama.cpp installed successfully!")
        print(f"Location: {llamacpp_dir}")
        print(f"\nTo use: {llamacpp_dir}/main -m /path/to/model.gguf")
        return True
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return False

def main():
    """Main installation flow"""
    print("="*60)
    print("OsMEN Phase 2: LLM Tool Installation Assistant")
    print("="*60)
    
    # Check and install LM Studio
    if not os.path.exists("/Applications/LM Studio.app") and \
       not os.path.exists(os.path.expanduser("~/.lmstudio")) and \
       not os.path.exists("C:\\Program Files\\LM Studio"):
        if prompt_install(
            "LM Studio",
            "User-friendly local LLM runtime with model management"
        ):
            install_lm_studio()
    else:
        print("\n✅ LM Studio already installed")
    
    # Check and install Ollama
    if subprocess.run(["which", "ollama"], capture_output=True).returncode != 0:
        if prompt_install(
            "Ollama",
            "Simple local LLM runtime with CLI interface"
        ):
            install_ollama()
    else:
        print("\n✅ Ollama already installed")
    
    # Check and install llama.cpp
    if not os.path.exists(os.path.expanduser("~/llama.cpp")):
        if prompt_install(
            "llama.cpp",
            "High-performance LLM inference engine"
        ):
            install_llamacpp()
    else:
        print("\n✅ llama.cpp already installed")
    
    print("\n" + "="*60)
    print("Installation assistant complete!")
    print("="*60)

if __name__ == '__main__':
    main()
