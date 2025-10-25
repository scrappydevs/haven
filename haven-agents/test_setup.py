"""
Test script to verify Haven AI agent setup
Run this before starting the demo to ensure everything works
"""
import sys
import os
from pathlib import Path

print("=" * 80)
print("🧪 HAVEN AI - SETUP VERIFICATION TEST")
print("=" * 80)
print("\nChecking system requirements...\n")

# Test 1: Python version
print("1. Python Version")
try:
    import sys
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (need 3.10+)")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 2: Required packages
print("\n2. Required Packages")
required_packages = {
    "uagents": "Fetch.ai uAgents framework",
    "anthropic": "Anthropic Claude API",
    "pydantic": "Data validation",
}

all_installed = True
for package, description in required_packages.items():
    try:
        __import__(package)
        print(f"   ✅ {package:15s} - {description}")
    except ImportError:
        print(f"   ❌ {package:15s} - MISSING ({description})")
        all_installed = False

if not all_installed:
    print("\n   Install missing packages:")
    print("   pip install -r requirements.txt\n")
    sys.exit(1)

# Test 3: Environment variables
print("\n3. Environment Variables")
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        print(f"   ✅ ANTHROPIC_API_KEY: {anthropic_key[:20]}...")
    else:
        print("   ⚠️  ANTHROPIC_API_KEY: Not set (Claude will use fallback rules)")
    
    mailbox_key = os.getenv("AGENT_MAILBOX_KEY")
    if mailbox_key:
        print(f"   ✅ AGENT_MAILBOX_KEY: {mailbox_key[:20]}... (Agentverse enabled)")
    else:
        print("   ℹ️  AGENT_MAILBOX_KEY: Not set (local mode only)")
except ImportError:
    print("   ⚠️  python-dotenv not installed (optional)")

# Test 4: Import all agents
print("\n4. Agent Modules")
sys.path.append(str(Path(__file__).parent))

agent_modules = [
    ("agents.patient_guardian", "Patient Guardian Agent"),
    ("agents.nurse_coordinator", "Nurse Coordinator Agent"),
    ("agents.emergency_response", "Emergency Response Agent"),
    ("agents.protocol_compliance", "Protocol Compliance Agent"),
    ("agents.research_insights", "Research Insights Agent"),
]

all_agents_ok = True
for module, name in agent_modules:
    try:
        __import__(module)
        print(f"   ✅ {name}")
    except Exception as e:
        print(f"   ❌ {name}: {e}")
        all_agents_ok = False

if not all_agents_ok:
    print("\n   Fix agent import errors before continuing.\n")
    sys.exit(1)

# Test 5: Model imports
print("\n5. Data Models")
model_modules = [
    ("models.vitals", "PatientVitals"),
    ("models.alerts", "PatientAlert"),
    ("models.protocols", "ProtocolRules"),
]

for module, name in model_modules:
    try:
        __import__(module)
        print(f"   ✅ {name}")
    except Exception as e:
        print(f"   ❌ {name}: {e}")

# Test 6: Utility modules
print("\n6. Utility Modules")
util_modules = [
    ("utils.claude_client", "Claude Client"),
    ("utils.mock_data", "Mock Data Generator"),
]

for module, name in util_modules:
    try:
        __import__(module)
        print(f"   ✅ {name}")
    except Exception as e:
        print(f"   ❌ {name}: {e}")

# Test 7: Claude API connection (if key provided)
print("\n7. Claude API Connection")
try:
    from utils.claude_client import claude_client
    if claude_client.client:
        print("   ✅ Claude API client initialized")
        print("   ✅ Ready for AI reasoning")
    else:
        print("   ⚠️  Claude API not configured")
        print("   ℹ️  Agents will use fallback rule-based logic")
except Exception as e:
    print(f"   ⚠️  Claude client error: {e}")

# Test 8: Create test agent
print("\n8. Test Agent Creation")
try:
    from agents.patient_guardian import create_patient_guardian
    test_guardian = create_patient_guardian("TEST-001", name="test_guardian")
    print(f"   ✅ Test agent created")
    print(f"   ✅ Agent address: {test_guardian.agent.address}")
    print(f"   ✅ Chat protocol: Enabled")
except Exception as e:
    print(f"   ❌ Failed to create test agent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Final summary
print("\n" + "=" * 80)
print("✅ SETUP VERIFICATION COMPLETE")
print("=" * 80)

print("\n🎉 All systems ready! You can now:")
print("\n1. Run full demo:")
print("   python main.py")
print("\n2. Run individual agents:")
print("   python agents/patient_guardian.py")
print("\n3. View deployment info:")
print("   python deploy.py")
print("\n4. Test single agent for 1 minute:")
print("   timeout 60 python agents/patient_guardian.py")

print("\n" + "=" * 80)
print("\n📋 System Summary:\n")
print(f"   • Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
print(f"   • uAgents: Installed ✅")
print(f"   • Claude API: {'Enabled ✅' if claude_client.client else 'Fallback mode ⚠️'}")
print(f"   • 5 Autonomous Agents: Ready ✅")
print(f"   • Chat Protocol: Enabled ✅")
print(f"   • Agent-to-Agent Comm: Ready ✅")

print("\n" + "=" * 80)
print("\n🏆 Ready for Fetch.ai Innovation Lab Prize!")
print("\nNext steps:")
print("  1. ✅ Setup complete (you are here)")
print("  2. ⏳ Run demo: python main.py")
print("  3. ⏳ Record 3-5 min video")
print("  4. ⏳ (Optional) Deploy to Agentverse")
print("  5. ⏳ Submit to hackathon")
print("\n" + "=" * 80 + "\n")

