from http.server import BaseHTTPRequestHandler
import json
import os
import httpx

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
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
            response = httpx.get(
                f'{supabase_url}/rest/v1/reports?order=created_at.desc',
                headers={
                    'apikey': supabase_key,
                    'Authorization': f'Bearer {supabase_key}'
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise ValueError(f"Supabase error: {response.text}")

            reports = response.json()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'reports': reports}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
