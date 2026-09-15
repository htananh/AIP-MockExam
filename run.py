"""Chạy trang luyện đề qua HTTP để localStorage được lưu bền vững.

Dùng: python run.py   (rồi mở http://localhost:8000/)
"""
import http.server
import os
import socketserver
import webbrowser

PORT = 8000
os.chdir(os.path.dirname(os.path.abspath(__file__)))

Handler = http.server.SimpleHTTPRequestHandler
url = f"http://localhost:{PORT}/"

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Đang phục vụ tại {url}")
    print("Nhấn Ctrl+C để dừng.")
    webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng server.")
