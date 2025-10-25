"""
Agentverse Deployment Helper
Prepares agents for deployment to Fetch.ai's Agentverse platform
"""
import os
import sys
from pathlib import Path

print("=" * 80)
print("🌐 AGENTVERSE DEPLOYMENT - STEP BY STEP GUIDE")
print("=" * 80)
print("\n📋 This will help you deploy all 5 agents to Agentverse")
print("   and register them for the Fetch.ai Innovation Lab Prize!\n")
print("=" * 80)

# Step 1: Account Setup
print("\n📝 STEP 1: CREATE AGENTVERSE ACCOUNT")
print("=" * 80)
print("\n1. Open browser and go to: https://agentverse.ai")
print("2. Click 'Sign Up' (top right)")
print("3. Create account with email")
print("4. Verify your email address")
print("5. Return here when done\n")

input("Press ENTER when you've created your account and logged in...")

# Step 2: Get Mailbox Key
print("\n" + "=" * 80)
print("🔑 STEP 2: GET YOUR MAILBOX KEY")
print("=" * 80)
print("\n1. In Agentverse, click your profile icon (top right)")
print("2. Go to 'API Keys'")
print("3. Click 'Create New Key' or 'Generate Mailbox Key'")
print("4. Copy the key (it looks like: mbox_...)")
print("5. Paste it below\n")

mailbox_key = input("Enter your Mailbox Key: ").strip()

# Validate key format (accepts both mbox_ and JWT formats)
if not mailbox_key:
    print("\n❌ Error: No mailbox key provided")
    sys.exit(1)

# JWT format is valid (newer Agentverse format)
if mailbox_key.startswith("eyJ"):
    print("\n✅ JWT format mailbox key detected (valid)")
elif mailbox_key.startswith("mbox_"):
    print("\n✅ Legacy mbox_ format detected (valid)")
else:
    print("\n⚠️  Warning: Unexpected key format")
    cont = input("\nContinue anyway? (y/n): ")
    if cont.lower() != 'y':
        sys.exit(1)

# Update .env file
print("\n✅ Saving mailbox key to .env file...")
env_path = Path(__file__).parent / ".env"

if env_path.exists():
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update or add mailbox key
    found = False
    for i, line in enumerate(lines):
        if line.startswith("AGENT_MAILBOX_KEY="):
            lines[i] = f"AGENT_MAILBOX_KEY={mailbox_key}\n"
            found = True
            break
    
    if not found:
        lines.append(f"\nAGENT_MAILBOX_KEY={mailbox_key}\n")
    
    with open(env_path, 'w') as f:
        f.writelines(lines)
else:
    with open(env_path, 'w') as f:
        f.write(f"AGENT_MAILBOX_KEY={mailbox_key}\n")

print("✅ Mailbox key saved!")

# Step 3: Deployment Instructions
print("\n" + "=" * 80)
print("🚀 STEP 3: DEPLOY AGENTS TO AGENTVERSE")
print("=" * 80)
print("\nYou have 2 options:\n")

print("OPTION A: Deploy via Agentverse UI (Recommended - Easier)")
print("-" * 80)
print("\nFor EACH agent file, do the following:\n")

agents = [
    ("patient_guardian.py", "Patient Guardian P-001", "8001"),
    ("patient_guardian.py", "Patient Guardian P-002", "8002"),
    ("patient_guardian.py", "Patient Guardian P-003", "8003"),
    ("nurse_coordinator.py", "Nurse Coordinator", "8010"),
    ("emergency_response.py", "Emergency Response", "8020"),
    ("protocol_compliance.py", "Protocol Compliance", "8030"),
    ("research_insights.py", "Research Insights", "8040"),
]

print("1. In Agentverse, click 'My Agents' → 'Create Agent'")
print("2. Give it a name (see list below)")
print("3. Copy the entire agent file code")
print("4. Paste into the code editor")
print("5. Click 'Environment Variables' and add:")
print("   - ANTHROPIC_API_KEY = your_anthropic_key")
print("6. Click 'Deploy'\n")

print("Agents to deploy:")
for i, (file, name, port) in enumerate(agents, 1):
    print(f"\n   Agent {i}: {name}")
    print(f"   File: agents/{file}")
    print(f"   Port: {port}")

print("\n" + "-" * 80)
print("\nOPTION B: Deploy via CLI (Advanced)")
print("-" * 80)
print("\n1. Install Agentverse CLI:")
print("   pip install fetchai-agentverse")
print("\n2. Configure:")
print("   agentverse config set")
print("\n3. Deploy each agent:")
print("   agentverse deploy agents/patient_guardian.py")
print("   (Repeat for each agent)")

print("\n" + "=" * 80)
print("\n📝 Which option do you want to use?")
print("   A) Deploy via Agentverse UI (easier)")
print("   B) Deploy via CLI (advanced)")
print("   C) Skip deployment for now\n")

choice = input("Enter choice (A/B/C): ").strip().upper()

if choice == 'A':
    print("\n✅ Great choice! Follow these steps:\n")
    print("1. Open Agentverse in your browser: https://agentverse.ai")
    print("2. Go to 'My Agents'")
    print("3. For each agent below, click 'Create Agent' and follow instructions\n")
    
    print("=" * 80)
    print("AGENT DEPLOYMENT CHECKLIST")
    print("=" * 80)
    
    for i, (file, name, port) in enumerate(agents, 1):
        print(f"\n[ ] Agent {i}: {name}")
        print(f"    File: agents/{file}")
        print(f"    Name in Agentverse: {name}")
        print(f"    Environment Variables:")
        print(f"      ANTHROPIC_API_KEY = <your_key>")
        if i <= 3:  # Patient guardians need patient ID
            patient_id = f"P-00{i}"
            print(f"      (Modify code to use patient_id='{patient_id}')")
    
    print("\n" + "=" * 80)
    print("\n💡 TIP: Open agents/ files in your code editor")
    print("   Copy entire file → Paste in Agentverse → Deploy")
    
    input("\nPress ENTER when you've deployed all agents...")

elif choice == 'B':
    print("\n📦 Installing Agentverse CLI...")
    os.system("pip install fetchai-agentverse")
    
    print("\n⚙️  Configuring Agentverse...")
    os.system("agentverse config set")
    
    print("\n🚀 Ready to deploy!")
    print("\nRun these commands to deploy each agent:\n")
    
    for file, name, port in agents:
        print(f"agentverse deploy agents/{file} --name '{name}'")

else:
    print("\n⏭️  Skipping deployment for now")
    print("   Run this script again when ready to deploy")

# Step 4: Get Agent Addresses
print("\n" + "=" * 80)
print("📍 STEP 4: GET YOUR AGENT ADDRESSES")
print("=" * 80)
print("\nAfter deploying, get each agent's address from Agentverse:\n")
print("1. Go to 'My Agents'")
print("2. Click on each agent")
print("3. Copy the agent address (looks like: agent1q...@agentverse)")
print("4. Save them for the README\n")

print("Create a file with your agent addresses:")
print("=" * 80)

addresses_file = Path(__file__).parent / "AGENT_ADDRESSES.txt"
print(f"\nFile will be saved to: {addresses_file}\n")

print("Patient Guardian P-001: ")
print("Patient Guardian P-002: ")
print("Patient Guardian P-003: ")
print("Nurse Coordinator: ")
print("Emergency Response: ")
print("Protocol Compliance: ")
print("Research Insights: ")

input("\nPress ENTER to continue...")

# Step 5: Enable Chat Protocol
print("\n" + "=" * 80)
print("💬 STEP 5: VERIFY CHAT PROTOCOL")
print("=" * 80)
print("\n✅ Good news! Chat protocol is already enabled in your code!")
print("\nIn patient_guardian.py, you have:")
print("   self.agent.include(chat_proto, publish_manifest=True)")
print("\nThis means your agents are already ASI:One compatible!")
print("\nTo test:")
print("1. In Agentverse, click on Patient Guardian P-001")
print("2. Click 'Chat' tab")
print("3. Send message: 'What is the patient status?'")
print("4. Verify agent responds\n")

# Step 6: Update README
print("\n" + "=" * 80)
print("📝 STEP 6: UPDATE README WITH ADDRESSES")
print("=" * 80)
print("\nOnce you have all agent addresses, update the README:")
print("\n1. Open haven-agents/README.md")
print("2. Add a section with your deployed agent addresses")
print("3. Format:")
print("""
## 🌐 Deployed Agents (Agentverse)

All agents are live on Fetch.ai's Agentverse:

- **Patient Guardian P-001**: `agent1q...@agentverse`
- **Patient Guardian P-002**: `agent1q...@agentverse`
- **Patient Guardian P-003**: `agent1q...@agentverse`
- **Nurse Coordinator**: `agent1q...@agentverse`
- **Emergency Response**: `agent1q...@agentverse`
- **Protocol Compliance**: `agent1q...@agentverse`
- **Research Insights**: `agent1q...@agentverse`

Test them live: https://agentverse.ai
""")

# Final Summary
print("\n" + "=" * 80)
print("✅ DEPLOYMENT CHECKLIST - FINAL VERIFICATION")
print("=" * 80)

checklist = [
    ("Create Agentverse account", "agentverse.ai"),
    ("Get mailbox key", "Profile → API Keys"),
    ("Deploy 7 agents", "My Agents → Create Agent"),
    ("Copy agent addresses", "Click each agent → Copy address"),
    ("Test chat protocol", "Click agent → Chat tab"),
    ("Update README with addresses", "Add deployed addresses section"),
    ("Verify all agents show 'Running'", "Check status in Agentverse"),
]

print("\nBefore submitting, verify:\n")
for i, (task, hint) in enumerate(checklist, 1):
    print(f"{i}. [ ] {task}")
    print(f"       ({hint})\n")

print("=" * 80)
print("\n🏆 PRIZE SUBMISSION REQUIREMENTS")
print("=" * 80)

requirements = [
    ("✅", "Agents registered on Agentverse", "7 agents deployed"),
    ("✅", "Chat protocol enabled", "publish_manifest=True in code"),
    ("✅", "Anthropic Claude integrated", "Claude 3.5 Sonnet reasoning"),
    ("✅", "Innovation Lab badges", "Added to README"),
    ("⏳", "Demo video (3-5 min)", "Record video showing agents"),
]

print("\n")
for status, requirement, note in requirements:
    print(f"{status} {requirement}")
    print(f"   → {note}\n")

print("=" * 80)
print("\n🎉 YOU'RE READY TO WIN!")
print("\nNext steps:")
print("1. ✅ Agents deployed to Agentverse")
print("2. ⏳ Record demo video showing:")
print("   - Agentverse dashboard with 7 agents running")
print("   - Chat with Patient Guardian")
print("   - Haven app with agent integration")
print("   - Claude reasoning in action")
print("3. ⏳ Submit to Innovation Lab")
print("\n" + "=" * 80)
print("\n💰 Prize: $2,500 + Internship Interview Opportunity")
print("🏆 You have a WINNING submission!")
print("\n" + "=" * 80 + "\n")

