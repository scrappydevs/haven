# Database Reference - TrialSentinel AI

## Supabase Tables

### 📋 `public.patients`

Patient information for clinical trial monitoring.

**Columns:**
- `id` (uuid, PK) - Auto-generated unique identifier
- `patient_id` (text, UNIQUE) - Human-readable patient ID (e.g., "P-001")
- `name` (text) - Patient full name
- `age` (integer) - Patient age
- `gender` (text) - Patient gender
- `date_of_birth` (date) - Date of birth
- `photo_url` (text) - URL to patient photo
- `condition` (text) - Medical condition/diagnosis
- `enrollment_date` (date) - Trial enrollment date
- `enrollment_status` (text) - Status: 'active', 'completed', 'withdrawn'
- `ecog_status` (integer) - ECOG performance status (0-4)
- `prior_treatment_lines` (integer) - Number of prior therapies
- `infusion_count` (integer) - Number of infusions received
- `baseline_vitals` (jsonb) - Baseline vital signs data
- `baseline_crs_risk` (numeric) - Baseline CRS risk score (0-1)
- `created_at` (timestamp) - Record creation time
- `updated_at` (timestamp) - Last update time
- `notes` (text) - Additional notes

**Used By:**
- `/patients/search` - Search patients by name
- `/patients/by-id/{patient_id}` - Get patient details
- Floor plan patient assignment

---

### 🏥 `public.room_assignments`

Hospital floor plan room and patient assignments.

**Columns:**
- `id` (uuid, PK) - Auto-generated unique identifier
- `room_id` (text, UNIQUE) - Room identifier (e.g., "room-101", furniture ID from Smplrspace)
- `room_name` (text) - Display name for room
- `room_type` (text) - Room type: 'patient', 'nurse_station', 'icu', 'surgery', 'lab', 'other'
- `patient_id` (text) - Assigned patient ID (foreign key to patients.patient_id)
- `patient_name` (text) - Cached patient name for performance
- `nurse_ids` (text[]) - Array of assigned nurse IDs
- `metadata` (jsonb) - Additional room metadata
- `created_at` (timestamp) - Record creation time
- `updated_at` (timestamp) - Last update time

**Constraints:**
- `room_type` CHECK constraint enforces valid types
- `room_id` UNIQUE constraint prevents duplicates

**Indexes:**
- `idx_room_assignments_patient_id` on `patient_id` - Fast patient lookups
- `idx_room_assignments_room_type` on `room_type` - Filter by room type

**Used By:**
- `GET /rooms/assignments` - Fetch all room assignments
- `POST /rooms/assign-patient` - Assign patient to room
- `DELETE /rooms/unassign-patient/{room_id}` - Remove patient from room
- `POST /rooms/assign-nurse` - Assign nurse to station
- `DELETE /rooms/unassign-nurse/{room_id}/{nurse_id}` - Remove nurse

---

## API Operations

### Get All Room Assignments
```python
# DATABASE REFERENCE: public.room_assignments
response = supabase.table("room_assignments").select("*").execute()
```

### Assign Patient to Room
```python
# DATABASE REFERENCE: public.room_assignments
# Updates: patient_id, patient_name
# WHERE: room_id = :room_id
response = supabase.table("room_assignments") \
    .update({"patient_id": patient_id, "patient_name": patient_name}) \
    .eq("room_id", room_id) \
    .execute()
```

### Remove Patient from Room
```python
# DATABASE REFERENCE: public.room_assignments
# Sets: patient_id = NULL, patient_name = NULL
# WHERE: room_id = :room_id
response = supabase.table("room_assignments") \
    .update({"patient_id": None, "patient_name": None}) \
    .eq("room_id", room_id) \
    .execute()
```

### Search Patients
```python
# DATABASE REFERENCE: public.patients
# WHERE: name ILIKE '%:query%' AND enrollment_status = 'active'
response = supabase.table("patients") \
    .select("*") \
    .ilike("name", f"%{query}%") \
    .eq("enrollment_status", "active") \
    .order("name") \
    .execute()
```

---

## Environment Variables

**Backend (.env):**
```bash
SUPABASE_URL=https://mbmccgnixowxwryycedf.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SMPLR_SPACE_ID=spc_hjebpfu1
NEXT_PUBLIC_SMPLR_CLIENT_TOKEN=pub_f2847c1d38634d919b77b2e7a3467998
```

---

## Row Level Security (RLS)

Both tables have RLS enabled with policies:

**Policy: "Allow all operations for authenticated users"**
- Applies to: authenticated role
- Operations: SELECT, INSERT, UPDATE, DELETE
- Condition: true (allow all)

**Policy: "Allow all operations for service role"**
- Applies to: service_role
- Operations: SELECT, INSERT, UPDATE, DELETE
- Condition: true (allow all)

---

## Triggers

**`update_updated_at_column()`**
- Automatically updates `updated_at` timestamp on row UPDATE
- Applies to: `room_assignments` table

---

## Usage Examples

### Create Room Assignment (Auto-created on first patient assignment)
```sql
INSERT INTO room_assignments (room_id, room_name, room_type)
VALUES ('bedroom-1', 'Bedroom 1', 'patient');
```

### Assign Patient
```sql
UPDATE room_assignments
SET patient_id = 'P-001', patient_name = 'John Doe'
WHERE room_id = 'bedroom-1';
```

### Query Occupied Rooms
```sql
SELECT * FROM room_assignments
WHERE patient_id IS NOT NULL;
```

### Query by Room Type
```sql
SELECT * FROM room_assignments
WHERE room_type = 'patient';
```

---

**Migration File:** `/backend/migrations/001_room_assignments.sql`

