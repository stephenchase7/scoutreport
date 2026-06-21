from http.server import BaseHTTPRequestHandler
import json
import os
import httpx
from urllib.parse import urlparse, parse_qs

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_DELETE(self):
        query = parse_qs(urlparse(self.path).query)
        report_id = query.get('id', [None])[0]

        if not report_id:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing report ID'}).encode())
            return

        supabase_url = os.environ.get('SUPABASE_URL', '').strip()
        supabase_key = os.environ.get('SUPABASE_ANON_KEY', '').strip()

        if not supabase_url or not supabase_key:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Supabase not configured'}).encode())
            return

        try:
            response = httpx.delete(
                f'{supabase_url}/rest/v1/reports?id=eq.{report_id}',
                headers={
                    'apikey': supabase_key,
                    'Authorization': f'Bearer {supabase_key}'
                },
                timeout=30.0
            )

            if response.status_code not in [200, 204]:
                raise ValueError(f"Supabase error: {response.text}")

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
