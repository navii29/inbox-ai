#!/usr/bin/env python3
"""
Inbox AI - Universal Email Processor
Supports: Gmail, Outlook/365, IONOS, iCloud, Yahoo, Zoho, Fastmail, ProtonMail, GMX, Custom IMAP
"""
import os
import sys
import json
import time
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import ssl
import smtplib
import socket

CONFIG_FILE = os.path.expanduser("~/.openclaw/workspace/inbox-ai-config.env")

def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#') and line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    return config

def connect_imap(config):
    imap = imaplib.IMAP4_SSL(config['IMAP_SERVER'], int(config.get('IMAP_PORT', 993)))
    imap.login(config['EMAIL_USERNAME'], config['EMAIL_PASSWORD'])
    return imap

def categorize_email(subject, body, sender):
    subject_lower = subject.lower()
    body_lower = body.lower()
    sender_lower = sender.lower()

    spam_keywords = ['unsubscribe', 'newsletter', 'no-reply', 'noreply', 'promo', 'discount']
    if any(k in sender_lower or k in subject_lower for k in spam_keywords):
        return 'spam', 0.0, False

    urgent_keywords = ['urgent', 'asap', 'dringend', 'sofort', 'critical', 'emergency', 'down', 'broken', 'failed', 'immediately']
    urgency_score = sum(1 for k in urgent_keywords if k in subject_lower or k in body_lower) / len(urgent_keywords)

    if any(k in subject_lower for k in ['meeting', 'termin', 'calendly', 'appointment', 'schedule', 'call']):
        category = 'booking'
    elif any(k in subject_lower for k in ['support', 'problem', 'error', 'issue', 'bug', 'help', 'broken', 'hilfe']):
        category = 'support'
    elif any(k in subject_lower for k in ['quote', 'pricing', 'inquiry', 'partnership', 'angebot', 'anfrage']):
        category = 'inquiry'
    elif any(k in subject_lower for k in ['invoice', 'payment', 'billing', 'rechnung', 'zahlung']):
        category = 'billing'
    elif any(k in subject_lower for k in ['legal', 'gdpr', 'dsgvo', 'complaint', 'beschwerde']):
        category = 'legal'
    else:
        category = 'general'

    priority = min(0.3 + urgency_score * 0.7, 1.0)
    requires_escalation = (
        urgency_score > 0.5 or
        category == 'legal' or
        'complaint' in body_lower or
        len(body) > 3000
    )
    return category, priority, requires_escalation

def generate_summary(subject, body):
    for line in body.strip().split('\n'):
        line = line.strip()
        if len(line) > 30 and not line.startswith('>') and not line.startswith('--'):
            return line[:200] + ('...' if len(line) > 200 else '')
    return subject

def should_auto_reply(category, priority, requires_escalation, config):
    if config.get('AUTO_REPLY_ENABLED', 'true').lower() != 'true':
        return False
    if requires_escalation or category == 'spam':
        return False
    if priority > float(config.get('ESCALATION_THRESHOLD', 0.7)):
        return False
    return True

def generate_reply(category, subject, body, config):
    from_name = config.get('FROM_NAME', 'Your Team')
    lang = config.get('SUMMARY_LANGUAGE', 'en')
    calendly = config.get('CALENDLY_LINK', '')

    if lang == 'de':
        templates = {
            'booking': f"Hallo,\n\nvielen Dank für Ihre Terminanfrage.{chr(10) + 'Buchen Sie direkt hier: ' + calendly if calendly else ''}\n\nMit freundlichen Grüßen\n{from_name}",
            'inquiry': f"Hallo,\n\nvielen Dank für Ihr Interesse. Sie erhalten innerhalb von 24 Stunden eine Antwort.\n\nMit freundlichen Grüßen\n{from_name}",
            'support': f"Hallo,\n\nvielen Dank für Ihre Nachricht. Ich bearbeite Ihr Anliegen und melde mich baldmöglichst.\n\nMit freundlichen Grüßen\n{from_name}",
            'billing': f"Hallo,\n\nvielen Dank für Ihre Rechnungsanfrage. Ich prüfe den Sachverhalt umgehend.\n\nMit freundlichen Grüßen\n{from_name}",
            'general': f"Hallo,\n\nvielen Dank für Ihre E-Mail. Ich melde mich schnellstmöglich.\n\nMit freundlichen Grüßen\n{from_name}"
        }
    else:
        templates = {
            'booking': f"Hi,\n\nThank you for reaching out about scheduling.{chr(10) + 'Book directly here: ' + calendly if calendly else ' I will get back to you shortly.'}\n\nBest regards,\n{from_name}",
            'inquiry': f"Hi,\n\nThank you for your interest! I'll get back to you with a full response within 24 hours.\n\nBest regards,\n{from_name}",
            'support': f"Hi,\n\nThank you for reaching out. I've received your request and am looking into it.\n\nBest regards,\n{from_name}",
            'billing': f"Hi,\n\nThank you for your message. I'm reviewing your billing query and will respond shortly.\n\nBest regards,\n{from_name}",
            'general': f"Hi,\n\nThank you for your email. I'll respond as soon as possible.\n\nBest regards,\n{from_name}"
        }
    return templates.get(category, templates['general'])

def send_reply(to_email, subject, body, in_reply_to, config):
    msg = MIMEMultipart()
    msg['From'] = f"{config.get('FROM_NAME')} <{config['EMAIL_USERNAME']}>"
    msg['To'] = to_email
    msg['Subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject
    if in_reply_to:
        msg['In-Reply-To'] = in_reply_to
        msg['References'] = in_reply_to
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    context = ssl.create_default_context()
    with smtplib.SMTP(config['SMTP_SERVER'], int(config.get('SMTP_PORT', 587))) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(config['EMAIL_USERNAME'], config['EMAIL_PASSWORD'])
        server.send_message(msg)

def is_within_working_hours(config):
    if config.get('WORKING_HOURS_START') and config.get('WORKING_HOURS_END'):
        now = datetime.now()
        sh, sm = map(int, config['WORKING_HOURS_START'].split(':'))
        eh, em = map(int, config['WORKING_HOURS_END'].split(':'))
        start = now.replace(hour=sh, minute=sm, second=0)
        end = now.replace(hour=eh, minute=em, second=0)
        days = config.get('WORKING_DAYS', 'mon,tue,wed,thu,fri').split(',')
        day_names = ['mon','tue','wed','thu','fri','sat','sun']
        if day_names[now.weekday()] not in days:
            return False
        return start <= now <= end
    return True

def process_emails(mode='monitor'):
    config = load_config()
    if not config:
        print(f"ERROR: Config not found at {CONFIG_FILE}")
        sys.exit(1)

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Inbox AI | mode={mode.upper()} | {config.get('EMAIL_USERNAME')}")
    within_hours = is_within_working_hours(config)

    try:
        imap = connect_imap(config)
        imap.select('INBOX')
        _, messages = imap.search(None, 'UNSEEN')
        email_ids = messages[0].split() if messages[0] else []
        print(f"  {len(email_ids)} unread email(s)")

        processed = []
        reply_count = 0
        max_replies = int(config.get('MAX_AUTO_REPLY_PER_HOUR', 20))

        for email_id in email_ids:
            try:
                _, msg_data = imap.fetch(email_id, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                subject = msg.get('subject', '(no subject)')
                sender = msg.get('from', '')
                msg_id = msg.get('message-id', '')
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == 'text/plain':
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                else:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

                category, priority, escalate = categorize_email(subject, body, sender)
                summary = generate_summary(subject, body)
                result = {
                    'id': email_id.decode(), 'from': sender, 'subject': subject[:80],
                    'category': category, 'priority': round(priority, 2),
                    'escalation': escalate, 'summary': summary[:200],
                    'action': 'none', 'timestamp': datetime.now().isoformat()
                }

                effective_mode = mode if within_hours else 'monitor'
                if effective_mode == 'auto' and should_auto_reply(category, priority, escalate, config) and reply_count < max_replies:
                    send_reply(sender, subject, generate_reply(category, subject, body, config), msg_id, config)
                    result['action'] = 'auto_replied'
                    reply_count += 1
                    print(f"  ✓ Replied [{category}]: {subject[:50]}")
                    if config.get('AUTO_ARCHIVE', 'true').lower() == 'true':
                        imap.store(email_id, '+FLAGS', '\\Seen')
                elif escalate or priority > float(config.get('ESCALATION_THRESHOLD', 0.7)):
                    result['action'] = 'escalated'
                    print(f"  ⚠ Escalated [{category}]: {subject[:50]}")
                elif category == 'spam':
                    result['action'] = 'spam'
                    imap.store(email_id, '+FLAGS', '\\Seen')
                    print(f"  🗑 Spam: {subject[:50]}")
                else:
                    result['action'] = 'categorized'
                    print(f"  • [{category}] p={priority:.2f}: {subject[:50]}")

                processed.append(result)
                time.sleep(0.5)
            except Exception as e:
                print(f"  ✗ Error: {e}")

        imap.close()
        imap.logout()

        log_dir = os.path.expanduser("~/inbox-ai-logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d')}.json")
        existing = []
        if os.path.exists(log_file):
            with open(log_file) as f:
                try: existing = json.load(f)
                except: pass
        with open(log_file, 'w') as f:
            json.dump(existing + processed, f, indent=2)

        print(f"  Done. Log: {log_file}")
        return processed

    except Exception as e:
        print(f"FATAL: {e}")
        raise

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Inbox AI Email Processor')
    parser.add_argument('--mode', default='monitor', choices=['monitor', 'hybrid', 'auto'])
    args = parser.parse_args()
    process_emails(args.mode)
