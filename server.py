#!/usr/bin/env python3
"""
Scouting Report Generator - Local Server
Converts shorthand notes to Scoutastic-format reports using Claude API
"""

import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
from datetime import datetime
import anthropic
from dotenv import load_dotenv

REPORTS_FOLDER = os.path.expanduser("~/Desktop/Scouting Reports")

# Load API key from .env
load_dotenv()

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
- NEVER use em-dashes (—), use commas or periods instead
- Write in a natural human style, avoid overly formal or AI-sounding phrasing"""

class ReportHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            try:
                player_name = data.get('playerName', 'Unknown')
                # Create safe filename
                safe_name = "".join(c for c in player_name if c.isalnum() or c in (' ', '-', '_')).strip()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{safe_name}_{timestamp}.json"
                filepath = os.path.join(REPORTS_FOLDER, filename)

                # Save the report data
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'filename': filename}).encode())

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())

        elif self.path == '/generate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            player_name = data.get('playerName', 'Player')
            position = data.get('position', '')
            special_weapon = data.get('specialWeapon', '')
            notes_with_ball = data.get('notesWithBall', '').strip()
            notes_against_ball = data.get('notesAgainstBall', '').strip()

            # Build the prompt with clear separation
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
                client = anthropic.Anthropic()

                message = client.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )

                response_text = message.content[0].text

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'report': response_text}).encode())

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, ReportHandler)
    print(f"\n🔴 Scouting Report Generator running at http://localhost:{port}")
    print("📋 Open index.html in your browser to start generating reports")
    print("Press Ctrl+C to stop\n")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
