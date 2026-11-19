"""Chuẩn hóa LF cho manifest trước train trên Windows; không đổi nội dung JSON."""
import hashlib
import json
from pathlib import Path


def main():
    path = Path(__file__).resolve().parents[1] / "submission/export/clean_v1/manifest.json"
    before = path.read_bytes()
    after = before.replace(b"\r\n", b"\n")
    if json.loads(before) != json.loads(after):
        raise ValueError("Nội dung JSON thay đổi; từ chối ghi")
    if before != after:
        path.write_bytes(after)
    print("Manifest LF SHA1:", hashlib.sha1(after).hexdigest())


if __name__ == "__main__":
    main()
