#!/usr/bin/env python3
"""
版本一致性檢查腳本

檢查專案所有版本定義檔案是否一致
用於 pre-commit hook
"""

import json
import re
import sys
from pathlib import Path


def get_root_dir() -> Path:
    """取得專案根目錄"""
    # 從 backend/ 目錄執行時，需要往上一層
    current = Path(__file__).parent
    if current.name == "scripts":
        return current.parent
    return current.parent.parent


def read_version_json() -> str:
    """讀取 version.json"""
    version_file = get_root_dir() / "version.json"
    if not version_file.exists():
        print(f"[ERROR] File not found: {version_file}", file=sys.stderr)
        sys.exit(1)

    with version_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data["version"]


def read_package_json_version() -> str:
    """讀取 frontend/package.json 版本"""
    file_path = get_root_dir() / "frontend" / "package.json"
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data["version"]


def read_pyproject_toml_version() -> str:
    """讀取 backend/sj-trading/pyproject.toml 版本"""
    file_path = get_root_dir() / "backend" / "sj-trading" / "pyproject.toml"
    content = file_path.read_text(encoding="utf-8")

    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not match:
        print(f"[ERROR] Cannot parse version from {file_path}", file=sys.stderr)
        sys.exit(1)

    return match.group(1)


def read_app_init_version() -> str:
    """讀取 backend/app/__init__.py 版本"""
    file_path = get_root_dir() / "backend" / "app" / "__init__.py"
    content = file_path.read_text(encoding="utf-8")

    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    if not match:
        print(f"[ERROR] Cannot parse version from {file_path}", file=sys.stderr)
        sys.exit(1)

    return match.group(1)


def main():
    """主函式"""
    try:
        # 讀取所有版本
        version_json = read_version_json()
        package_json = read_package_json_version()
        pyproject_toml = read_pyproject_toml_version()
        app_init = read_app_init_version()

        versions = {
            "version.json": version_json,
            "frontend/package.json": package_json,
            "backend/sj-trading/pyproject.toml": pyproject_toml,
            "backend/app/__init__.py": app_init,
        }

        # 檢查是否一致
        unique_versions = set(versions.values())
        if len(unique_versions) == 1:
            print(f"[OK] Version consistency check passed: {version_json}")
            sys.exit(0)
        else:
            print("[ERROR] Version mismatch detected!", file=sys.stderr)
            for file, version in versions.items():
                print(f"  {file}: {version}", file=sys.stderr)
            print("\nPlease run `python bump.py` to sync versions", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Check failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
