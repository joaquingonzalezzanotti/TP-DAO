import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
import json
import requests


class MailService:
    """Servicio simple para enviar notificaciones por mail.

    Comportamiento:
    - Si las variables de entorno SMTP_* están definidas (HOST, PORT, USER, PASS, FROM)
      intentará enviar el correo vía SMTP/TLS.
    - Si no hay configuración SMTP, guardará un archivo simulando el envío en
      `front/salidas/emails/` con nombre timestamp para facilitar pruebas locales.

    Método público:
    - enviar_turno(to_email: str, turno) -> bool
      Intenta enviar un email con la información del turno. Devuelve True si
      el envío (o simulación) fue exitoso, False en caso contrario.
    """

    @staticmethod
    def enviar_turno(to_email: str, turno) -> bool:
        if not to_email:
            print("[MailService] Dirección de mail destino vacía. No se enviará el correo.")
            return False

        subject = f"Confirmación de turno #{getattr(turno, 'id_turno', '')}"
        fecha = getattr(turno, 'fecha_hora_inicio', '')
        cuerpo = (
            f"Detalle del turno:\n\n"
            f"ID: {getattr(turno, 'id_turno', '')}\n"
            f"Fecha/Hora: {fecha}\n"
            f"Médico (matrícula): {getattr(turno, 'nro_matricula_medico', '')}\n"
            f"Motivo: {getattr(turno, 'motivo', '')}\n"
            f"Observaciones: {getattr(turno, 'observaciones', '')}\n"
        )

        smtp_host = os.environ.get('SMTP_HOST')
        smtp_port = os.environ.get('SMTP_PORT')
        smtp_user = os.environ.get('SMTP_USER')
        smtp_pass = os.environ.get('SMTP_PASS')
        from_email = os.environ.get('FROM_EMAIL', smtp_user)
        sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        # Opt-in to allow the service to remove sendgrid suppressions automatically (use with caution)
        allow_unsuppress = os.environ.get('ALLOW_SENDGRID_UNSUPPRESS', 'false').lower() in ('1', 'true', 'yes')

        def _log_error(msg: str):
            try:
                root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                out_dir = os.path.join(root, 'front', 'salidas', 'emails')
                os.makedirs(out_dir, exist_ok=True)
                log_path = os.path.join(out_dir, 'mail_errors.log')
                ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                with open(log_path, 'a', encoding='utf-8') as lf:
                    lf.write(f"[{ts}] {msg}\n")
            except Exception:
                # no podemos hacer mucho si el log falla
                pass

        def _log_success(msg: str):
            try:
                root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                out_dir = os.path.join(root, 'front', 'salidas', 'emails')
                os.makedirs(out_dir, exist_ok=True)
                success_path = os.path.join(out_dir, 'mail_success.log')
                ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                with open(success_path, 'a', encoding='utf-8') as lf:
                    lf.write(f"[{ts}] {msg}\n")
            except Exception:
                pass

        # Si falta configuración SMTP, caeremos a modo 'simulado' escribiendo un archivo
        # Priorizar SendGrid si está configurado
        if sendgrid_key:
            try:
                root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                out_dir = os.path.join(root, 'front', 'salidas', 'emails')
                # Construir payload SendGrid
                payload = {
                    "personalizations": [{
                        "to": [{"email": to_email}],
                        "subject": subject
                    }],
                    "from": {"email": from_email or smtp_user or "no-reply@example.com"},
                    "content": [{"type": "text/plain", "value": cuerpo}]
                }
                headers = {
                    "Authorization": f"Bearer {sendgrid_key}",
                    "Content-Type": "application/json"
                }
                # Antes de enviar: comprobar si el destinatario está en listas de supresión
                try:
                    suppressed = []
                    # bounces
                    r_b = requests.get(f'https://api.sendgrid.com/v3/suppression/bounces?email={to_email}', headers=headers, timeout=8)
                    if r_b.status_code == 200 and r_b.text and r_b.text != '[]':
                        suppressed.append(('bounces', r_b.text))
                    # blocks
                    r_blk = requests.get(f'https://api.sendgrid.com/v3/suppression/blocks?email={to_email}', headers=headers, timeout=8)
                    if r_blk.status_code == 200 and r_blk.text and r_blk.text != '[]':
                        suppressed.append(('blocks', r_blk.text))
                    # global suppressions
                    r_glob = requests.get(f'https://api.sendgrid.com/v3/asm/suppressions/global?email={to_email}', headers=headers, timeout=8)
                    if r_glob.status_code == 200 and r_glob.text and r_glob.text != '[]':
                        suppressed.append(('global', r_glob.text))

                    if suppressed:
                        detail = '; '.join([f"{k}:{v}" for k, v in suppressed])
                        msg = f"SendGrid suppression detected for {to_email}: {detail}"
                        print(f"[MailService WARN] {msg}")
                        _log_error(msg)
                        # Intentar eliminar la supresión solo si el admin explicitamente lo permite
                        if allow_unsuppress:
                            try:
                                for kind, _ in suppressed:
                                    if kind == 'bounces':
                                        requests.delete(f'https://api.sendgrid.com/v3/suppression/bounces/{to_email}', headers=headers, timeout=8)
                                    elif kind == 'blocks':
                                        requests.delete(f'https://api.sendgrid.com/v3/suppression/blocks/{to_email}', headers=headers, timeout=8)
                                    elif kind == 'global':
                                        requests.delete(f'https://api.sendgrid.com/v3/asm/suppressions/global/{to_email}', headers=headers, timeout=8)
                                # reintentar envío tras eliminar supresiones
                            except Exception as e_uns:
                                _log_error(f"Failed to remove suppression for {to_email}: {e_uns}")
                                # No abortamos; intentaremos enviar de todos modos

                except Exception as e_check:
                    # Si falla la comprobación de supresiones, lo registramos pero intentamos enviar
                    _log_error(f"Error checking SendGrid suppressions for {to_email}: {e_check}")

                resp = requests.post('https://api.sendgrid.com/v3/mail/send', headers=headers, data=json.dumps(payload), timeout=10)
                if resp.status_code == 202:
                    # Extraer X-Message-Id y loguear cabeceras para trazabilidad en SendGrid Activity
                    msg_id = resp.headers.get('X-Message-Id') or resp.headers.get('X-Message-Id'.lower())
                    try:
                        hdrs = dict(resp.headers)
                    except Exception:
                        hdrs = {k: v for k, v in resp.headers.items()}
                    hdrs_str = json.dumps(hdrs, ensure_ascii=False)
                    succ_msg = f"Email enviado a {to_email} via SendGrid | message_id={msg_id} | headers={hdrs_str}"
                    print(f"[MailService] {succ_msg}")
                    _log_success(succ_msg)
                    return True
                else:
                    try:
                        hdrs = dict(resp.headers)
                    except Exception:
                        hdrs = {k: v for k, v in resp.headers.items()}
                    hdrs_str = json.dumps(hdrs, ensure_ascii=False)
                    err = f"SendGrid returned {resp.status_code}: {resp.text} | headers={hdrs_str}"
                    print(f"[MailService ERROR] {err}")
                    _log_error(err)
                    # continuar y probar fallback SMTP/file
            except Exception as e:
                err = f"SendGrid exception: {e}"
                print(f"[MailService ERROR] {err}")
                _log_error(err)

        if not smtp_host or not smtp_port or not smtp_user or not smtp_pass:
            try:
                root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                out_dir = os.path.join(root, 'front', 'salidas', 'emails')
                os.makedirs(out_dir, exist_ok=True)
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"mail_turno_{ts}_{getattr(turno, 'id_turno', '')}.txt"
                path = os.path.join(out_dir, filename)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(f"To: {to_email}\n")
                    f.write(f"Subject: {subject}\n\n")
                    f.write(cuerpo)
                print(f"[MailService] Simulated email written to: {path}")
                return True
            except Exception as e:
                print(f"[MailService ERROR] No se pudo escribir el archivo de simulación: {e}")
                return False

        # Intentar envío SMTP real (primero STARTTLS, si falla, intentar SMTP_SSL)
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        msg.set_content(cuerpo)

        port = int(smtp_port)
        # Intento #1: SMTP con STARTTLS (puerto típico 587)
        try:
            with smtplib.SMTP(smtp_host, port, timeout=15) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            print(f"[MailService] Email enviado a {to_email} usando STARTTLS")
            return True
        except Exception as e_starttls:
            print(f"[MailService WARN] STARTTLS falló: {e_starttls}. Intentando SMTP_SSL...")

        # Intento #2: SMTP_SSL (puerto típico 465)
        try:
            with smtplib.SMTP_SSL(smtp_host, port, timeout=15) as server_ssl:
                server_ssl.login(smtp_user, smtp_pass)
                server_ssl.send_message(msg)
            print(f"[MailService] Email enviado a {to_email} usando SMTP_SSL")
            return True
        except Exception as e_ssl:
            print(f"[MailService ERROR] Falló el envío SMTP_SSL: {e_ssl}")
            return False
