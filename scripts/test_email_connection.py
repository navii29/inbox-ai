#!/usr/bin/env python3
"""
Inbox AI - Connection Tester
Run this before going live to verify IMAP + SMTP work correctly.
"""
import os, sys, imaplib, smtplib, ssl, socket

CONFIG_FILE = os.path.expanduser("~/.openclaw/workspace/inbox-ai-config.env")

def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#') and line:
                    k, v = line.split('=', 1)
                    config[k.strip()] = v.strip()
    return config

def test_connection():
    config = load_config()
    print("=" * 55)
    print("  Inbox AI — Connection Test")
    print("=" * 55)

    if not config:
        print(f"\n❌ Config not found: {CONFIG_FILE}")
        return False

    required = ['IMAP_SERVER', 'SMTP_SERVER', 'EMAIL_USERNAME', 'EMAIL_PASSWORD']
    missing = [f for f in required if not config.get(f)]
    if missing:
        print(f"\n❌ Missing: {', '.join(missing)}")
        return False

    print(f"\n  Account : {config['EMAIL_USERNAME']}")
    print(f"  IMAP    : {config['IMAP_SERVER']}:{config.get('IMAP_PORT', 993)}")
    print(f"  SMTP    : {config['SMTP_SERVER']}:{config.get('SMTP_PORT', 587)}")

    ok = True

    print("\n📡 DNS...")
    for key in ['IMAP_SERVER', 'SMTP_SERVER']:
        h = config[key]
        if h in ('127.0.0.1', 'localhost'):
            print(f"   • {h} (local)")
            continue
        try:
            print(f"   ✓ {h} → {socket.gethostbyname(h)}")
        except:
            print(f"   ✗ Cannot resolve {h}")
            ok = False

    print("\n📥 IMAP...")
    try:
        imap = imaplib.IMAP4_SSL(config['IMAP_SERVER'], int(config.get('IMAP_PORT', 993)))
        imap.login(config['EMAIL_USERNAME'], config['EMAIL_PASSWORD'])
        imap.select('INBOX')
        _, all_msgs = imap.search(None, 'ALL')
        _, unread = imap.search(None, 'UNSEEN')
        total = len(all_msgs[0].split()) if all_msgs[0] else 0
        unread_n = len(unread[0].split()) if unread[0] else 0
        print(f"   ✅ Connected! {total} total, {unread_n} unread")
        imap.close(); imap.logout()
    except imaplib.IMAP4.error as e:
        print(f"   ❌ Auth failed: {e}")
        print("      → Use App Password for Gmail / iCloud / Yahoo")
        ok = False
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        ok = False

    print("\n📤 SMTP...")
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(config['SMTP_SERVER'], int(config.get('SMTP_PORT', 587)), timeout=15) as s:
            s.ehlo(); s.starttls(ctx); s.ehlo()
            s.login(config['EMAIL_USERNAME'], config['EMAIL_PASSWORD'])
            print("   ✅ Connected!")
    except smtplib.SMTPAuthenticationError as e:
        print(f"   ❌ Auth failed: {e}")
        ok = False
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        ok = False

    print()
    if ok:
        print("✅ All tests passed — ready to deploy!\n")
        print("   python3 scripts/inbox_processor.py --mode=monitor")
        print("   python3 scripts/inbox_processor.py --mode=auto")
    else:
        print("❌ Fix errors above, then re-run this test.")
    return ok

if __name__ == '__main__':
    sys.exit(0 if test_connection() else 1)
