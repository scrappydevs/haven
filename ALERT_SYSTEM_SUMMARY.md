# Alert System Summary

## Overview
The Haven system now automatically creates alerts in Supabase when the Fetch.ai CV monitoring agent detects health concerns.

## How It Works

### 1. Computer Vision Detection
The Fetch.ai Health Agent continuously monitors video streams and analyzes:
- **Movement events**: Falls, seizures, extreme agitation
- **Vital signs**: Heart rate, respiratory rate
- **Behavior**: Movement patterns, posture

### 2. Alert Triggering
When the agent detects concerning events with severity **CRITICAL** or **WARNING**, it:
1. Analyzes the event using AI (local fallback or Agentverse)
2. Determines severity level
3. **Automatically inserts an alert into Supabase `alerts` table**
4. Logs the event for the nursing dashboard

### 3. Alert Details

Each alert includes:
- **alert_type**: Mapped from movement event
  - `fall` → `fall_risk`
  - `seizure` → `vital_sign`
  - `extreme_agitation` → `other`
  - Vital sign issues → `vital_sign`

- **severity**: Mapped from agent analysis
  - `CRITICAL` → `critical`
  - `WARNING` → `high`

- **title**: Human-readable event name
  - "Fall Detected"
  - "Seizure Activity Detected"
  - "Elevated Heart Rate"
  - etc.

- **description**: Combines concerns and AI reasoning

- **metadata**: Full context including:
  - CV metrics (movement confidence, event type)
  - Vitals (heart rate, respiratory rate)
  - AI concerns list
  - Recommended actions
  - Agent confidence score

- **patient_id**: The monitored patient
- **room_id**: Auto-fetched from patient record
- **triggered_by**: "FETCH_AI_AGENT"
- **status**: "active" (ready for nurse acknowledgment)

## Dashboard Integration

### Active Alerts List
- Alerts appear immediately in the dashboard "Active Alerts" section
- Auto-refreshes every 5 seconds
- Color-coded by severity (red=critical, orange/yellow=high/medium)

### Alert Modal
When clicked:
- Shows full alert details
- Allows downloading PDF handoff form
- Allows acknowledging the alert (changes status to 'acknowledged')

### Handoff Forms
- PDFs generated on-demand when nurse clicks "Download PDF"
- Includes all alert context, patient info, and AI recommendations
- Form reference saved back to alert record

## Code Locations

### Backend
- **`backend/app/fetch_health_agent.py`**
  - `analyze_patient()` - Main analysis function (line 75)
  - `_insert_alert_to_supabase()` - Alert insertion logic (line 295)
  - Called every time CV detects concerning events

- **`backend/app/websocket.py`**
  - Line 332-345: Fetches room_id and calls analyze_patient()
  - Runs in background thread to never block video streaming

- **`backend/app/main.py`**
  - Line 712: `GET /alerts/{alert_id}` - Fetch single alert
  - Line 2848: `POST /alerts/{alert_id}/acknowledge` - Acknowledge alerts

### Frontend
- **`frontend/components/HandoffFormsList.tsx`**
  - Displays active alerts
  - Refreshes every 5 seconds
  - Opens modal on click

- **`frontend/components/HandoffFormModal.tsx`**
  - Shows alert details
  - PDF download functionality
  - Acknowledge button

## Testing

### Mock Data
Use `backend/migrations/mock_alerts_data.sql` to insert test alerts:
```sql
-- See 12 test alerts for patient P-DHE-001
-- Includes various severity levels and types
```

### Live Testing
1. Start video stream with patient monitoring
2. Simulate concerning events (rapid movement, unusual posture)
3. Watch terminal for agent analysis logs
4. Check dashboard for new alerts appearing
5. Click alert to view details and test acknowledgment

## Event Flow

```
CV Detection → Fetch.ai Agent Analysis → Alert Creation → Dashboard Display
     ↓                    ↓                    ↓                  ↓
Movement event    Severity: CRITICAL    Insert to DB      Nurse sees alert
(e.g., fall)      Concerns: [...]       Status: active    Can acknowledge
                  Confidence: 0.85                        Can download PDF
```

## Alert Throttling

To prevent alert spam:
- **Normal monitoring**: Max 1 Agentverse call per 30 seconds per patient
- **Emergency events**: Max 1 call per 15 seconds per patient
- **Voice calls**: Max 1 emergency call per 60 seconds per patient

Throttled events use fast local fallback analysis.

## Future Enhancements

Potential improvements:
- [ ] Alert escalation if not acknowledged within X minutes
- [ ] Group related alerts (same patient, similar timeframe)
- [ ] Alert analytics and trending
- [ ] Nurse assignment and routing
- [ ] Mobile push notifications
- [ ] Integration with hospital paging systems
