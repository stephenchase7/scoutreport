from http.server import BaseHTTPRequestHandler
import json
import os
import httpx

SYSTEM_PROMPT = """You are a professional youth soccer scout writing reports for Red Bull's Scoutastic platform.

Your task is to convert shorthand scouting notes into polished paragraphs for two sections:
1. "With the Ball" - Technical abilities, attacking actions, possession play
2. "Against the Ball" - Defensive work, pressing, positioning, effort

CRITICAL RULE: Only write about what is explicitly provided in the notes.
- If "With the Ball" notes are empty or say "N/A", output exactly: **With the Ball:** N/A
- If "Against the Ball" notes are empty or say "N/A", output exactly: **Against the Ball:** N/A
- NEVER fabricate or infer observations that weren't provided

Writing style guidelines:
- Professional, observational tone used by elite academy scouts
- Position-specific vocabulary (e.g., "deployed across the front three", "operated as an inverted fullback")
- Balanced assessment - acknowledge strengths AND limitations honestly
- Reference specific actions observed (goals scored, 1v1 situations, saves made)
- 3-5 sentences per section when notes are provided
- Use player's name or position naturally in the text
- Avoid generic praise - be specific about what was observed
- NEVER use em-dashes, use commas or periods instead
- Write in a natural human style, avoid overly formal or AI-sounding phrasing"""

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

        player_name = data.get('playerName', 'Player')
        position = data.get('position', '')
        special_weapon = data.get('specialWeapon', '')
        notes_with_ball = data.get('notesWithBall', '').strip()
        notes_against_ball = data.get('notesAgainstBall', '').strip()

        with_ball_section = notes_with_ball if notes_with_ball else "N/A - no observations provided"
        against_ball_section = notes_against_ball if notes_against_ball else "N/A - no observations provided"
        weapon_section = special_weapon if special_weapon else "Not identified"

        user_prompt = f"""Convert these shorthand scouting notes into a professional Scoutastic report.

Player: {player_name}
Position: {position}
Special Weapon(s): {weapon_section}

WITH THE BALL NOTES:
{with_ball_section}

AGAINST THE BALL NOTES:
{against_ball_section}

Generate two sections. The player's special weapon(s) should be emphasized naturally in the relevant section. If a section's notes say "N/A", output "N/A" for that section. Do not make up observations."""

        try:
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")

            response = httpx.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01'
                },
                json={
                    'model': 'claude-haiku-4-5',
                    'max_tokens': 1024,
                    'system': SYSTEM_PROMPT,
                    'messages': [{'role': 'user', 'content': user_prompt}]
                },
                timeout=60.0
            )

            if response.status_code != 200:
                raise ValueError(f"API error {response.status_code}: {response.text}")

            result = response.json()
            response_text = result['content'][0]['text']

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'report': response_text}).encode())

        except Exception as e:
            error_detail = f"{type(e).__name__}: {str(e)}"
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': error_detail}).encode())
