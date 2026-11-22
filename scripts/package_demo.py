"""Package the complete Python demo, static assets, migrations and evidence."""

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from scripts.sqlite_worker import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    if args.file.suffix != ".zip":
        parser.error("Dùng đường dẫn có đuôi .zip.")
    items = ("dist", "Database", "backend", "scripts", "tests", "docs", "entry.py",
             "pyproject.toml", "pylock.toml", "uv.lock", "package.json", "package-lock.json", "README.md", "wrangler.jsonc",
             "wrangler.example.jsonc", ".dev.vars.example", ".gitignore")
    with ZipFile(args.file, "x", compression=ZIP_DEFLATED) as archive:
        for name in items:
            path = ROOT / name
            for item in path.rglob("*") if path.is_dir() else (path,):
                target = item.relative_to(ROOT)
                if item.is_file() and "__pycache__" not in target.parts and item.name != ".DS_Store":
                    if not target.is_relative_to("dist/server"):
                        archive.write(item, target)
    print(args.file.resolve())


if __name__ == "__main__":
    main()
