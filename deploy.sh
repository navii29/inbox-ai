#!/bin/bash
# ============================================================
#  Inbox AI — GitHub Deploy Script
#  Usage: bash deploy.sh YOUR_GITHUB_TOKEN YOUR_GITHUB_USERNAME
# ============================================================

set -e

TOKEN=$1
USERNAME=$2
REPO_NAME="inbox-ai"

if [ -z "$TOKEN" ] || [ -z "$USERNAME" ]; then
  echo "Usage: bash deploy.sh <github_token> <github_username>"
  echo "Example: bash deploy.sh ghp_xxxx navii-automation"
  exit 1
fi

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   Inbox AI — GitHub Deployer         ║"
echo "╚══════════════════════════════════════╝"
echo ""

# 1. Create the repo
echo "① Creating repository '$REPO_NAME'..."
RESPONSE=$(curl -s -X POST \
  -H "Authorization: token $TOKEN" \
  -H "Content-Type: application/json" \
  https://api.github.com/user/repos \
  -d "{
    \"name\": \"$REPO_NAME\",
    \"description\": \"AI-powered email automation for every inbox provider\",
    \"private\": false,
    \"auto_init\": false
  }")

REPO_URL=$(echo $RESPONSE | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('html_url','ERROR'))" 2>/dev/null)

if [[ "$REPO_URL" == "ERROR" ]] || [[ -z "$REPO_URL" ]]; then
  # Repo might already exist
  echo "   (Repository may already exist — continuing...)"
  REPO_URL="https://github.com/$USERNAME/$REPO_NAME"
fi

echo "   ✓ Repository: $REPO_URL"

# 2. Init git and push
echo ""
echo "② Pushing files to GitHub..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

git init -q
git checkout -b main 2>/dev/null || git checkout main
git add .
git commit -q -m "🚀 Initial deploy — Inbox AI universal email automation

- Universal IMAP/SMTP processor (Gmail, Outlook, IONOS, iCloud, Yahoo, Zoho, Fastmail, ProtonMail, GMX)
- GitHub Actions workflow (runs every 10 min, Mon–Fri)
- Connection tester script
- Full provider documentation"

git remote remove origin 2>/dev/null || true
git remote add origin "https://$TOKEN@github.com/$USERNAME/$REPO_NAME.git"
git push -u origin main -q

echo "   ✓ Code pushed!"

# 3. Print secrets setup instructions
echo ""
echo "③ Add these secrets to your repository:"
echo "   $REPO_URL/settings/secrets/actions/new"
echo ""
echo "   ┌─────────────────────────────────────────────────┐"
echo "   │  Secret Name               │ Your Value         │"
echo "   ├─────────────────────────────────────────────────┤"
echo "   │  IMAP_SERVER               │ imap.ionos.de      │"
echo "   │  IMAP_PORT                 │ 993                │"
echo "   │  SMTP_SERVER               │ smtp.ionos.de      │"
echo "   │  SMTP_PORT                 │ 587                │"
echo "   │  EMAIL_USERNAME            │ your@email.com     │"
echo "   │  EMAIL_PASSWORD            │ your-password      │"
echo "   │  FROM_NAME                 │ Your Company       │"
echo "   │  AUTO_REPLY_ENABLED        │ true               │"
echo "   │  ESCALATION_THRESHOLD      │ 0.70               │"
echo "   │  SUMMARY_LANGUAGE          │ de                 │"
echo "   │  MAX_AUTO_REPLY_PER_HOUR   │ 20                 │"
echo "   │  CALENDLY_LINK             │ https://...        │"
echo "   │  ESCALATION_PHONE          │ +49-123-...        │"
echo "   │  AUTO_ARCHIVE              │ true               │"
echo "   └─────────────────────────────────────────────────┘"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  ✅ Deployment complete!                             ║"
echo "║                                                      ║"
echo "║  Repository : $REPO_URL"
echo "║  Actions    : $REPO_URL/actions"
echo "║  Secrets    : $REPO_URL/settings/secrets/actions"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "  Next: Add your secrets, then trigger a manual run:"
echo "  $REPO_URL/actions → 'Run workflow' → mode: monitor"
echo ""
