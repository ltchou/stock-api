#!/usr/bin/env python3
"""
版本遞增快速命令

簡化腳本，直接呼叫 scripts/bump_version.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    """主函式"""
    script_path = Path(__file__).parent / "scripts" / "bump_version.py"

    # 將所有參數轉發給 bump_version.py
    cmd = [sys.executable, str(script_path)] + sys.argv[1:]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
