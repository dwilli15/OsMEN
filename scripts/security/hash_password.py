#!/usr/bin/env python3
"""Generate bcrypt password hashes for WEB_ADMIN_PASSWORD_HASH."""

import argparse
import getpass
import sys

import bcrypt


def parse_args():
    parser = argparse.ArgumentParser(description="Generate a bcrypt hash for OsMEN dashboard credentials.")
    parser.add_argument("password", nargs="?", help="Plaintext password (omit to be prompted securely).")
    parser.add_argument("--rounds", type=int, default=12, help="bcrypt cost factor (default: 12)")
    return parser.parse_args()


def main():
    args = parse_args()
    plaintext = args.password or getpass.getpass("Password: ")
    if not plaintext:
        print("Password cannot be empty", file=sys.stderr)
        return 1
    salt = bcrypt.gensalt(rounds=args.rounds)
    hashed = bcrypt.hashpw(plaintext.encode(), salt)
    print(hashed.decode())
    return 0


if __name__ == "__main__":
    sys.exit(main())
