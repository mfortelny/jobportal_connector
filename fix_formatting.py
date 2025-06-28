#!/usr/bin/env python3
"""
Simple script to fix all formatting issues in the project.
Run: python fix_formatting.py
"""

import os
import subprocess
import sys


def run_command(cmd, description):
    """Run a command and return True if successful"""
    print(f"🔄 {description}...")
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {cmd}")
        print(f"   Error: {e.stderr}")
        return False


def main():
    """Main formatting workflow"""
    print("🚀 Starting code formatting...")

    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Commands to run
    commands = [
        ("python3 -m pip install black isort flake8", "Installing formatting tools"),
        ("python3 -m black .", "Running Black formatter"),
        ("python3 -m isort .", "Running isort import sorter"),
        ("python3 -m black --check .", "Verifying Black formatting"),
        ("python3 -m isort --check-only .", "Verifying isort formatting"),
        (
            "python3 -m flake8 . --max-line-length=88 --extend-ignore=E203,W503,E501",
            "Running flake8 code quality check",
        ),
    ]

    # Run all commands
    success_count = 0
    for cmd, description in commands:
        if run_command(cmd, description):
            success_count += 1
        else:
            print("\n⚠️  Some issues found. You may need to fix them manually.")

    print(f"\n📊 Results: {success_count}/{len(commands)} steps completed successfully")

    if success_count == len(commands):
        print("🎉 All formatting checks passed!")
        return 0
    else:
        print("💡 Some formatting issues remain. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
