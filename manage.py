#!/usr/bin/env python
"""Điểm chạy các lệnh quản trị Django."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Không tìm thấy Django. Hãy kích hoạt môi trường ảo và cài requirements.txt.") from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
