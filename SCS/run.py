"""
Smart Complaint System (SCS) Kota Bandar Lampung - Application Launcher
Runs the web application server and opens the browser.
"""

import sys
import os
import webbrowser
import threading
import time
import socket

# Ensure base directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import init_db
from app.server import SCSRequestHandler, ThreadedHTTPServer

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def open_browser_delayed(url, delay=1.2):
    def _open():
        time.sleep(delay)
        print(f"Membuka peramban (browser) di {url} ...")
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()

def main():
    print("=" * 65)
    print("   SMART COMPLAINT SYSTEM (SCS) - KOTA BANDAR LAMPUNG")
    print("   Sistem Pengaduan Masyarakat Berbasis Smart City")
    print("   Disusun oleh: Gilang Ramadan (Universitas Teknokrat Indonesia)")
    print("   Pembimbing: Dr. Erliyan Redy Susanto, M.Kom")
    print("=" * 65)

    print("[1/3] Menginisialisasi basis data SQLite dan data awal (seeding)...")
    init_db()

    target_port = 8080
    while is_port_in_use(target_port):
        print(f"Port {target_port} sedang digunakan, mencoba port {target_port + 1}...")
        target_port += 1

    app_url = f"http://127.0.0.1:{target_port}/"
    print(f"[2/3] Memulai server web HTTP di {app_url}...")
    
    # Auto-open browser
    if "--no-browser" not in sys.argv:
        open_browser_delayed(app_url)

    print(f"[3/3] Aplikasi siap digunakan! Tekan Ctrl+C untuk berhenti.")
    print("=" * 65)

    server_address = ('', target_port)
    httpd = ThreadedHTTPServer(server_address, SCSRequestHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nMenutup server. Sampai jumpa!")
        httpd.server_close()

if __name__ == "__main__":
    main()

