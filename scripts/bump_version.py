#!/usr/bin/env python3
"""
版本遞增腳本

自動更新專案所有版本定義檔案，並執行 Git commit 和 tag
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Literal


def get_root_dir() -> Path:
    """取得專案根目錄"""
    return Path(__file__).parent.parent


def read_version() -> str:
    """從 version.json 讀取當前版本"""
    version_file = get_root_dir() / "version.json"
    with version_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data["version"]


def write_version(version: str) -> None:
    """寫入版本到 version.json"""
    version_file = get_root_dir() / "version.json"
    with version_file.open("w", encoding="utf-8") as f:
        json.dump({"version": version}, f, indent=2, ensure_ascii=False)
        f.write("\n")


def bump_version(current: str, bump_type: Literal["patch", "minor", "major"]) -> str:
    """遞增版本號"""
    parts = current.split(".")
    if len(parts) != 3:
        raise ValueError(f"無效的版本格式: {current}")

    major, minor, patch = map(int, parts)

    if bump_type == "patch":
        patch += 1
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "major":
        major += 1
        minor = 0
        patch = 0

    return f"{major}.{minor}.{patch}"


def update_package_json(version: str) -> None:
    """更新 frontend/package.json"""
    file_path = get_root_dir() / "frontend" / "package.json"
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    data["version"] = version

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def update_pyproject_toml(version: str) -> None:
    """更新 backend/sj-trading/pyproject.toml"""
    file_path = get_root_dir() / "backend" / "sj-trading" / "pyproject.toml"
    content = file_path.read_text(encoding="utf-8")

    # 使用正則替換 version
    pattern = r'(version\s*=\s*")[^"]+(")'
    replacement = rf"\g<1>{version}\g<2>"
    new_content = re.sub(pattern, replacement, content)

    file_path.write_text(new_content, encoding="utf-8")


def update_app_init(version: str) -> None:
    """更新 backend/app/__init__.py"""
    file_path = get_root_dir() / "backend" / "app" / "__init__.py"
    content = file_path.read_text(encoding="utf-8")

    # 檢查是否已有 __version__
    if "__version__" in content:
        # 替換現有的 __version__
        pattern = r'(__version__\s*=\s*")[^"]+(")'
        replacement = rf"\g<1>{version}\g<2>"
        new_content = re.sub(pattern, replacement, content)
    else:
        # 在 docstring 後添加 __version__
        new_content = f'"""FastAPI 應用初始化"""\n\n__version__ = "{version}"\n'

    file_path.write_text(new_content, encoding="utf-8")


def git_commit_and_tag(version: str) -> None:
    """執行 Git commit 和 tag"""
    root_dir = get_root_dir()

    try:
        # Git add
        subprocess.run(
            ["git", "add", "version.json", "frontend/package.json"],
            cwd=root_dir,
            check=True,
        )
        subprocess.run(
            ["git", "add", "backend/sj-trading/pyproject.toml"],
            cwd=root_dir,
            check=True,
        )
        subprocess.run(
            ["git", "add", "backend/app/__init__.py"],
            cwd=root_dir,
            check=True,
        )

        # Git commit
        commit_msg = f"chore: bump version to {version}"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=root_dir,
            check=True,
        )

        # Git tag
        tag_name = f"v{version}"
        subprocess.run(
            ["git", "tag", tag_name],
            cwd=root_dir,
            check=True,
        )

        print(f"✅ 已建立 Git commit: {commit_msg}")
        print(f"✅ 已建立 Git tag: {tag_name}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git 操作失敗: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """主函式"""
    parser = argparse.ArgumentParser(description="遞增專案版本號")
    parser.add_argument(
        "--patch",
        action="store_const",
        const="patch",
        dest="bump_type",
        help="遞增 PATCH 版本 (預設)",
    )
    parser.add_argument(
        "--minor",
        action="store_const",
        const="minor",
        dest="bump_type",
        help="遞增 MINOR 版本",
    )
    parser.add_argument(
        "--major",
        action="store_const",
        const="major",
        dest="bump_type",
        help="遞增 MAJOR 版本",
    )

    args = parser.parse_args()
    bump_type = args.bump_type or "patch"

    # 讀取當前版本
    current_version = read_version()
    print(f"當前版本: {current_version}")

    # 遞增版本
    new_version = bump_version(current_version, bump_type)
    print(f"新版本: {new_version}")

    # 更新所有檔案
    print("\n更新檔案...")
    write_version(new_version)
    print("✅ version.json")

    update_package_json(new_version)
    print("✅ frontend/package.json")

    update_pyproject_toml(new_version)
    print("✅ backend/sj-trading/pyproject.toml")

    update_app_init(new_version)
    print("✅ backend/app/__init__.py")

    # Git commit 和 tag
    print("\n執行 Git 操作...")
    git_commit_and_tag(new_version)

    print(f"\n🎉 版本已成功遞增至 {new_version}")


if __name__ == "__main__":
    main()
