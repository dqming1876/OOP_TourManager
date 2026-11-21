"""Export the demo as a new SQL file for the local D1 or demo database."""

import argparse
from pathlib import Path

from scripts.demo_data import demo_sql


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    if args.file.suffix != ".sql":
        parser.error("Dùng đường dẫn có đuôi .sql.")
    try:
        with args.file.open("x", encoding="utf-8") as output:
            output.write(demo_sql())
    except FileExistsError:
        parser.error("Tệp đã tồn tại.")
    print("Đã tạo bộ seed. Chỉ nạp vào D1 cục bộ hoặc cơ sở dữ liệu demo.")


if __name__ == "__main__":
    main()
