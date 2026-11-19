#!/usr/bin/env python3
"""Chạy checker gốc, chuẩn hóa duy nhất đường dẫn khi nhận diện file được ghim.

Windows dùng dấu \\ nhưng _protected.json dùng /. Checker gốc vì vậy quét
nhầm calibrate.py (file của đề) như bài viết mới. Không sửa checker gốc,
không bỏ kiểm hash, cấu hình, test, báo cáo hay kiểm đọc đáp án.
Usage: python scripts/check_submission_windows.py  (thêm --no-train nếu chưa train)
"""
from pathlib import Path


def main():
    checker = Path(__file__).resolve().with_name("check_submission.py")
    source = checker.read_text(encoding="utf-8")
    old = "str(p.relative_to(ROOT)) not in prot"
    new = "p.relative_to(ROOT).as_posix() not in prot"
    if source.count(old) != 1:
        raise RuntimeError("Checker đã đổi; cần kiểm tra lại bản vá đường dẫn trước khi chạy")
    source = source.replace(old, new, 1)
    print("Windows compatibility: chuẩn hóa đường dẫn file mẫu sang POSIX; giữ toàn bộ kiểm tra.")
    namespace = {"__name__": "__main__", "__file__": str(checker)}
    exec(compile(source, str(checker), "exec"), namespace)


if __name__ == "__main__":
    main()
