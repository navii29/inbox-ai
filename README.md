# 📬 Inbox AI — Universal Email Automation

AI-powered email automation for every inbox. Automatically categorizes, prioritizes, summarizes, and replies to emails 24/7.

## ✦ Supported Providers

| Provider | IMAP Server | SMTP Server | Notes |
|---|---|---|---|
| **Gmail** | imap.gmail.com:993 | smtp.gmail.com:587 | App Password required |
| **Outlook / 365** | outlook.office365.com:993 | smtp.office365.com:587 | Enable IMAP in settings |
| **IONOS / 1&1** | imap.ionos.de:993 | smtp.ionos.de:587 | Standard password |
| **Apple iCloud** | imap.mail.me.com:993 | smtp.mail.me.com:587 | App Password required |
| **Yahoo Mail** | imap.mail.yahoo.com:993 | smtp.mail.yahoo.com:587 | App Password required |
| **Zoho Mail** | imap.zoho.com:993 | smtp.zoho.com:587 | Enable IMAP in settings |
| **Fastmail** | imap.fastmail.com:993 | smtp.fastmail.com:587 | App Password required |
| **ProtonMail** | 127.0.0.1:1143 | 127.0.0.1:1025 | Bridge app required |
| **GMX** | imap.gmx.net:993 | mail.gmx.net:587 | Enable IMAP in settings |
| **Custom IMAP** | your server | your server | Any standard provider |

---

## 🚀 Quick Start (Local)

### 1. Configure

```bash
mkdir -p ~/.openclaw/workspace
cp inbox-ai-config.template.env ~/.openclaw/workspace/inbox-ai-config.env
nano ~/.openclaw/workspace/inbox-ai-config.env  # fill in your credentials
```

### 2. Test connection

```bash
python3 scripts/test_email_connection.py
```

Expected output:
```
✅ IMAP connected! (42 total, 3 unread)
✅ SMTP connected!
✅ All tests passed — ready to deploy!
```

### 3. Run in monitor mode first (safe — no replies sent)

```bash
python3 scripts/inbox_processor.py --mode=monitor
```

### 4. Go live

```bash
python3 scripts/inbox_processor.py --mode=auto
```

### 5. Automate with cron (every 10 minutes)

```bash
crontab -e
# Add:
*/10 * * * * python3 ~/inbox-ai/scripts/inbox_processor.py --mode=auto >> ~/inbox-ai-logs/cron.log 2>&1
```

---

## ☁️ Deploy to GitHub Actions (Free, 24/7)

Run Inbox AI automatically in the cloud every 10 minutes — free with GitHub's included Actions minutes.

### Step 1: Add your secrets

Go to your repository → **Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:

| Secret Name | Example Value |
|---|---|
| `IMAP_SERVER` | `imap.ionos.de` |
| `IMAP_PORT` | `993` |
| `SMTP_SERVER` | `smtp.ionos.de` |
| `SMTP_PORT` | `587` |
| `EMAIL_USERNAME` | `kontakt@navii-automation.de` |
| `EMAIL_PASSWORD` | `your-password` |
| `FROM_NAME` | `Navii Automation` |
| `AUTO_REPLY_ENABLED` | `true` |
| `ESCALATION_THRESHOLD` | `0.70` |
| `SUMMARY_LANGUAGE` | `de` |
| `MAX_AUTO_REPLY_PER_HOUR` | `20` |
| `CALENDLY_LINK` | `https://calendly.com/your-link` |
| `ESCALATION_PHONE` | `+49-123-456789` |
| `AUTO_ARCHIVE` | `true` |

### Step 2: Enable the workflow

The workflow file is already at `.github/workflows/inbox-ai.yml`. It runs:
- ✅ **Every 10 minutes**, Monday–Friday, 7am–7pm UTC
- ✅ **Manually** via Actions tab → "Run workflow" (choose monitor/hybrid/auto)

### Step 3: Monitor results

- Go to **Actions tab** in your repository
- Click any run to see the full processing log
- Download log artifacts (kept 30 days)

---

## ⚙️ Configuration Reference

Edit `~/.openclaw/workspace/inbox-ai-config.env`:

```env
# Required
IMAP_SERVER=imap.ionos.de
IMAP_PORT=993
SMTP_SERVER=smtp.ionos.de
SMTP_PORT=587
EMAIL_USERNAME=you@yourdomain.com
EMAIL_PASSWORD=your-password
FROM_NAME=Your Company

# AI Behaviour
AUTO_REPLY_ENABLED=true        # true/false
ESCALATION_THRESHOLD=0.70      # 0.0–1.0 (higher = fewer escalations)
SUMMARY_LANGUAGE=de            # en, de, fr, es, it
MAX_AUTO_REPLY_PER_HOUR=20     # rate limiting

# Optional
CALENDLY_LINK=https://calendly.com/your-link
ESCALATION_PHONE=+49-123-456789
AUTO_ARCHIVE=true
WORKING_HOURS_START=08:00
WORKING_HOURS_END=18:00
WORKING_DAYS=mon,tue,wed,thu,fri
```

---

## 🤖 Automation Modes

| Mode | Behaviour |
|---|---|
| `monitor` | Read-only. Categorizes & logs. No replies sent. |
| `hybrid` | Drafts replies, logs them. No sending. Good for review. |
| `auto` | Full automation. Sends replies, archives spam, escalates urgent. |

---

## 📊 Email Categories

| Category | Trigger Keywords | Auto-Reply? |
|---|---|---|
| `booking` | meeting, termin, calendly, appointment | ✅ Yes |
| `inquiry` | quote, pricing, interest, angebot | ✅ Yes |
| `support` | help, error, problem, broken | ✅ Yes |
| `billing` | invoice, payment, rechnung | ✅ Yes |
| `legal` | gdpr, complaint, lawsuit | ⚠️ Escalated |
| `spam` | newsletter, unsubscribe | 🗑 Archived |
| `general` | (everything else) | ✅ Yes |

Emails above the **ESCALATION_THRESHOLD** urgency score are flagged for human review regardless of category.

---

## 🔐 App Passwords (Required for some providers)

**Gmail:**
1. myaccount.google.com/security → 2-Step Verification
2. Scroll to "App passwords" → Generate → name it "Inbox AI"
3. Use the 16-character code as your `EMAIL_PASSWORD`
4. Also enable IMAP: Gmail Settings → Forwarding and POP/IMAP → Enable IMAP

**Apple iCloud:**
1. appleid.apple.com → Sign In & Security → App-Specific Passwords
2. Generate → "Inbox AI" → copy password

**Yahoo Mail:**
1. Yahoo Account Security → Manage app passwords
2. Generate app password for "Inbox AI"

**Fastmail:**
1. Settings → Privacy & Security → Third-party apps → New app password

**ProtonMail:**
1. Install Proton Mail Bridge from proton.me/mail/bridge
2. Keep Bridge running; use Bridge-provided password and localhost ports

---

## 🛠 Troubleshooting

**Authentication failed:**
- Gmail/iCloud/Yahoo/Fastmail → you MUST use an App Password
- Make sure IMAP is enabled in your provider's settings
- Double-check the email address (full address required)

**Connection refused / timeout:**
- Verify IMAP/SMTP server addresses
- Check port numbers (993 for IMAP SSL, 587 for SMTP STARTTLS)
- Disable VPN if active and retry
- IONOS may block new connections for ~10 minutes

**SSL certificate error:**
- Update Python: `brew upgrade python3`
- On macOS: run `/Applications/Python 3.x/Install Certificates.command`
- Verify system clock is correct

**Emails not sending:**
- Check `AUTO_REPLY_ENABLED=true` in config
- Lower `ESCALATION_THRESHOLD` (e.g. 0.80) if too many are being escalated
- Check SMTP credentials separately from IMAP

---

## 📁 Project Structure

```
inbox-ai/
├── scripts/
│   ├── inbox_processor.py          # Main automation engine
│   └── test_email_connection.py    # Connection tester
├── .github/
│   └── workflows/
│       └── inbox-ai.yml            # GitHub Actions (runs every 10 min)
├── inbox-ai-config.template.env    # Config template (safe to commit)
├── .gitignore                      # Prevents committing credentials
└── README.md
```

> ⚠️ **Never commit your actual `inbox-ai-config.env`** — it contains credentials. The `.gitignore` already excludes it. Use GitHub Secrets for cloud deployment.

---

## 📜 License

MIT — free to use, modify, and deploy.
