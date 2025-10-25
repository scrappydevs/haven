# Haven Hospital - Database Schema Documentation

**Last Updated:** October 25, 2025  
**Database:** PostgreSQL (Supabase)  
**Version:** 1.0

---

## 📊 Table of Contents

1. [Core Tables](#core-tables)
2. [Clinical Data Tables](#clinical-data-tables)
3. [Management Tables](#management-tables)
4. [AI & Communication Tables](#ai--communication-tables)
5. [Indexes & Performance](#indexes--performance)
6. [Sample Queries](#sample-queries)

---

## 🏥 Core Tables

### `patients`
**Purpose:** Primary patient demographic and enrollment data

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key (auto-generated) |
| `patient_id` | TEXT | Unique patient identifier (e.g., 'P-DHE-001') |
| `name` | TEXT | Full patient name |
| `age` | INTEGER | Current age |
| `gender` | TEXT | Gender |
| `date_of_birth` | DATE | Date of birth |
| `photo_url` | TEXT | Supabase Storage URL to patient photo |
| `condition` | TEXT | Primary diagnosis/admission reason |
| `enrollment_date` | DATE | Admission/enrollment date |
| `enrollment_status` | TEXT | Status: 'active', 'discharged', 'transferred' |
| `ecog_status` | INTEGER | ECOG Performance Status (0-4) |
| `prior_treatment_lines` | INTEGER | Number of previous treatments |
| `infusion_count` | INTEGER | Number of infusions received |
| `baseline_vitals` | JSONB | JSON object with baseline vital signs |
| `baseline_crs_risk` | NUMERIC | Baseline risk score (0-1) |
| `notes` | TEXT | Clinical notes |
| `created_at` | TIMESTAMPTZ | Record creation timestamp |
| `updated_at` | TIMESTAMPTZ | Last update timestamp |

**Sample baseline_vitals JSONB:**
```json
{
  "heart_rate": 72,
  "respiratory_rate": 16,
  "temperature": 36.8,
  "oxygen_saturation": 98,
  "blood_pressure": "118/76",
  "blood_pressure_systolic": 118,
  "blood_pressure_diastolic": 76,
  "weight_kg": 75,
  "height_cm": 178,
  "bmi": 23.7
}
```

**Foreign Keys:** None (root table)  
**Indexes:** `patient_id` (unique), `enrollment_status`, `created_at`

---

### `rooms`
**Purpose:** Physical room/bed definitions

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `room_id` | TEXT | Unique room identifier (UUID or name) |
| `room_name` | TEXT | Display name (e.g., 'Room 1') |
| `room_type` | TEXT | Type: patient, nurse_station, icu, surgery, lab |
| `floor_id` | TEXT | Foreign key to floors table |
| `capacity` | INTEGER | Bed capacity (default: 1) |
| `metadata` | JSONB | Smplrspace polygon data, equipment list |
| `created_at` | TIMESTAMPTZ | Created timestamp |
| `updated_at` | TIMESTAMPTZ | Updated timestamp |

**Foreign Keys:** `floor_id` → `floors.floor_id`  
**Indexes:** `room_id` (unique), `room_type`, `floor_id`

---

### `floors`
**Purpose:** Hospital floor/level definitions

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `floor_id` | TEXT | Unique floor identifier |
| `name` | TEXT | Floor name |
| `smplr_space_id` | TEXT | Smplrspace space ID for 3D mapping |
| `level_index` | INTEGER | Floor level (0 = ground, 1 = first, etc.) |
| `building` | TEXT | Building name/identifier |
| `description` | TEXT | Floor description |
| `metadata` | JSONB | Additional floor data |
| `created_at` | TIMESTAMPTZ | Created timestamp |
| `updated_at` | TIMESTAMPTZ | Updated timestamp |

**Foreign Keys:** None  
**Indexes:** `floor_id` (unique)

---

## 🏨 Management Tables

### `patients_room`
**Purpose:** Patient-to-room assignments (junction table)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `room_id` | TEXT | Room assignment |
| `patient_id` | TEXT | Patient assignment |
| `assigned_at` | TIMESTAMPTZ | Assignment timestamp |
| `assigned_by` | TEXT | Who made assignment (user/system) |
| `notes` | TEXT | Assignment notes |
| `metadata` | JSONB | Additional assignment data |

**Foreign Keys:**  
- `room_id` → `rooms.room_id` (CASCADE delete)
- `patient_id` → `patients.patient_id` (CASCADE delete)

**Indexes:** `room_id`, `patient_id`, `assigned_at DESC`

**Business Rules:**
- One patient per room (enforced by application logic)
- No duplicate assignments for same patient

---

## 🏥 Clinical Data Tables

### `medical_history`
**Purpose:** Complete patient medical timeline with structured metadata

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `patient_id` | TEXT | Patient reference |
| `entry_type` | TEXT | Type: diagnosis, procedure, medication, allergy, vital_measurement, lab_result, imaging, note, symptom, family_history, social_history |
| `entry_date` | TIMESTAMPTZ | When this occurred/was documented |
| `title` | TEXT | Brief title/summary |
| `description` | TEXT | Detailed description |
| `severity` | TEXT | critical, high, medium, low, info |
| `status` | TEXT | active, resolved, chronic, historical |
| `provider` | TEXT | Provider name |
| `facility` | TEXT | Facility where occurred |
| `metadata` | JSONB | **Structured data: vitals, lab values, dosages** |
| `created_at` | TIMESTAMPTZ | Record creation |
| `updated_at` | TIMESTAMPTZ | Last update |

**Foreign Keys:** `patient_id` → `patients.patient_id` (CASCADE delete)

**Critical Feature - Metadata Examples:**

**Vital Measurement:**
```json
{
  "heart_rate": 108,
  "blood_pressure": "102/68",
  "temperature": 39.2,
  "respiratory_rate": 28,
  "oxygen_saturation": 92,
  "consciousness": "alert",
  "seizure_free_hours": 72
}
```

**Lab Result:**
```json
{
  "wbc": 14.5,
  "wbc_unit": "K/uL",
  "crp": 85,
  "crp_unit": "mg/L",
  "procalcitonin": 1.2,
  "trend": "improving"
}
```

**Medication:**
```json
{
  "dosage": "1000mg",
  "frequency": "BID",
  "route": "PO",
  "therapeutic_level": "monitored",
  "indication": "seizure_control"
}
```

**Indexes:** `patient_id`, `entry_type`, `entry_date DESC`, `status`, `severity`

---

### `vital_signs`
**Purpose:** Time-series vital sign measurements for trending

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `patient_id` | TEXT | Patient reference |
| `recorded_at` | TIMESTAMPTZ | Measurement timestamp |
| `heart_rate` | NUMERIC | Beats per minute |
| `respiratory_rate` | NUMERIC | Breaths per minute |
| `temperature` | NUMERIC | Celsius |
| `oxygen_saturation` | NUMERIC | SpO2 percentage |
| `blood_pressure_systolic` | NUMERIC | mmHg |
| `blood_pressure_diastolic` | NUMERIC | mmHg |
| `crs_score` | NUMERIC | Risk score (0-1) |
| `crs_grade` | INTEGER | Grade (0-4) |
| `pain_level` | INTEGER | Pain scale (0-10) |
| `consciousness_level` | TEXT | alert, confused, drowsy, unresponsive |
| `measurement_type` | TEXT | routine, admission, alert_triggered, etc. |
| `recorded_by` | TEXT | Who recorded (nurse/system) |
| `location` | TEXT | Where measured (room/unit) |
| `notes` | TEXT | Clinical notes |
| `metadata` | JSONB | Additional measurements |
| `created_at` | TIMESTAMPTZ | Record creation |

**Foreign Keys:** `patient_id` → `patients.patient_id` (CASCADE delete)

**Indexes:**  
- `patient_id`
- `recorded_at DESC`
- `patient_id, recorded_at DESC` (composite for trending)
- `crs_grade` (partial index WHERE >= 3)

**Views:**
- `patient_latest_vitals` - Most recent vital per patient
- `abnormal_vitals` - Auto-detected concerning values

---

### `alerts`
**Purpose:** Real-time clinical alerts and notifications

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `alert_type` | TEXT | vital_sign, crs, medication, fall_risk, equipment, protocol, other |
| `severity` | TEXT | critical, high, medium, low, info |
| `patient_id` | TEXT | Associated patient (nullable) |
| `room_id` | TEXT | Associated room (nullable) |
| `title` | TEXT | Alert title |
| `description` | TEXT | Detailed description |
| `status` | TEXT | active, acknowledged, resolved, dismissed |
| `triggered_by` | TEXT | System/person who triggered |
| `triggered_at` | TIMESTAMPTZ | When alert fired |
| `acknowledged_by` | TEXT | Who acknowledged |
| `acknowledged_at` | TIMESTAMPTZ | When acknowledged |
| `resolved_by` | TEXT | Who resolved |
| `resolved_at` | TIMESTAMPTZ | When resolved |
| `metadata` | JSONB | Alert-specific data |
| `created_at` | TIMESTAMPTZ | Record creation |
| `updated_at` | TIMESTAMPTZ | Last update |

**Foreign Keys:**  
- `patient_id` → `patients.patient_id`
- `room_id` → `rooms.room_id`

**Indexes:** `patient_id`, `room_id`, `status`, `severity`, `triggered_at DESC`

---

## 🤖 AI & Communication Tables

### `chat_sessions`
**Purpose:** Haven AI chat conversation persistence

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | TEXT | User identifier (default: 'default_user') |
| `title` | TEXT | Session title (from first message) |
| `context` | JSONB | Full conversation context + state |
| `created_at` | TIMESTAMPTZ | Session start |
| `updated_at` | TIMESTAMPTZ | Last activity |

**Context JSONB Structure:**
```json
{
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "kv_store": {},
  "state": {
    "current_page": "/dashboard/floorplan",
    "user_name": "Clinical Staff",
    "tagged_context": []
  }
}
```

**Indexes:** `user_id`, `updated_at DESC`, GIN on `context`

---

## 📈 Key Relationships

```
patients (1) ──────< (M) patients_room (M) >────── (1) rooms
    │                                                      │
    │                                                      │
    ├──< medical_history (1:M)                            │
    ├──< vital_signs (1:M)                                │
    ├──< alerts (1:M)                         alerts >────┘
    
rooms (M) >────── (1) floors

chat_sessions (independent - no FK)
```

---

## 🔍 Critical Metadata Fields

### Why Metadata is Essential:

The AI tools query metadata to make informed decisions. Examples:

**1. Checking for Allergies:**
```sql
SELECT * FROM medical_history 
WHERE patient_id = 'P-DAV-001' 
  AND entry_type = 'allergy'
  AND metadata->>'allergen' = 'penicillin'
```

**2. Trending Vitals:**
```sql
SELECT 
  entry_date,
  metadata->>'heart_rate' as hr,
  metadata->>'temperature' as temp
FROM medical_history 
WHERE patient_id = 'P-DHE-001'
  AND entry_type = 'vital_measurement'
ORDER BY entry_date DESC
```

**3. Medication Details:**
```sql
SELECT 
  title,
  metadata->>'dosage' as dose,
  metadata->>'frequency' as freq,
  metadata->>'route' as route
FROM medical_history
WHERE patient_id = 'P-DAV-001'
  AND entry_type = 'medication'
  AND status = 'active'
```

---

## 🎯 Current Mock Patients

### Dheeraj Vislawath (P-DHE-001)
- **Age:** 20
- **Condition:** Epilepsy - Seizure Disorder Monitoring
- **Status:** Active monitoring, video EEG
- **Last Seizure:** 3 days ago (witnessed, 90 sec)
- **Medications:** Levetiracetam 1000mg BID, Lacosamide 200mg BID
- **Location:** Neuro ICU
- **Photo:** `/images/dheeraj.jpeg` (Supabase Storage)

### David Chung (P-DAV-001)
- **Age:** 20
- **Condition:** Community-Acquired Pneumonia
- **Status:** Day 7, improving, fever resolved
- **Allergies:** Penicillin (rash/hives)
- **Medications:** Ceftriaxone IV, Azithromycin PO
- **Location:** Medical Floor
- **Photo:** `/images/david.jpeg` (Supabase Storage)

---

## 📝 SQL Files Reference

| File | Purpose | Run Order |
|------|---------|-----------|
| `VITAL_SIGNS_TABLE.sql` | Create vital_signs table + sample data | 1st |
| `UPDATE_DHEERAJ_SEIZURES.sql` | Update Dheeraj to seizure patient | 2nd |
| `UPDATE_PATIENT_AGES.sql` | Set both patients to age 20 | (optional) |

---

## 🔐 Security & Permissions

**Row Level Security (RLS):**
- Currently disabled for development
- TODO: Enable RLS in production
- TODO: Add service role policies

**API Access:**
- Supabase anon key for read operations
- Service key for write operations (backend only)

---

## 🚀 Performance Optimizations

**Indexes Created:**
- Time-series queries (vital_signs by patient + date)
- Alert lookups (status + severity)
- Medical history filtering (type + date)
- Room assignments (patient_id, room_id)
- GIN indexes for JSONB columns

**Views for Common Queries:**
- `patient_latest_vitals` - Current vital signs
- `abnormal_vitals` - Flagged measurements

---

## 📊 Sample Data Statistics

After running all SQL files:
- **Patients:** 2 (Dheeraj, David)
- **Medical History:** ~35 entries
- **Vital Signs:** ~250+ measurements
- **Alerts:** ~6 active/resolved
- **Rooms:** 6 (5 patient rooms, 1 nurse station)
- **Floors:** 1 (floor-1)
- **Chat Sessions:** Created as used

---

## 🔄 AI Tool Integration

**Tools That Query These Tables:**

| Tool | Tables Queried |
|------|----------------|
| `search_patients` | patients |
| `get_patient_details` | patients, patients_room, rooms, alerts |
| `get_patient_medical_history` | medical_history |
| `generate_patient_clinical_summary` | patients, medical_history, vital_signs, alerts, patients_room |
| `get_room_status` | rooms, patients_room, patients |
| `transfer_patient` | patients_room (read/write) |
| `get_active_alerts` | alerts |

---

## 📈 Data Flow Example

**Patient Admission Flow:**
1. Insert into `patients` table
2. Add medical history entries (diagnosis, allergies, medications)
3. Assign to room (`patients_room`)
4. Begin vital sign monitoring (`vital_signs` every 4h)
5. Alerts trigger based on vitals (`alerts`)
6. AI monitors and generates reports
7. Discharge: Remove from `patients_room`, generate discharge PDF

---

## 🎨 Frontend Data Usage

**Dashboard:**
- Queries: `patients`, `alerts`, `patients_room`
- Real-time: Polls alerts every 5 seconds
- Updates: Cache invalidation via events

**Floor Plan:**
- Queries: `rooms`, `patients_room`, `patients`
- Updates: Real-time when patients assigned/removed
- 3D Visualization: Uses `rooms.metadata` polygon data

**AI Chat:**
- Queries: All tables via tool calls
- Writes: `patients_room`, `medical_history`, `alerts`
- Context: Stored in `chat_sessions`

---

## 📋 Future Enhancements

**Planned Tables:**
- [ ] `nursing_notes` - Shift notes and assessments
- [ ] `medications_administered` - MAR (Medication Administration Record)
- [ ] `imaging_studies` - X-rays, CT scans, MRIs
- [ ] `lab_orders` - Pending and completed labs
- [ ] `care_team` - Assigned providers per patient
- [ ] `discharge_summaries` - Structured discharge data

**Planned Features:**
- [ ] Real-time vitals streaming (WebSocket)
- [ ] Automated alert escalation rules
- [ ] Audit logging for all changes
- [ ] Multi-tenant support (organizations)

---

## 🔧 Maintenance

**Backup Recommendations:**
- Daily automated backups (Supabase handles this)
- Export critical tables weekly
- Version control schema changes

**Performance Monitoring:**
- Monitor slow queries (>1s)
- Review index usage monthly
- Archive old data (>1 year) to cold storage

---

**Last Schema Update:** October 25, 2025  
**Maintained By:** Haven Development Team  
**Questions:** Reference this doc + check Supabase dashboard

