"""
Deploy Haven AI Agents to Agentverse
This script helps you register and deploy agents to Fetch.ai's Agentverse
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

print("=" * 80)
print("🚀 HAVEN AI - AGENTVERSE DEPLOYMENT")
print("=" * 80)
print("\n📋 This script will help you deploy agents to Fetch.ai's Agentverse")
print("\n✨ What Agentverse provides:")
print("  • Persistent agent hosting (agents run 24/7)")
print("  • Public agent addresses (discoverable by other agents)")
print("  • Mailbox service (reliable message delivery)")
print("  • ASI:One marketplace integration")
print("\n" + "=" * 80)

print("\n📝 DEPLOYMENT OPTIONS:\n")
print("OPTION 1: Local Development (Recommended for Testing)")
print("  ✓ Run agents locally on your machine")
print("  ✓ No Agentverse account needed")
print("  ✓ Perfect for development and testing")
print("  ✓ Agents communicate via local network")
print("  → Run: python main.py")

print("\nOPTION 2: Agentverse Deployment (Production)")
print("  ✓ Agents hosted on Fetch.ai infrastructure")
print("  ✓ 24/7 availability")
print("  ✓ Public agent addresses")
print("  ✓ ASI:One marketplace integration")
print("  → Requires Agentverse account")

print("\n" + "=" * 80)
print("\n🔧 AGENTVERSE SETUP INSTRUCTIONS:\n")

print("STEP 1: Create Agentverse Account")
print("  1. Go to: https://agentverse.ai")
print("  2. Click 'Sign Up' (free account)")
print("  3. Verify your email")

print("\nSTEP 2: Get Your Mailbox Key")
print("  1. Login to Agentverse")
print("  2. Go to: Profile → API Keys")
print("  3. Create new 'Mailbox Key'")
print("  4. Copy the key")

print("\nSTEP 3: Configure Environment")
print("  1. Copy .env.example to .env:")
print("     cp .env.example .env")
print("  2. Edit .env and add your keys:")
print("     AGENT_MAILBOX_KEY=<your_mailbox_key>")
print("     ANTHROPIC_API_KEY=<your_anthropic_key>")

print("\nSTEP 4: Deploy Agents")
print("  Option A: Deploy via Agentverse UI")
print("    1. Go to Agentverse → 'My Agents'")
print("    2. Click 'Create Agent'")
print("    3. Upload agent code (each .py file in agents/)")
print("    4. Configure environment variables")
print("    5. Deploy")
print("")
print("  Option B: Deploy via CLI (Advanced)")
print("    1. Install: pip install fetchai-agentverse")
print("    2. Configure: agentverse config set")
print("    3. Deploy: agentverse deploy")

print("\n" + "=" * 80)
print("\n🎯 RECOMMENDED WORKFLOW:\n")

print("1. DEVELOPMENT PHASE (Now)")
print("   → Run locally: python main.py")
print("   → Test all features")
print("   → Verify Claude integration")
print("   → Test agent communication")

print("\n2. DEMO PHASE (For Hackathon)")
print("   → Keep running locally")
print("   → Record demo video")
print("   → Show agent interactions")
print("   → Highlight Claude reasoning")

print("\n3. PRODUCTION PHASE (Optional)")
print("   → Deploy to Agentverse")
print("   → Get public agent addresses")
print("   → Add to README")
print("   → Submit to ASI:One marketplace")

print("\n" + "=" * 80)
print("\n💡 FOR FETCH.AI PRIZE SUBMISSION:\n")

print("✅ REQUIRED (You Have This):")
print("  ✓ Agents using uAgents framework")
print("  ✓ Claude as reasoning engine")
print("  ✓ Chat protocol implemented")
print("  ✓ Meaningful use case (patient safety)")
print("  ✓ Innovation Lab badges")

print("\n🎁 BONUS (Agentverse):")
print("  • Higher judging score")
print("  • Public agent addresses")
print("  • ASI:One marketplace")
print("  • Production-ready demo")

print("\n📹 CRITICAL FOR PRIZE:")
print("  🎥 Record 3-5 minute demo video showing:")
print("     • Agents running and communicating")
print("     • Claude reasoning visible")
print("     • Chat protocol working")
print("     • Real-world use case (patient monitoring)")

print("\n" + "=" * 80)
print("\n🚀 QUICK START:\n")
print("1. Run local demo now:")
print("   cd /Users/gsdr/haven/haven-agents")
print("   python main.py")
print("")
print("2. Record demo video:")
print("   • Show all 5 agents running")
print("   • Trigger concerning alert")
print("   • Trigger critical emergency")
print("   • Show Claude reasoning in logs")
print("   • Demo chat protocol")
print("")
print("3. (Optional) Deploy to Agentverse:")
print("   • Follow steps above")
print("   • Add agent addresses to README")
print("")
print("=" * 80)

print("\n\n🎯 AGENT ADDRESSES (Local Development):\n")

try:
    from agents.patient_guardian import create_patient_guardian
    from agents.nurse_coordinator import NurseCoordinatorAgent
    from agents.emergency_response import EmergencyResponseAgent
    from agents.protocol_compliance import ProtocolComplianceAgent
    from agents.research_insights import ResearchInsightsAgent
    
    print("Creating agents to display addresses...\n")
    
    # Patient Guardians
    for patient_id in ["P-001", "P-002", "P-003"]:
        guardian = create_patient_guardian(patient_id)
        print(f"Patient Guardian ({patient_id}):")
        print(f"  Address: {guardian.agent.address}")
        print(f"  Port: {guardian.agent._port}")
        print("")
    
    # Coordinator
    coordinator = NurseCoordinatorAgent()
    print(f"Nurse Coordinator:")
    print(f"  Address: {coordinator.agent.address}")
    print(f"  Port: 8010")
    print("")
    
    # Emergency
    emergency = EmergencyResponseAgent()
    print(f"Emergency Response:")
    print(f"  Address: {emergency.agent.address}")
    print(f"  Port: 8020")
    print("")
    
    # Compliance
    compliance = ProtocolComplianceAgent()
    print(f"Protocol Compliance:")
    print(f"  Address: {compliance.agent.address}")
    print(f"  Port: 8030")
    print("")
    
    # Research
    research = ResearchInsightsAgent()
    print(f"Research Insights:")
    print(f"  Address: {research.agent.address}")
    print(f"  Port: 8040")
    print("")
    
    print("=" * 80)
    print("\n💾 Copy these addresses to your README.md for local testing")
    print("\n🌐 For Agentverse deployment, addresses will be different:")
    print("   Format: agent1q<hash>@agentverse")
    print("=" * 80)
    
except Exception as e:
    print(f"\n⚠️  Could not create agents: {e}")
    print("   Make sure all dependencies are installed:")
    print("   pip install -r requirements.txt")
    print("")

print("\n\n✅ Ready to proceed! Choose your path:\n")
print("  [1] Run local demo now: python main.py")
print("  [2] Deploy to Agentverse: Follow steps above")
print("  [3] Record demo video: Start local demo and record")
print("\n" + "=" * 80 + "\n")

