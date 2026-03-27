import os
import sys
import socket
import argparse
import shutil
import html
from http.server import HTTPServer, BaseHTTPRequestHandler
import qrcode
from urllib.parse import quote

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QR-Beam 파일 받기</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background: #f0f2f5; margin: 0; }}
.card {{ background: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); text-align: center; max-width: 80%; }}
h2 {{ margin-top: 0; color: #1a1a1a; word-break: keep-all; }}
.filename {{ font-size: 1.1rem; color: #555; word-break: break-all; margin: 15px 0; padding: 10px; background: #f8f9fa; border-radius: 8px; border: 1px solid #eee; }}
.size {{ color: #888; font-size: 0.9rem; margin-bottom: 20px; }}
.btn {{ display: inline-block; padding: 12px 24px; background: #007AFF; color: white; text-decoration: none; border-radius: 10px; font-weight: bold; font-size: 1.1rem; transition: background 0.2s; box-shadow: 0 4px 10px rgba(0, 122, 255, 0.3); }}
.btn:active {{ background: #0056b3; transform: scale(0.98); }}
</style>
</head>
<body>
<div class="card">
  <h2>📥 파일 전송 대기중</h2>
  <div class="filename">{filename}</div>
  <div class="size">크기: {filesize}</div>
  <a class="btn" href="/download">파일 다운로드</a>
</div>
</body>
</html>"""

def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

class SingleFileHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        actual_filename = os.path.basename(self.server.file_path)
        file_size = os.path.getsize(self.server.file_path)

        if self.path == '/':
            # 루트 경로 접속 시 랜딩 페이지 제공
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            # 경로 이름에 <, > 등 특수문자가 있을 때 깨지지 않고 렌더링되게 방어
            html_content = HTML_TEMPLATE.format(
                filename=html.escape(actual_filename),
                filesize=format_size(file_size)
            )
            self.wfile.write(html_content.encode('utf-8'))
            return

        elif self.path == '/download':
            # 102b 버그 원인 해결 1: 한글 파일명 HTTP 헤더 인코딩 오류(UnicodeEncodeError)를 방지하기 위해 RFC 5987 표준 적용
            encoded_filename = quote(actual_filename)
            
            try:
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{encoded_filename}")
                self.send_header("Content-Length", str(file_size))
                self.end_headers()
                
                with open(self.server.file_path, 'rb') as f:
                    shutil.copyfileobj(f, self.wfile)
                
                # 오류없이 전송이 완전히 끝난 경우에만 종료 플래그를 세움
                # (102b 버그 원인 해결 2: 모바일 브라우저의 사전 탐색 요청 등에 의해 서버가 미리 닫히는 현상 방어)
                if hasattr(self.server, "on_download_complete"):
                    self.server.on_download_complete()

            except (BrokenPipeError, ConnectionResetError):
                print("\n[!] 다운로드가 중단되었습니다. (브라우저나 네트워크 연결 끊어짐)")
            except Exception as e:
                print(f"\n[!] 파일 전송 중 오류 발생: {e}")
            return

        # 그 외의 경로는 404
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        pass

def serve_file(file_path):
    ip = get_local_ip()
    
    server = HTTPServer(('0.0.0.0', 0), SingleFileHandler)
    server.file_path = file_path
    port = server.server_port
    
    url = f"http://{ip}:{port}/"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    print(f"\n🚀 Serving: {file_path}")
    print(f"🔗 URL: {url}")
    print("\n[모바일 기기로 아래 QR 코드를 스캔하세요]")
    
    qr.print_tty()
    
    shutdown_flag = False
    
    def on_download_complete():
        nonlocal shutdown_flag
        shutdown_flag = True
        print("\n✅ 파일 다운로드가 완료되었습니다. 서버를 종료합니다...")

    server.on_download_complete = on_download_complete

    try:
        while not shutdown_flag:
            server.handle_request()
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 서버가 중단되었습니다.")
    finally:
        server.server_close()

def main():
    parser = argparse.ArgumentParser(description="QR-Beam (터미널 기반 직통 파일 공유 도구)")
    parser.add_argument("file", help="공유할 파일의 경로 (파일명 포함)")
    args = parser.parse_args()

    file_path = os.path.abspath(args.file)
    if not os.path.isfile(file_path):
        print(f"❌ 오류: 지정한 파일을 찾을 수 없습니다. 경로를 다시 확인해주세요. -> '{file_path}'")
        sys.exit(1)

    serve_file(file_path)

if __name__ == "__main__":
    main()
