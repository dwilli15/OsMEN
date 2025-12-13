#!/usr/bin/env python3
"""Generate encryption key for OAuth tokens."""
from cryptography.fernet import Fernet

if __name__ == "__main__":
    key = Fernet.generate_key().decode()
    print("Generated Encryption Key:")
    print(key)
    print("\nAdd this to your .env file as:")
    print(f"OAUTH_ENCRYPTION_KEY={key}")
