# Quick Start: Handoff Form Generator

Get the Fetch.ai handoff form generator running in 5 minutes!

## Prerequisites

- Python 3.10+
- Supabase account with Haven database
- SMTP email account (Gmail recommended for testing)
- Anthropic API key (optional, but highly recommended)

## 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## 2. Create Database Table

Run this SQL in your Supabase SQL Editor:

```sql
-- Run the handoff_forms schema
-- File: database/handoff_forms_schema.sql
```

Or use the provided file:
```bash
psql $DATABASE_URL < database/handoff_forms_schema.sql
```

## 3. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

**Minimal Configuration (for testing):**

```env
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# AI (optional but recommended)
ANTHROPIC_API_KEY=sk-ant-...

# Email (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SENDER_EMAIL=your-email@gmail.com
SENDER_NAME=Haven Health

# Nurses to notify
NURSE_EMAILS=nurse@example.com,doctor@example.com
```

### Gmail Setup (Quick)

1. Go to [Google Account → Security](https://myaccount.google.com/security)
2. Enable 2-Factor Authentication
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Create new app password for "Mail"
5. Copy 16-character password to `SMTP_PASSWORD`

## 4. Test Email Connection

```bash
python -c "from app.services.email_service import email_service; print(email_service.test_connection())"
```

Should output: `{'success': True, 'message': 'SMTP connection successful'}`

## 5. Start the Server

```bash
uvicorn app.main:app --reload
```

**You should see:**
```
✅ Fetch.ai Handoff Agent initialized: agent1q...
📧 Default nurse emails: ['nurse@example.com']
🏥 Haven Backend Services:
   • Fetch.ai Handoff Agent: ✅ Enabled
```

## 6. Test Manual Form Generation

### Option A: Using cURL

```bash
curl -X POST http://localhost:8000/handoff-agent/generate \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "P-DAV-001",
    "recipient_emails": ["your-test-email@gmail.com"]
  }'
```

### Option B: Using the API Docs

1. Open http://localhost:8000/docs
2. Find `POST /handoff-agent/generate`
3. Click "Try it out"
4. Enter:
   ```json
   {
     "patient_id": "P-DAV-001"
   }
   ```
5. Click "Execute"

### Expected Response:

```json
{
  "success": true,
  "form_id": "uuid-here",
  "form_number": "HO-20251026143022",
  "pdf_path": "/tmp/handoff_forms/HO-20251026143022.pdf",
  "alerts_processed": 1,
  "email_sent": true,
  "message": "Successfully generated handoff form HO-20251026143022"
}
```

**Check your email!** You should receive:
- Subject: `[CRITICAL] Patient Handoff Form HO-... - Patient Name`
- PDF attachment with full handoff form

## 7. View Generated Forms

### List all forms:
```bash
curl http://localhost:8000/handoff-agent/forms
```

### Get specific form:
```bash
curl http://localhost:8000/handoff-agent/forms/{form_id}
```

### Download PDF:
```bash
curl http://localhost:8000/handoff-agent/forms/{form_id}/pdf --output handoff.pdf
```

## 8. Check Agent Status

```bash
curl http://localhost:8000/handoff-agent/status
```

**Response:**
```json
{
  "enabled": true,
  "agent_address": "agent1q...",
  "processed_alerts": 0,
  "generated_forms": 1,
  "nurse_emails": ["nurse@example.com"],
  "check_interval_seconds": 300
}
```

## Automatic Monitoring

The agent automatically:
- **Checks every 5 minutes** for new alerts
- **Groups by patient** to create one form per patient
- **Generates PDFs** with all alert details
- **Emails nurses** immediately
- **Tracks delivery** status in database

### View Automatic Activity:

Watch the logs while alerts are created:

```bash
# Terminal 1: Run server with verbose logging
uvicorn app.main:app --reload --log-level debug

# Terminal 2: Create a test alert
curl -X POST http://localhost:8000/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type": "vital_sign",
    "severity": "critical",
    "title": "Test Alert",
    "description": "Testing handoff generation",
    "patient_id": "P-DAV-001"
  }'
```

Within 5 minutes, you should see:
```
🔄 Checking for alerts requiring handoff...
📋 Found 1 alert for 1 patient
📝 Generating handoff form for patient P-DAV-001 (1 alert)
📄 Generated PDF: /tmp/handoff_forms/HO-...pdf
📧 Email sent to 1 recipient
✅ Successfully generated form HO-...
```

## Troubleshooting

### "SMTP authentication error"

**Problem:** Wrong email credentials

**Solution:**
- If using Gmail: Create an [App Password](https://myaccount.google.com/apppasswords)
- Don't use your regular Gmail password
- Enable 2FA first

### "No alerts found"

**Problem:** No active alerts in database

**Solution:**
```bash
# Create test alert
curl -X POST http://localhost:8000/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type": "vital_sign",
    "severity": "high",
    "title": "Blood Pressure Elevated",
    "patient_id": "P-DAV-001",
    "description": "BP: 160/95 mmHg"
  }'
```

### "PDF generation failed"

**Problem:** Missing reportlab or file permissions

**Solution:**
```bash
# Install reportlab
pip install reportlab

# Create output directory
mkdir -p /tmp/handoff_forms
chmod 777 /tmp/handoff_forms
```

### "Email sent but not received"

**Problem:** Spam filter or wrong recipient

**Solution:**
- Check spam/junk folder
- Verify `NURSE_EMAILS` in .env
- Test with your personal email first

## Next Steps

1. **Customize PDF**: Edit `app/services/pdf_generator.py`
2. **Customize Email**: Edit `app/services/email_service.py`
3. **Change Frequency**: Edit `fetch_handoff_agent.py` check_interval
4. **Add More Recipients**: Update `NURSE_EMAILS` in .env
5. **Deploy to Production**: See `HANDOFF_AGENT_README.md`

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/handoff-agent/status` | GET | Agent health check |
| `/handoff-agent/generate` | POST | Manual form generation |
| `/handoff-agent/forms` | GET | List all forms |
| `/handoff-agent/forms/{id}` | GET | Get specific form |
| `/handoff-agent/forms/{id}/pdf` | GET | Download PDF |

## Support

- Full documentation: `HANDOFF_AGENT_README.md`
- API docs: http://localhost:8000/docs
- Logs: Check terminal output

---

**You're all set! 🎉**

Your Fetch.ai handoff agent is now monitoring alerts and will automatically generate and email handoff forms to your nursing staff.
