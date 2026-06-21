from http.server import BaseHTTPRequestHandler
import json
import os
import httpx

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Invalid JSON'}).encode())
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
            response = httpx.post(
                f'{supabase_url}/rest/v1/reports',
                headers={
                    'Content-Type': 'application/json',
                    'apikey': supabase_key,
                    'Authorization': f'Bearer {supabase_key}',
                    'Prefer': 'return=representation'
                },
                json={
                    'player_name': data.get('playerName', 'Unknown'),
                    'position': data.get('position', ''),
                    'event': data.get('event', ''),
                    'date': data.get('date') or None,
                    'special_weapon': data.get('specialWeapon', ''),
                    'notes_with_ball': data.get('notesWithBall', ''),
                    'notes_against_ball': data.get('notesAgainstBall', ''),
                    'report_with_ball': data.get('reportWithBall', ''),
                    'report_against_ball': data.get('reportAgainstBall', '')
                },
                timeout=30.0
            )

            if response.status_code not in [200, 201]:
                raise ValueError(f"Supabase error: {response.text}")

            result = response.json()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'report': result}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
