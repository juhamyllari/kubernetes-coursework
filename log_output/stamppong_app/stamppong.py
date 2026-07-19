
import http.server
import socketserver
import uuid
from datetime import datetime
from pathlib import Path


COUNTER_FILE = Path('/data/pingpong_counter.txt')


class Handler(http.server.BaseHTTPRequestHandler):
	server_uuid = str(uuid.uuid4())

	def do_GET(self):
		if self.path != '/':
			self.send_error(404)
			return

		# read pong count
		try:
			text = COUNTER_FILE.read_text(encoding='utf-8').strip()
			pong_count = int(text) if text else 0
		except Exception:
			pong_count = 0

		timestamp = datetime.utcnow().isoformat() + 'Z'
		body = f"{timestamp}: {self.server_uuid}.\nPing / Pongs: {pong_count}\n"

		body_bytes = body.encode('utf-8')
		self.send_response(200)
		self.send_header('Content-Type', 'text/plain; charset=utf-8')
		self.send_header('Content-Length', str(len(body_bytes)))
		self.end_headers()
		self.wfile.write(body_bytes)


def run(port=8000):
	with socketserver.TCPServer(('', port), Handler) as httpd:
		print(f'Serving on port {port}, UUID: {Handler.server_uuid}')
		try:
			httpd.serve_forever()
		except KeyboardInterrupt:
			pass


if __name__ == '__main__':
	run()

