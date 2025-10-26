# 📞 Alert Call System - Setup Guide

Automatic phone calls to nurses when critical alerts are triggered.

---

## 🏗️ Architecture

```
┌──────────────┐
│   Database   │
│    Alerts    │ (INSERT critical alert)
└──────┬───────┘
       │ PostgreSQL Trigger
       ↓
┌──────────────┐
│ Edge Function│ (Supabase Deno runtime)
│alert-call-   │
│    nurse     │
└──────┬───────┘
       │ LiveKit SIP API
       ↓
┌──────────────┐
│   LiveKit    │ (SIP → PSTN Gateway)
│   Cloud      │
└──────┬───────┘
       │ Phone Network
       ↓
┌──────────────┐
│ Nurse Phone  │ 📞 +1-385-401-9951
└──────────────┘
```

**Flow:**
1. **Critical alert created** → `INSERT INTO alerts` with `severity='critical'`
2. **Trigger fires** → `on_critical_alert_created` invokes edge function
3. **Edge function runs** → Fetches patient/room data, builds message
4. **LiveKit SIP call** → Makes outbound call to nurse's phone
5. **AI agent speaks** → Text-to-speech delivers alert message
6. **Call logged** → Result stored in `alert_calls` table

---

## 📋 Prerequisites

### 1. Supabase Project
- [ ] Create project at [supabase.com](https://supabase.com)
- [ ] Enable Edge Functions
- [ ] Get Project URL and Service Role Key

### 2. LiveKit Account
- [ ] Sign up at [livekit.io](https://livekit.io)
- [ ] Create a new project
- [ ] Enable **SIP** feature (required for outbound calls)
- [ ] Get API Key and Secret
- [ ] Configure SIP Trunk (see below)

### 3. Phone Number (via LiveKit SIP or Twilio)
- [ ] LiveKit SIP Trunk configured
- [ ] Test number: `+13854019951` (currently used in app)

---

## 🚀 Step-by-Step Setup

### **Step 1: Install Supabase CLI**

```bash
# macOS
brew install supabase/tap/supabase

# Or via npm
npm install -g supabase

# Verify installation
supabase --version
```

### **Step 2: Initialize Supabase**

```bash
cd /Users/julianng-thow-hing/Desktop/haven

# Link to your Supabase project
supabase link --project-ref YOUR_PROJECT_REF

# Login to Supabase
supabase login
```

### **Step 3: Configure LiveKit SIP**

1. **Go to LiveKit Cloud Dashboard**
   - Navigate to: https://cloud.livekit.io/projects/YOUR_PROJECT/settings
   
2. **Create SIP Trunk**
   - Click "SIP" tab → "Add SIP Trunk"
   - **Inbound:** Not needed (we're making outbound calls)
   - **Outbound:** Configure with your SIP provider
     - Option A: LiveKit's managed SIP (easiest)
     - Option B: Bring your own (Twilio, Vonage, etc.)
   
3. **Get SIP Trunk ID**
   - Copy the Trunk ID (starts with `ST_`)
   - Example: `ST_xxxxxxxxxxxxxxxxxxx`

4. **Get API Credentials**
   - API Key: `APIxxxxxxxxxxxxxxx`
   - API Secret: `<long-secret-string>`

### **Step 4: Set Edge Function Secrets**

```bash
cd /Users/julianng-thow-hing/Desktop/haven

# Set LiveKit credentials
supabase secrets set LIVEKIT_API_URL=https://haven-livekit.livekit.cloud
supabase secrets set LIVEKIT_API_KEY=APIxxxxxxxxxxxxxxx
supabase secrets set LIVEKIT_API_SECRET=your-long-secret-string
supabase secrets set LIVEKIT_SIP_TRUNK_ID=ST_xxxxxxxxxxxxxxxxxxx

# Set nurse phone number
supabase secrets set NURSE_PHONE_NUMBER=+13854019951

# Verify secrets
supabase secrets list
```

### **Step 5: Deploy Edge Function**

```bash
cd /Users/julianng-thow-hing/Desktop/haven

# Deploy the edge function
supabase functions deploy alert-call-nurse

# Verify deployment
supabase functions list
```

Expected output:
```
┌──────────────────┬──────────┬─────────────────────┐
│ Name             │ Status   │ Updated             │
├──────────────────┼──────────┼─────────────────────┤
│ alert-call-nurse │ deployed │ 2025-01-XX XX:XX:XX │
└──────────────────┴──────────┴─────────────────────┘
```

### **Step 6: Run Database Migration**

```bash
cd /Users/julianng-thow-hing/Desktop/haven

# Apply migration
supabase db push

# Or manually run the SQL file in Supabase Dashboard:
# 1. Go to SQL Editor
# 2. Copy contents of supabase/migrations/003_alert_call_system.sql
# 3. Execute
```

This creates:
- ✅ `alert_calls` table for logging calls
- ✅ `notify_critical_alert()` function
- ✅ `on_critical_alert_created` trigger

### **Step 7: Configure Database Trigger**

The trigger needs the edge function URL. Set it in Supabase:

```sql
-- Run this in Supabase SQL Editor
-- Replace YOUR_PROJECT_REF with your actual project reference

ALTER DATABASE postgres SET app.edge_function_url = 
  'https://YOUR_PROJECT_REF.supabase.co/functions/v1/alert-call-nurse';

ALTER DATABASE postgres SET app.supabase_service_key = 
  'YOUR_SERVICE_ROLE_KEY';
```

Or use environment variable in the trigger (already configured).

---

## 🧪 Testing

### **Test 1: Manual Edge Function Invocation**

```bash
# Test edge function locally
supabase functions serve alert-call-nurse

# In another terminal, test with curl
curl -X POST http://localhost:54321/functions/v1/alert-call-nurse \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -d '{
    "type": "INSERT",
    "table": "alerts",
    "record": {
      "alert_id": "test-123",
      "patient_id": "P-DHE-001",
      "room_id": "room-uuid",
      "severity": "critical",
      "message": "Test critical alert",
      "status": "active"
    }
  }'
```

Expected response:
```json
{
  "message": "Call initiated successfully",
  "alert_id": "test-123",
  "call_id": "alert-test-123",
  "to": "+13854019951"
}
```

### **Test 2: End-to-End via Database Insert**

```sql
-- Insert a critical alert in Supabase SQL Editor
INSERT INTO alerts (
  patient_id,
  room_id,
  severity,
  status,
  alert_type,
  message
) VALUES (
  'P-DHE-001',
  (SELECT room_id FROM rooms WHERE room_name = 'Room 2' LIMIT 1),
  'critical',
  'active',
  'seizure_detected',
  'Seizure activity detected - immediate response required'
);

-- Check if call was logged
SELECT * FROM alert_calls ORDER BY created_at DESC LIMIT 1;
```

Expected result in `alert_calls`:
```
alert_id      | phone_number    | call_status | message
--------------+-----------------+-------------+---------
<uuid>        | +13854019951    | initiated   | Critical alert at...
```

### **Test 3: Check Edge Function Logs**

```bash
# View real-time logs
supabase functions logs alert-call-nurse --follow

# Should see:
# 📨 Webhook received: INSERT alerts
# 🚨 CRITICAL ALERT: <alert_id>
# 📞 Calling nurse at +13854019951
# ✅ Call initiated: <call_id>
```

---

## 🔍 Monitoring & Debugging

### **View Call History**

```sql
-- Dashboard query: Recent alert calls
SELECT 
  ac.created_at,
  a.severity,
  a.message as alert_message,
  p.name as patient_name,
  r.room_name,
  ac.call_status,
  ac.phone_number,
  ac.duration_seconds
FROM alert_calls ac
JOIN alerts a ON ac.alert_id = a.alert_id
LEFT JOIN patients p ON a.patient_id = p.patient_id
LEFT JOIN rooms r ON a.room_id = r.room_id
ORDER BY ac.created_at DESC
LIMIT 20;
```

### **Check Edge Function Health**

```bash
# Test edge function is responsive
curl https://YOUR_PROJECT.supabase.co/functions/v1/alert-call-nurse/health

# Check deployment status
supabase functions list
```

### **Common Issues**

#### **1. "LiveKit not configured"**
- **Symptom:** Logs show "would call nurse in production"
- **Fix:** Set secrets (Step 4)
  ```bash
  supabase secrets list  # Verify secrets are set
  ```

#### **2. "Function not found"**
- **Symptom:** Trigger fires but no call happens
- **Fix:** Deploy edge function (Step 5)
  ```bash
  supabase functions deploy alert-call-nurse
  ```

#### **3. "SIP call failed"**
- **Symptom:** Call initiated but fails to connect
- **Fix:** Check LiveKit SIP trunk configuration
  - Ensure SIP trunk is active
  - Verify phone number format (`+1` prefix)
  - Check LiveKit dashboard for SIP errors

#### **4. Trigger not firing**
- **Symptom:** No logs when alert inserted
- **Fix:** Check trigger exists
  ```sql
  SELECT * FROM pg_trigger WHERE tgname = 'on_critical_alert_created';
  ```

---

## 📊 Frontend Integration

The UI already shows alert calls in the dashboard. To display call status:

```tsx
// Example: Alert panel with call status
<div className="alert-card">
  <div className="alert-header">
    {alert.severity === 'critical' && (
      <span className="badge badge-critical">
        📞 Nurse Called
      </span>
    )}
  </div>
  
  {alertCall && (
    <div className="call-status">
      <p>Called: {alertCall.phone_number}</p>
      <p>Status: {alertCall.call_status}</p>
      {alertCall.answered_at && (
        <p>Answered: {formatTime(alertCall.answered_at)}</p>
      )}
    </div>
  )}
</div>
```

---

## 💰 Cost Estimate

### **LiveKit SIP Pricing** (as of 2025)
- **Outbound calls:** ~$0.01/min (US domestic)
- **Critical alerts:** Assume 2/day × 2 min avg = 4 min/day
- **Monthly cost:** 4 min/day × 30 days × $0.01 = **$1.20/month**

### **Supabase Edge Functions**
- **Free tier:** 500K invocations/month
- **Critical alerts:** ~60/month
- **Cost:** **$0** (well within free tier)

**Total: ~$1-2/month for production alert calling system**

---

## 🎯 Next Steps

### **Phase 1: MVP (Current)**
- ✅ Edge function created
- ✅ Database trigger configured
- ✅ Call to single nurse number

### **Phase 2: Enhancements**
- [ ] **Multiple nurses:** Rotate on-call staff
- [ ] **Escalation:** If no answer in 30s, call backup
- [ ] **Two-way interaction:** Nurse can acknowledge via phone keypad
- [ ] **Call recording:** Store audio for compliance
- [ ] **SMS fallback:** If call fails, send SMS

### **Phase 3: Advanced**
- [ ] **AI conversation:** LiveKit agent can answer nurse questions
- [ ] **Video conferencing:** Nurse can join room video call
- [ ] **Shift scheduling:** Auto-detect on-call nurse per shift
- [ ] **Analytics dashboard:** Call answer rates, response times

---

## 📚 Resources

- **LiveKit SIP Docs:** https://docs.livekit.io/home/server/sip/
- **Supabase Edge Functions:** https://supabase.com/docs/guides/functions
- **Database Triggers:** https://supabase.com/docs/guides/database/postgres/triggers

---

## 🆘 Support

If you encounter issues:

1. **Check logs:**
   ```bash
   supabase functions logs alert-call-nurse --follow
   ```

2. **Verify secrets:**
   ```bash
   supabase secrets list
   ```

3. **Test locally:**
   ```bash
   supabase functions serve alert-call-nurse
   ```

4. **Check database:**
   ```sql
   SELECT * FROM alert_calls ORDER BY created_at DESC LIMIT 10;
   ```

---

## ✅ Production Checklist

Before going live:

- [ ] LiveKit SIP trunk configured and tested
- [ ] Edge function deployed to production
- [ ] Database migration applied
- [ ] Secrets configured in production
- [ ] Test call successfully made and received
- [ ] Nurse phone number confirmed: `+13854019951`
- [ ] Monitoring dashboard set up
- [ ] Alert call logs accessible to staff
- [ ] Backup escalation plan documented
- [ ] Cost monitoring enabled

**Your alert call system is ready for production!** 🚀

