#!/usr/bin/env python3
"""Local wrapper that forwards to verify_stack_trace.py in the same Code folder.

Place this wrapper next to `verify_stack_trace.py` and run it instead of calling the script directly.
It forwards all arguments to the real script using the same Python interpreter.
"""
import os
import subprocess
import sys


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    real_script = os.path.join(script_dir, "verify_stack_trace.py")
    if not os.path.exists(real_script):
        print(f"ERROR: could not find target script: {real_script}")
        sys.exit(2)
    cmd = [sys.executable, real_script] + sys.argv[1:]
    rc = subprocess.call(cmd)
    sys.exit(rc)


if __name__ == '__main__':
    main()
