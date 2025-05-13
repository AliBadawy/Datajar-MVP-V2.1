#!/usr/bin/env python3
"""
Test runner for Datajar backend API tests.
This script provides a convenient way to run the API tests with various options.
"""

import os
import sys
import argparse
import subprocess
from dotenv import load_dotenv

# Configure the argument parser
parser = argparse.ArgumentParser(description="Run Datajar Backend API tests")
parser.add_argument("--module", "-m", help="Specific test module to run (auth, projects, messages, salla)")
parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
parser.add_argument("--html", action="store_true", help="Generate HTML report")
parser.add_argument("--env", "-e", default=".env.test", help="Environment file to use")

args = parser.parse_args()

# Load environment variables
env_file = os.path.join(os.path.dirname(__file__), args.env)
if not os.path.exists(env_file):
    print(f"Error: Environment file {env_file} not found.")
    sys.exit(1)

load_dotenv(env_file)

# Build the pytest command
cmd = ["pytest"]

# Add verbosity flag if requested
if args.verbose:
    cmd.append("-v")

# Add coverage if requested
if args.coverage:
    cmd.append("--cov=../Backend")  # Point to Backend directory for coverage
    cmd.append("--cov-report=term")
    if args.html:
        cmd.append("--cov-report=html")

# Add specific module if requested
if args.module:
    module_map = {
        "auth": "tests/api/test_auth.py",
        "projects": "tests/api/test_projects.py",
        "messages": "tests/api/test_messages.py",
        "salla": "tests/api/test_salla_integration.py"
    }
    
    if args.module in module_map:
        cmd.append(module_map[args.module])
    else:
        print(f"Error: Unknown module '{args.module}'. Available modules: {', '.join(module_map.keys())}")
        sys.exit(1)
else:
    # Run all tests if no module specified
    cmd.append("tests/api/")

# Print the command being run
print(f"Running: {' '.join(cmd)}")

# Run the tests
result = subprocess.run(cmd)

# Exit with the same code as pytest
sys.exit(result.returncode)
