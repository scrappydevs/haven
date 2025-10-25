# 🏥 Haven AI - Room Management Through Chat

## 🎯 Overview

You can now manage patient room assignments **directly through the Haven AI chat** using natural language commands. The AI will execute the appropriate database operations and confirm actions.

---

## 💬 **CONVERSATIONAL COMMANDS**

### **1. Remove Patient from Room**

**What you can say:**
```
"Remove P-001 from their room"
"Please discharge patient P-001"
"Take David Rodriguez out of room 2"
"Remove patient from room xyz"
"Discharge Emily Martinez"
```

**What happens:**
1. 🔧 AI calls `remove_patient_from_room` tool
2. Queries database for current room assignment
3. Removes patient from `patients_room` table
4. Optionally generates discharge report PDF
5. Confirms action with room name

**AI Response:**
```
✅ Removed patient P-001 from Room 2

Discharge report generated and available for download.

Next steps: Room 2 is now available for new patient assignment.
```

---

### **2. Transfer Patient Between Rooms**

**What you can say:**
```
"Transfer P-001 to Room 5"
"Move David Rodriguez from Room 2 to Room 3"
"Relocate Emily Martinez to Room 1"
"Change patient P-004's room to Room 5"
```

**What happens:**
1. 🔧 AI calls `transfer_patient` tool
2. Auto-detects current room (if not specified)
3. Checks if destination room is available
4. Removes from old room
5. Assigns to new room
6. Updates `patients_room` table

**AI Response:**
```
✅ Transferred patient P-001 from Room 2 to Room 5

Transfer complete. Patient now located in Room 5.

Status: Room 2 is now available.
```

---

### **3. Check Patient's Current Room**

**What you can say:**
```
"Where is P-001?"
"Which room is David Rodriguez in?"
"Find Emily Martinez's room"
"What room is patient P-004 in?"
```

**What happens:**
1. 🔧 AI calls `get_patient_current_room` tool
2. Queries `patients_room` table
3. Joins with `rooms` table for details

**AI Response:**
```
**Patient P-001** (David Rodriguez)

Currently assigned to: Room 2
Room type: Patient room
Assigned since: 2025-10-25 14:23:45
```

---

### **4. Suggest Optimal Room**

**What you can say:**
```
"Suggest a room for P-001"
"Find the best room for Emily Martinez"
"Where should I put patient P-004?"
"Recommend a room for this patient"
```

**What happens:**
1. 🔧 AI calls `suggest_optimal_room` tool
2. Gets patient condition
3. Lists available rooms
4. Suggests best option with reasoning

**AI Response:**
```
Suggested room for P-001:

**Room 5** (patient room)
Reason: Next available patient room

Other available options: Room 3, Room 4

Total available: 3 rooms
```

---

### **5. Combined Operations**

You can also combine commands in natural conversation:

**Complex Example 1:**
```
User: "I need to transfer P-001 from Room 2 to an available room"

AI:
1. 🔧 get_patient_current_room("P-001")
2. 🔧 list_available_rooms()
3. 🔧 suggest_optimal_room("P-001")
4. Responds with recommendation

"Patient P-001 is currently in Room 2.

Available rooms: Room 3, Room 5

Suggested: **Room 5** (closest available)

Would you like me to proceed with the transfer?"
```

**Complex Example 2:**
```
User: "Yes, transfer P-001 to Room 5"

AI:
1. 🔧 transfer_patient("P-001", "Room 5")
2. Confirms transfer

"✅ Transferred P-001 from Room 2 to Room 5

Transfer complete. Patient now in Room 5.

Room 2 is now available for admission."
```

---

## 🔒 **SAFETY FEATURES**

### **Validation Checks:**
1. **Patient exists** before any operation
2. **Room availability** before assignment/transfer
3. **Current assignment** verified before removal
4. **No duplicate assignments** (one patient per room)

### **Error Handling:**
```
User: "Transfer P-001 to Room 2"

AI: "❌ Cannot transfer: Room 2 is already occupied by patient P-002.

Available rooms: Room 3, Room 5

Would you like to transfer to one of these instead?"
```

### **Confirmation Messages:**
Every operation includes:
- ✅ Success confirmation
- Patient ID and name
- Room names (not just IDs)
- Next steps or status

---

## 📊 **TOOLS SUMMARY**

| Tool | Read/Write | Use Case |
|------|------------|----------|
| `search_patients` | Read | Find patients |
| `get_patient_details` | Read | Full patient info |
| `get_room_status` | Read | Check room |
| `list_occupied_rooms` | Read | See full rooms |
| `list_available_rooms` | Read | See empty rooms |
| `get_active_alerts` | Read | Check alerts |
| `get_hospital_stats` | Read | Overall stats |
| `get_patients_by_condition` | Read | Filter by diagnosis |
| `get_patient_current_room` | Read | Patient location |
| `assign_patient_to_room` | **Write** | Put patient in room |
| `remove_patient_from_room` | **Write** | Discharge/remove |
| `transfer_patient` | **Write** | Move between rooms |
| `suggest_optimal_room` | Read | Get recommendation |
| `get_crs_monitoring_protocol` | Read | CRS guidelines |

**Total: 14 tools** (10 read, 4 write)

---

## 🧪 **TESTING EXAMPLES**

### **Test 1: Simple Removal**
```
User: "Remove P-001 from their room"
Expected: ✅ Confirmation + discharge report offer
```

### **Test 2: Transfer**
```
User: "Transfer David Rodriguez to Room 5"
Expected: ✅ Finds patient ID, executes transfer, confirms
```

### **Test 3: Room Query**
```
User: "Where is Emily Martinez?"
Expected: 🔧 Searches patient, finds room, reports location
```

### **Test 4: Suggestion**
```
User: "I need to admit P-003, suggest a room"
Expected: 🔧 Lists available rooms, suggests best option
```

### **Test 5: Complex Workflow**
```
User: "I need to move P-001 to a different room because of an equipment issue"

AI: 
- Checks current room
- Lists alternatives
- Asks which room or suggests best

User: "Put them in Room 5"

AI:
- Transfers patient
- Confirms new location
- Marks old room available
```

---

## 🎨 **AI RESPONSE STYLE**

**Before (No Tools):**
```
User: "Remove P-001 from Room 2"
AI: "I don't have the ability to modify room assignments..."
```

**After (With Tools):**
```
User: "Remove P-001 from Room 2"
AI: 🔧 [Executes removal]

"✅ Removed patient P-001 (David Rodriguez) from Room 2

Room 2 is now available for new admissions.

Discharge report generated: /reports/discharge/P-001/room-2

Action complete."
```

---

## ⚡ **WORKFLOW EXAMPLES**

### **Discharge Flow:**
```
1. "Remove P-001 from their room"
   → Removes patient
   → Generates PDF report
   → Frees up room

2. "Download discharge report for P-001"
   → Provides download link
```

### **Transfer Flow:**
```
1. "Where is P-001?"
   → Room 2

2. "What rooms are available?"
   → Room 3, Room 5

3. "Transfer P-001 to Room 5"
   → Executes transfer
   → Confirms completion
```

### **Admission Flow:**
```
1. "Find available rooms"
   → Lists empty rooms

2. "Suggest room for P-004"
   → Recommends Room 5

3. "Assign P-004 to Room 5"
   → Creates assignment
   → Confirms placement
```

---

## 🚀 **SETUP**

### **Already Configured!**
All tools are already integrated. Just:

1. **Restart backend:**
   ```bash
   cd backend
   source venv/bin/activate
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Refresh frontend:**
   ```bash
   # Cmd+Shift+R
   ```

3. **Start using:**
   ```
   Open chat → Type: "Remove P-001 from Room 2"
   ```

---

## 📝 **NATURAL LANGUAGE EXAMPLES**

The AI understands various phrasings:

### **Removal:**
- "Remove patient xyz from room"
- "Discharge P-001"
- "Take patient out of Room 2"
- "Clear Room 3"

### **Transfer:**
- "Move P-001 to Room 5"
- "Transfer patient from Room 2 to Room 3"
- "Relocate P-004 to a different room"
- "Change Emily's room to Room 1"

### **Assignment:**
- "Put P-001 in Room 2"
- "Assign David Rodriguez to Room 3"
- "Place patient P-004 in an available room"

### **Queries:**
- "Where is P-001?"
- "Which room has David Rodriguez?"
- "Is Emily Martinez in a room?"
- "Show me P-004's location"

---

## ✅ **BENEFITS**

1. **Hands-Free**: Talk or type, no clicking through UI
2. **Fast**: Direct database operations
3. **Confirmed**: Every action gets clear confirmation
4. **Safe**: Validates before executing
5. **Tracked**: All changes logged with "Haven AI" as assignor
6. **Reports**: Auto-generates discharge PDFs

---

## 🎯 **READY TO USE!**

Try it now:
```
1. Open Haven AI chat (click ❤️ or press ⌘⇧H)
2. Type: "Remove P-001 from their room"
3. Watch: Tool call → Database update → Confirmation
4. Verify: Check Floor Plan → Room should be empty
```

**You can now manage your entire hospital through conversation!** 🚀

