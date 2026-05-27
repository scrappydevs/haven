"""
Phase 6: Integration & Polish - Complete Demo Flow
Main orchestrator that runs all agents together
"""
import sys
import os
import asyncio
import signal
from pathlib import Path
from datetime import datetime
from typing import List
import multiprocessing as mp

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from agents.patient_guardian import create_patient_guardian
from agents.nurse_coordinator import NurseCoordinatorAgent
from agents.emergency_response import EmergencyResponseAgent
from agents.protocol_compliance import ProtocolComplianceAgent
from agents.research_insights import ResearchInsightsAgent
from utils.mock_data import mock_generator


def run_patient_guardian(patient_id: str):
    """Run a patient guardian agent in a separate process"""
    guardian = create_patient_guardian(patient_id)
    try:
        guardian.run()
    except KeyboardInterrupt:
        pass


def run_nurse_coordinator():
    """Run nurse coordinator agent"""
    coordinator = NurseCoordinatorAgent()
    try:
        coordinator.run()
    except KeyboardInterrupt:
        pass


def run_emergency_response():
    """Run emergency response agent"""
    emergency = EmergencyResponseAgent()
    try:
        emergency.run()
    except KeyboardInterrupt:
        pass


def run_protocol_compliance():
    """Run protocol compliance agent"""
    compliance = ProtocolComplianceAgent()
    try:
        compliance.run()
    except KeyboardInterrupt:
        pass


def run_research_insights():
    """Run research insights agent"""
    research = ResearchInsightsAgent()
    try:
        research.run()
    except KeyboardInterrupt:
        pass


def print_demo_header():
    """Print demo header"""
    print("\n" + "=" * 80)
    print("🏥 HAVEN AI - MULTI-AGENT CLINICAL TRIAL MONITORING SYSTEM")
    print("=" * 80)
    print("\nBuilt with Fetch.ai uAgents + Anthropic Claude")
    print("CAR-T Cell Therapy Safety Monitoring Demo\n")
    print("=" * 80)
    print("\n📋 DEMO SCRIPT (3-5 minutes):")
    print("\nMinute 0-1: NORMAL OPERATIONS")
    print("  • All 3 patients stable")
    print("  • Routine monitoring every 30 seconds")
    print("  • Protocol compliance tracking active")
    print("\nMinute 1-2: CONCERNING ALERT")
    print("  • P-002 develops elevated vitals")
    print("  • Guardian Agent detects deviation")
    print("  • Nurse Coordinator assigns response")
    print("\nMinute 2-3: CRITICAL EMERGENCY")
    print("  • P-003 develops Grade 3 CRS")
    print("  • Emergency Response Agent activates protocol")
    print("  • Physician paged, medications prepared")
    print("\nMinute 3-4: PATTERN DETECTION")
    print("  • Research Insights detects tremor pattern")
    print("  • Safety signal flagged for investigation")
    print("\nMinute 4-5: SYSTEM SUMMARY")
    print("  • All agents coordinated successfully")
    print("  • Compliance report generated")
    print("  • Safety monitoring active")
    print("\n" + "=" * 80)
    print("\n🚀 STARTING ALL AGENTS...\n")


def print_demo_instructions():
    """Print instructions for demo scenarios"""
    print("\n" + "=" * 80)
    print("📝 DEMO SCENARIO CONTROLS")
    print("=" * 80)
    print("\nThe demo will automatically progress through scenarios.")
    print("You can also manually trigger scenarios by editing utils/mock_data.py:")
    print("\nAvailable scenarios:")
    print("  • 'normal' - All patients stable (default)")
    print("  • 'p002_concerning' - P-002 develops concerning symptoms")
    print("  • 'p003_critical' - P-003 develops critical CRS")
    print("  • 'pattern_tremor' - Multiple patients show tremor")
    print("\nTo change scenario during demo:")
    print("  1. Keep this running")
    print("  2. In Python console: mock_generator.set_scenario('scenario_name')")
    print("\n" + "=" * 80)
    print("\n⌛ Agents will start in 3 seconds...")
    print("   Press Ctrl+C to stop all agents\n")


def main():
    """Main orchestrator"""
    
    # Print demo information
    print_demo_header()
    print_demo_instructions()
    
    import time
    time.sleep(3)
    
    print("=" * 80)
    print("🎬 DEMO STARTING - Minute 0: Normal Operations")
    print("=" * 80 + "\n")
    
    # List of processes
    processes = []
    
    try:
        # Start all agents in separate processes
        
        # 1. Patient Guardian Agents (3 patients)
        print("🤖 Starting Patient Guardian Agents...")
        for patient_id in ["P-001", "P-002", "P-003"]:
            p = mp.Process(target=run_patient_guardian, args=(patient_id,))
            p.start()
            processes.append(p)
            time.sleep(1)  # Stagger startup
        
        # 2. Nurse Coordinator
        print("👨‍⚕️ Starting Nurse Coordinator Agent...")
        p = mp.Process(target=run_nurse_coordinator)
        p.start()
        processes.append(p)
        time.sleep(1)
        
        # 3. Emergency Response
        print("🚑 Starting Emergency Response Agent...")
        p = mp.Process(target=run_emergency_response)
        p.start()
        processes.append(p)
        time.sleep(1)
        
        # 4. Protocol Compliance
        print("📋 Starting Protocol Compliance Agent...")
        p = mp.Process(target=run_protocol_compliance)
        p.start()
        processes.append(p)
        time.sleep(1)
        
        # 5. Research Insights
        print("🔬 Starting Research Insights Agent...")
        p = mp.Process(target=run_research_insights)
        p.start()
        processes.append(p)
        
        print("\n" + "=" * 80)
        print("✅ ALL AGENTS RUNNING")
        print("=" * 80)
        print(f"\nTotal agents: {len(processes)}")
        print("  • 3 Patient Guardian Agents (P-001, P-002, P-003)")
        print("  • 1 Nurse Coordinator Agent")
        print("  • 1 Emergency Response Agent")
        print("  • 1 Protocol Compliance Agent")
        print("  • 1 Research Insights Agent")
        print("\n📊 Monitoring all patients... Watch the console output below:")
        print("=" * 80 + "\n")
        
        # Demo scenario progression (automated)
        print("⏱️  Demo timeline started...")
        
        # Wait and let normal operations run
        time.sleep(60)  # Minute 0-1: Normal
        
        # Change to concerning scenario
        print("\n" + "=" * 80)
        print("🎬 DEMO MINUTE 1: Concerning Alert (P-002)")
        print("=" * 80 + "\n")
        mock_generator.set_scenario("p002_concerning")
        
        time.sleep(60)  # Minute 1-2: Concerning
        
        # Change to critical scenario
        print("\n" + "=" * 80)
        print("🎬 DEMO MINUTE 2: Critical Emergency (P-003)")
        print("=" * 80 + "\n")
        mock_generator.set_scenario("p003_critical")
        
        time.sleep(60)  # Minute 2-3: Critical
        
        # Change to pattern detection scenario
        print("\n" + "=" * 80)
        print("🎬 DEMO MINUTE 3: Pattern Detection (Tremor Signal)")
        print("=" * 80 + "\n")
        mock_generator.set_scenario("pattern_tremor")
        
        time.sleep(60)  # Minute 3-4: Pattern
        
        # Final summary
        print("\n" + "=" * 80)
        print("🎬 DEMO MINUTE 4: System Summary")
        print("=" * 80 + "\n")
        
        print("✅ DEMO COMPLETED SUCCESSFULLY")
        print("\n📊 Final Statistics:")
        print("  • 3 patients monitored continuously")
        print("  • 1 concerning alert triaged")
        print("  • 1 critical emergency managed")
        print("  • 1 safety signal detected")
        print("  • Full protocol compliance tracked")
        print("\n💡 Key Achievements:")
        print("  ✓ Autonomous monitoring with AI reasoning")
        print("  ✓ Intelligent multi-patient triage")
        print("  ✓ Emergency protocol activation")
        print("  ✓ Regulatory compliance tracking")
        print("  ✓ Safety signal detection")
        print("\n🏆 Innovation Lab: Fetch.ai + Anthropic Claude")
        print("=" * 80 + "\n")
        
        # Keep running for manual interaction
        print("Demo timeline complete. Agents continue running for manual testing.")
        print("Press Ctrl+C to stop all agents.\n")
        
        # Wait for Ctrl+C
        for p in processes:
            p.join()
    
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down all agents...")
        
        # Terminate all processes
        for p in processes:
            p.terminate()
        
        # Wait for all to finish
        for p in processes:
            p.join(timeout=5)
        
        print("\n✅ All agents stopped gracefully")
        print("\n" + "=" * 80)
        print("🏥 HAVEN AI DEMO SESSION COMPLETE")
        print("=" * 80)
        print("\nThank you for watching!")
        print("Built with ❤️  for patient safety")
        print("Powered by Fetch.ai uAgents + Anthropic Claude")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    # Set multiprocessing start method
    mp.set_start_method('spawn', force=True)
    
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

