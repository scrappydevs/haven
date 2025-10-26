# Haven Handoff Form Generator - Fetch.ai Agent

This document describes the Fetch.ai agent that automatically monitors the `alerts` table, generates professional handoff forms summarizing patient information, and emails them to healthcare staff.

## Overview

The **Fetch.ai Handoff Agent** is an autonomous agent that:

1. **Monitors** the `alerts` table in Supabase every 5 minutes
2. **Queries** all active/unhandled alerts for each patient
3. **Generates** AI-powered handoff forms with:
   - Patient demographics and clinical information
   - Alert summaries and severity assessments
   - Clinical context (vitals, medications, history)
   - Recommended actions and protocols
   - Complete alert timeline
4. **Creates** professional PDF documents
5. **Stores** forms in the `handoff_forms` database table
6. **Emails** PDFs to configured nurse email addresses
7. **Tracks** email delivery status

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Fetch.ai Handoff Agent                       │
│                  (fetch_handoff_agent.py)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Periodic Check (every 5 min)                                │
│     ↓                                                            │
│  2. Query Alerts Service → Supabase alerts table                │
│     ↓                                                            │
│  3. Group alerts by patient                                     │
│     ↓                                                            │
│  4. Generate Form Content:                                      │
│     • Fetch patient demographics                                │
│     • Query recent vitals from alert metadata                   │
│     • Use Claude AI to generate clinical summary                │
│     • Create recommended actions                                │
│     ↓                                                            │
│  5. Generate PDF (reportlab)                                    │
│     ↓                                                            │
│  6. Save to handoff_forms table                                 │
│     ↓                                                            │
│  7. Email PDF to nurses (SMTP)                                  │
│     ↓                                                            │
│  8. Update delivery status                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## File Structure

```
backend/
├── app/
│   ├── fetch_handoff_agent.py          # Main Fetch.ai agent
│   ├── models/
│   │   └── handoff_forms.py            # Pydantic data models
│   ├── services/
│   │   ├── alerts_service.py           # Alert querying service
│   │   ├── pdf_generator.py            # PDF generation utility
│   │   └── email_service.py            # Email/SMTP service
│   └── main.py                         # FastAPI integration
├── database/
│   └── handoff_forms_schema.sql        # Database schema
├── .env.example                        # Environment variables template
└── HANDOFF_AGENT_README.md            # This file
```

## Database Schema

The agent uses a new `handoff_forms` table:

```sql
CREATE TABLE handoff_forms (
  id UUID PRIMARY KEY,
  form_number TEXT UNIQUE,          -- e.g., "HO-2025-0001"
  patient_id TEXT REFERENCES patients(patient_id),
  alert_ids JSONB,                  -- Array of alert UUIDs
  content JSONB,                    -- Full form content
  pdf_path TEXT,                    -- Local path to PDF
  pdf_url TEXT,                     -- Optional cloud storage URL
  status TEXT,                      -- generated, sent, acknowledged
  emailed_to JSONB,                 -- Array of recipient emails
  email_sent_at TIMESTAMP,
  email_delivery_status TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Required packages:
- `uagents` - Fetch.ai agent framework
- `anthropic` - Claude AI for intelligent summaries
- `reportlab` - PDF generation
- `supabase` - Database client
- `smtplib` - Email (built-in Python)

### 2. Create Database Table

Run the SQL schema to create the `handoff_forms` table:

```bash
# Apply schema to your Supabase database
psql $DATABASE_URL < database/handoff_forms_schema.sql
```

Or execute via Supabase dashboard SQL editor.

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Required variables:**

```env
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# AI (for intelligent summaries)
ANTHROPIC_API_KEY=sk-ant-...

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SENDER_EMAIL=noreply@haven-health.com
SENDER_NAME=Haven Health System

# Nurse email addresses (comma-separated)
NURSE_EMAILS=nurse1@hospital.com,nurse2@hospital.com

# Agent Configuration
HANDOFF_AGENT_SEED=your_unique_seed_phrase
```

### 4. Configure SMTP Email

#### Option A: Gmail SMTP

1. Enable 2-Factor Authentication on your Google account
2. Generate an [App Password](https://myaccount.google.com/apppasswords)
3. Use credentials:
   - `SMTP_SERVER=smtp.gmail.com`
   - `SMTP_PORT=587`
   - `SMTP_USERNAME=your-email@gmail.com`
   - `SMTP_PASSWORD=your-16-char-app-password`

#### Option B: SendGrid SMTP

1. Sign up for [SendGrid](https://sendgrid.com)
2. Create an API Key
3. Use credentials:
   - `SMTP_SERVER=smtp.sendgrid.net`
   - `SMTP_PORT=587`
   - `SMTP_USERNAME=apikey`
   - `SMTP_PASSWORD=your-sendgrid-api-key`

#### Option C: Custom SMTP Server

Configure your organization's SMTP server details.

### 5. Test Email Configuration

```bash
python -c "from app.services.email_service import email_service; print(email_service.test_connection())"
```

Should return `{'success': True, 'message': 'SMTP connection successful'}`

### 6. Run the Agent

The agent runs automatically when the FastAPI server starts:

```bash
uvicorn app.main:app --reload
```

The agent will:
- Start on server startup
- Check for new alerts every 5 minutes
- Generate and email handoff forms automatically

## API Endpoints

### Agent Status

```bash
GET /handoff-agent/status
```

Returns agent health, processed alerts count, and configuration.

**Response:**
```json
{
  "enabled": true,
  "agent_address": "agent1q...",
  "processed_alerts": 15,
  "generated_forms": 8,
  "nurse_emails": ["nurse@hospital.com"],
  "check_interval_seconds": 300
}
```

### Manual Form Generation

```bash
POST /handoff-agent/generate
```

**Request Body:**
```json
{
  "patient_id": "P-DAV-001",
  "recipient_emails": ["nurse@hospital.com", "doctor@hospital.com"]
}
```

**Response:**
```json
{
  "success": true,
  "form_id": "uuid",
  "form_number": "HO-2025-0001",
  "pdf_path": "/tmp/handoff_forms/HO-2025-0001.pdf",
  "alerts_processed": 3,
  "email_sent": true,
  "message": "Successfully generated handoff form HO-2025-0001"
}
```

### Get Generated Forms

```bash
GET /handoff-agent/forms?patient_id=P-DAV-001&limit=10
```

**Response:**
```json
{
  "forms": [
    {
      "id": "uuid",
      "form_number": "HO-2025-0001",
      "patient_id": "P-DAV-001",
      "status": "sent",
      "created_at": "2025-10-26T02:30:00Z",
      "emailed_to": ["nurse@hospital.com"],
      "alert_ids": ["alert-uuid-1", "alert-uuid-2"]
    }
  ],
  "count": 1
}
```

### Download PDF

```bash
GET /handoff-agent/forms/{form_id}/pdf
```

Downloads the PDF file for a specific form.

## Form Content

Each generated handoff form includes:

### 1. **Header**
- Form number (HO-YYYY-NNNN)
- Generation timestamp
- Severity level with color coding
- Intended recipient (Nurse/Doctor)

### 2. **Patient Information**
- Patient ID and name
- Age, gender, room number
- Diagnosis and treatment status
- **Allergies** (highlighted in red)
- Current medications

### 3. **Alert Summary**
- Primary concern (highlighted)
- Detailed AI-generated summary
- Severity assessment

### 4. **Clinical Context**
- Recent vital signs from alert metadata
- Current treatments
- Relevant medical history

### 5. **Recommended Actions**
- Numbered action items
- Urgency notes (if critical)
- Protocols to follow

### 6. **Related Alerts**
- All alerts included in handoff
- Alert type, severity, and time
- Brief descriptions

### 7. **Event Timeline**
- Chronological sequence of events
- Timestamps for each alert trigger

### 8. **Footer**
- Special instructions
- Contact information (Emergency x5555, etc.)
- Generation metadata

## Claude AI Integration

The agent uses Claude (Anthropic) for intelligent summaries:

### Without Claude:
- Basic rule-based summaries
- Simple alert aggregation
- Generic recommendations

### With Claude (Recommended):
- **Clinical Analysis**: Understands medical context
- **Intelligent Summarization**: Synthesizes multiple alerts
- **Risk Assessment**: Identifies concerning patterns
- **Actionable Recommendations**: Protocol-specific guidance
- **Natural Language**: Professional clinical language

**Example Prompt:**
```
You are a clinical decision support AI generating a handoff form.

PATIENT: P-DAV-001, Age 52, Multiple Myeloma
ALERTS:
- [CRITICAL] Blood Pressure 185/120 mmHg
- [HIGH] CRS Grade 2 symptoms
- [MEDIUM] Patient reported nausea

Generate:
1. Clinical summary (2-3 sentences)
2. Primary concern (1 sentence)
3. Recommended actions (3-5 items)
4. Urgency assessment
```

Claude responds with structured JSON for the form generator.

## Email Template

Nurses receive HTML emails with:

- **Subject**: `[CRITICAL] Patient Handoff Form HO-2025-0001 - John Doe`
- **Body**:
  - Patient demographics
  - Severity badge
  - Brief summary
  - PDF attachment notice
  - HIPAA confidentiality notice

## Monitoring & Logging

The agent logs all activities:

```
✅ Fetch.ai Handoff Agent initialized: agent1q...
📧 Default nurse emails: ['nurse@hospital.com']
🔄 Checking for alerts requiring handoff...
📋 Found 3 alerts for 1 patient
📝 Generating handoff form for patient P-DAV-001 (3 alerts)
📄 Generated PDF: /tmp/handoff_forms/HO-2025-0001.pdf
💾 Saved form to database: form-uuid
📧 Email sent to 2 recipients
✅ Successfully generated form HO-2025-0001
```

## Customization

### Change Check Interval

In `fetch_handoff_agent.py`:

```python
fetch_handoff_agent = FetchHandoffAgent(
    check_interval_seconds=180  # Check every 3 minutes
)
```

### Customize Form Generation Logic

Edit `_generate_handoff_form()` method to:
- Change alert filtering criteria
- Modify form content structure
- Add custom business logic

### Customize PDF Styling

Edit `backend/app/services/pdf_generator.py`:
- Colors, fonts, layout
- Header/footer content
- Section ordering

### Customize Email Template

Edit `backend/app/services/email_service.py`:
- Email subject format
- HTML template
- Attachment handling

## Troubleshooting

### Agent Not Running

**Check:**
1. Is FastAPI server running?
2. Are environment variables set?
3. Check logs for errors

**Solution:**
```bash
# Restart server with verbose logging
uvicorn app.main:app --reload --log-level debug
```

### No Forms Generated

**Check:**
1. Are there active alerts in the database?
2. Is Supabase connection working?

**Solution:**
```bash
# Manually trigger form generation
curl -X POST http://localhost:8000/handoff-agent/generate \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "P-DAV-001"}'
```

### Emails Not Sending

**Check:**
1. SMTP credentials correct?
2. Test connection:
   ```python
   from app.services.email_service import email_service
   print(email_service.test_connection())
   ```
3. Check firewall/port 587 open
4. Gmail: Use App Password, not regular password

**Solution:**
- Enable "Less secure app access" if using Gmail (or use App Password)
- Check spam folder
- Verify recipient email addresses

### PDF Generation Fails

**Check:**
1. Is `reportlab` installed?
   ```bash
   pip install reportlab
   ```
2. Is output directory writable?
   ```bash
   mkdir -p /tmp/handoff_forms
   chmod 777 /tmp/handoff_forms
   ```

## Production Deployment

### 1. Use Cloud Storage for PDFs

Instead of local storage, upload to S3/GCS:

```python
# In fetch_handoff_agent.py
pdf_url = upload_to_s3(pdf_path)
# Save pdf_url to database
```

### 2. Use Job Queue

For high-volume environments, use Celery/Redis:

```python
@celery.task
def generate_handoff_form_async(patient_id):
    # Generate form in background
    pass
```

### 3. Enable Monitoring

- Use Sentry for error tracking
- Enable Prometheus metrics
- Set up email delivery webhooks

### 4. HIPAA Compliance

- Encrypt PDFs before storage
- Use TLS for email (already enabled)
- Audit all form accesses
- Implement retention policies

## Advanced Features

### Future Enhancements

1. **Multi-language Support**: Generate forms in patient's preferred language
2. **Voice Notifications**: Text-to-speech alerts via phone
3. **Mobile App Integration**: Push notifications to staff devices
4. **Smart Routing**: Route forms based on alert type/specialty
5. **Automated Acknowledgment**: Track when staff review forms
6. **Analytics Dashboard**: Form generation metrics and trends

## Support

For issues or questions:
1. Check logs: `tail -f logs/handoff_agent.log`
2. Review environment variables
3. Test individual components (email, PDF, database)
4. Open GitHub issue with error details

---

**Generated with Claude Code**
