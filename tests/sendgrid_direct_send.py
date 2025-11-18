"""
Small helper to POST a test email directly to SendGrid API and print full response for debugging.
Usage:
  . .\.venv\Scripts\Activate.ps1
  $env:SENDGRID_API_KEY = '<your key>'
  $env:FROM_EMAIL = 'turnosDAO@outlook.com'
  python .\tests\sendgrid_direct_send.py

The script reads SENDGRID_API_KEY and FROM_EMAIL from env and asks for a destination email.
It posts the payload and prints status code, headers and body so you can check what SendGrid returns.
"""

import os
import sys
import json
import requests
from datetime import datetime

API_KEY = os.environ.get('SENDGRID_API_KEY')
FROM = os.environ.get('FROM_EMAIL')

if not API_KEY:
    print('SENDGRID_API_KEY no está configurado en el entorno. Aborta.')
    sys.exit(1)
if not FROM:
    print('FROM_EMAIL no está configurado en el entorno. Aborta.')
    sys.exit(1)

to_email = input('Email destino: ').strip()
if not to_email:
    print('Email destino obligatorio. Abortando.')
    sys.exit(1)

subject = f"DEBUG Test SendGrid {datetime.now().isoformat()}"
body = "Este es un test directo desde sendgrid_direct_send.py para depuración."

payload = {
    "personalizations": [{
        "to": [{"email": to_email}],
        "subject": subject
    }],
    "from": {"email": FROM},
    "content": [{"type": "text/plain", "value": body}]
}

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

print('Enviando petición a SendGrid...')
try:
    resp = requests.post('https://api.sendgrid.com/v3/mail/send', headers=headers, data=json.dumps(payload), timeout=15)
    print('\nStatus code:', resp.status_code)
    print('\nResponse headers:')
    for k, v in resp.headers.items():
        print(f'{k}: {v}')
    print('\nResponse body:')
    print(resp.text)
    if resp.status_code == 202:
        print('\nSendGrid aceptó el mensaje (202). Revisa Activity en 1-2 minutos.')
    else:
        print('\nSendGrid no aceptó el mensaje. Revisa el body para detalles.')
except Exception as e:
    print('Exception al llamar a SendGrid:', e)
    sys.exit(1)
