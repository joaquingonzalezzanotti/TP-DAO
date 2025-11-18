"""
Check common SendGrid suppression lists (bounces, blocks, global) for a given email.
Usage:
  . .\.venv\Scripts\Activate.ps1
  $env:SENDGRID_API_KEY = '<your key>'
  python .\tests\check_sendgrid_suppressions.py

Prints JSON responses for each suppression endpoint.
"""
import os
import sys
import requests
import json

API_KEY = os.environ.get('SENDGRID_API_KEY')
if not API_KEY:
    print('SENDGRID_API_KEY no está configurado en el entorno. Aborta.')
    sys.exit(1)

email = input('Email a chequear en supresiones: ').strip()
if not email:
    print('Email obligatorio. Abortando.')
    sys.exit(1)

headers = {'Authorization': f'Bearer {API_KEY}'}
endpoints = [
    ('bounces', f'https://api.sendgrid.com/v3/suppression/bounces?email={email}'),
    ('blocks', f'https://api.sendgrid.com/v3/suppression/blocks?email={email}'),
    ('global', f'https://api.sendgrid.com/v3/asm/suppressions/global?email={email}'),
]

for name, url in endpoints:
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f'--- {name} (status {r.status_code}) ---')
        try:
            parsed = r.json()
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
        except Exception:
            print(r.text)
    except Exception as e:
        print(f'Error consultando {name}: {e}')
