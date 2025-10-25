"""
Claude AI client wrapper for clinical reasoning
"""
import os
import json
from typing import Dict, Optional
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ClaudeClient:
    """Wrapper for Anthropic Claude API with clinical reasoning capabilities"""
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("⚠️  ANTHROPIC_API_KEY not found in environment. Set it in .env file.")
            print("   Agent will use rule-based fallback logic instead of AI reasoning.")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=api_key)
            print(f"✅ Claude AI client initialized (key: ...{api_key[-8:]})")
    
    def assess_severity(
        self,
        patient_id: str,
        current_hr: int,
        baseline_hr: int,
        current_rr: int,
        baseline_rr: int,
        crs_score: float,
        tremor_detected: bool,
        attention_score: float = 1.0
    ) -> Dict[str, any]:
        """
        Assess patient severity using Claude AI
        
        Returns:
            {
                "severity": "NORMAL" | "CONCERNING" | "CRITICAL",
                "reasoning": "Clinical explanation...",
                "concerns": ["list", "of", "concerns"],
                "confidence": 0.0-1.0,
                "recommended_actions": ["action1", "action2"]
            }
        """
        if not self.client:
            return self._fallback_assessment(current_hr, baseline_hr, current_rr, baseline_rr, crs_score, tremor_detected)
        
        # Calculate deviations
        hr_deviation = current_hr - baseline_hr
        hr_deviation_pct = (hr_deviation / baseline_hr) * 100
        rr_deviation = current_rr - baseline_rr
        rr_deviation_pct = (rr_deviation / baseline_rr) * 100
        
        prompt = f"""You are a clinical monitoring AI for CAR-T cell therapy patients. Analyze this patient data and assess severity.

**Patient ID:** {patient_id}

**Current Vitals:**
- Heart Rate: {current_hr} bpm (baseline: {baseline_hr} bpm, deviation: {hr_deviation:+d} bpm, {hr_deviation_pct:+.1f}%)
- Respiratory Rate: {current_rr} breaths/min (baseline: {baseline_rr} breaths/min, deviation: {rr_deviation:+d}, {rr_deviation_pct:+.1f}%)
- CRS Score: {crs_score:.2f} (0.0-1.0 scale)
- Tremor Detected: {tremor_detected}
- Attention Score: {attention_score:.2f} (1.0 = fully alert)

**Clinical Context:**
- CAR-T cell therapy patients are at risk for Cytokine Release Syndrome (CRS)
- CRS typically appears 1-14 days post-infusion
- Early symptoms: fever, tachycardia, hypotension, hypoxia
- Neurological symptoms (tremor, altered attention) may indicate ICANS

**Severity Levels:**
- **NORMAL**: All metrics within 15% of baseline, CRS < 0.5, no concerning trends
- **CONCERNING**: Any metric 15-30% deviation OR CRS 0.5-0.7 OR mild neurological symptoms
- **CRITICAL**: Any metric >30% deviation OR CRS > 0.7 OR severe neurological symptoms OR rapid deterioration

**Important:** Consider that sudden changes are more dangerous than gradual ones. A patient who was stable 5 minutes ago but now shows rapid HR increase is more concerning than someone with chronically elevated HR.

**Your Task:**
Assess severity (NORMAL/CONCERNING/CRITICAL) and provide clinical reasoning in 2-3 sentences.

Respond in JSON format:
{{
  "severity": "NORMAL" | "CONCERNING" | "CRITICAL",
  "reasoning": "Brief clinical explanation (2-3 sentences)",
  "concerns": ["specific concern 1", "specific concern 2"],
  "confidence": 0.0-1.0,
  "recommended_actions": ["recommended action 1", "recommended action 2"]
}}"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Sonnet 3.5 v2
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse JSON from Claude's response
            response_text = response.content[0].text
            
            # Find JSON in response (Claude sometimes adds explanation around it)
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]
            
            result = json.loads(json_str)
            
            # Validate severity level
            if result.get("severity") not in ["NORMAL", "CONCERNING", "CRITICAL"]:
                print(f"⚠️  Invalid severity from Claude: {result.get('severity')}, using fallback")
                return self._fallback_assessment(current_hr, baseline_hr, current_rr, baseline_rr, crs_score, tremor_detected)
            
            return result
            
        except Exception as e:
            print(f"❌ Claude API error: {e}")
            return self._fallback_assessment(current_hr, baseline_hr, current_rr, baseline_rr, crs_score, tremor_detected)
    
    def _fallback_assessment(
        self,
        current_hr: int,
        baseline_hr: int,
        current_rr: int,
        baseline_rr: int,
        crs_score: float,
        tremor_detected: bool
    ) -> Dict[str, any]:
        """Rule-based fallback when Claude API unavailable"""
        
        hr_deviation_pct = abs((current_hr - baseline_hr) / baseline_hr) * 100
        rr_deviation_pct = abs((current_rr - baseline_rr) / baseline_rr) * 100
        
        # Critical conditions
        if crs_score > 0.7 or hr_deviation_pct > 30 or rr_deviation_pct > 30:
            return {
                "severity": "CRITICAL",
                "reasoning": f"Critical CRS score ({crs_score:.2f}) or vital signs >30% from baseline. Immediate clinical assessment required.",
                "concerns": [
                    f"CRS score: {crs_score:.2f}" if crs_score > 0.7 else None,
                    f"HR deviation: {hr_deviation_pct:.1f}%" if hr_deviation_pct > 30 else None,
                    f"RR deviation: {rr_deviation_pct:.1f}%" if rr_deviation_pct > 30 else None,
                    "Tremor detected" if tremor_detected else None
                ],
                "confidence": 0.8,
                "recommended_actions": [
                    "Notify physician immediately",
                    "Increase monitoring frequency to q5min",
                    "Prepare for potential intervention"
                ]
            }
        
        # Concerning conditions
        if crs_score > 0.5 or hr_deviation_pct > 15 or rr_deviation_pct > 15 or tremor_detected:
            return {
                "severity": "CONCERNING",
                "reasoning": f"Elevated CRS score ({crs_score:.2f}) or vital signs 15-30% from baseline. Enhanced monitoring recommended.",
                "concerns": [
                    f"CRS score: {crs_score:.2f}" if crs_score > 0.5 else None,
                    f"HR deviation: {hr_deviation_pct:.1f}%" if hr_deviation_pct > 15 else None,
                    f"RR deviation: {rr_deviation_pct:.1f}%" if rr_deviation_pct > 15 else None,
                    "Tremor detected" if tremor_detected else None
                ],
                "confidence": 0.7,
                "recommended_actions": [
                    "Increase monitoring to q15min",
                    "Notify charge nurse",
                    "Continue close observation"
                ]
            }
        
        # Normal
        return {
            "severity": "NORMAL",
            "reasoning": f"All vitals within acceptable range. HR {current_hr} bpm (baseline {baseline_hr}), RR {current_rr} (baseline {baseline_rr}), CRS {crs_score:.2f}.",
            "concerns": [],
            "confidence": 0.9,
            "recommended_actions": ["Continue routine monitoring"]
        }


# Global client instance
claude_client = ClaudeClient()

