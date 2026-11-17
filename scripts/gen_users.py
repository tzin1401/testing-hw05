"""Sinh data/users.csv: 300 tài khoản test perf001..perf300.

SUT chỉ seed 2 user (admin, test) nên không đủ cho nhiều VU chạy song song.
Mật khẩu Perf@NNNa thỏa yêu cầu mật khẩu mạnh của FR-01 (hoa, thường, số, ký tự đặc biệt, >= 8).
scripts/reset_sut.sh sẽ đăng ký các tài khoản này vào SUT qua POST /api/register.

Chạy: python3 scripts/gen_users.py
"""
from pathlib import Path

N = 300
out = Path(__file__).resolve().parent.parent / "data" / "users.csv"
with out.open("w") as f:
    f.write("name,email,password\n")
    for i in range(1, N + 1):
        f.write(f"Perf User {i:03d},perf{i:03d}@eshop.com,Perf@{i:03d}a\n")
print(f"Wrote {N} users to {out}")
