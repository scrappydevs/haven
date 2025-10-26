# LiveKit Voice AI Options - Comparison

## **Why Do I Need Extra Services?**

**Short Answer:** LiveKit is a **framework/orchestrator** for voice AI, not the AI itself. You need to bring your own STT/LLM/TTS providers.

Think of it like this:
- **LiveKit** = Railway tracks + train system
- **AI Services** = The actual trains carrying passengers

---

## **Option 1: OpenAI Realtime API (✅ RECOMMENDED)**

### What You Need:
- ✅ LiveKit (orchestration)
- ✅ OpenAI (STT + LLM + TTS in one)

### Setup Complexity: **Easy** ⭐⭐⭐⭐⭐
- 2 accounts to create
- 2 API keys to manage
- 1 AI service to configure

### Architecture:
```
Patient → LiveKit → OpenAI Realtime API → Patient
                    (does everything)
```

### Cost per 5-min intake: **~$0.16**

### Pros:
- ✅ **Simplest setup** (only 2 services)
- ✅ **Single API call** (lower latency)
- ✅ **Built-in interruption handling**
- ✅ **Fewer failure points**
- ✅ **Good voice quality**

### Cons:
- ❌ Uses GPT-4o (not Claude)
- ❌ No medical-specific STT models
- ❌ Slightly more expensive

---

## **Option 2: Separate STT-LLM-TTS Pipeline**

### What You Need:
- ✅ LiveKit (orchestration)
- ✅ Deepgram (speech-to-text)
- ✅ Claude/Anthropic (reasoning)
- ✅ Cartesia (text-to-speech)

### Setup Complexity: **Complex** ⭐⭐
- 4 accounts to create
- 4 API keys to manage
- 3 AI services to configure

### Architecture:
```
Patient → LiveKit → Deepgram → Claude → Cartesia → Patient
                    (STT)      (LLM)    (TTS)
```

### Cost per 5-min intake: **~$0.10**

### Pros:
- ✅ **Use Claude** (better for medical reasoning)
- ✅ **Medical-optimized STT** (Deepgram nova-2-medical)
- ✅ **More control** over each component
- ✅ **Slightly cheaper**

### Cons:
- ❌ More complex setup (4 services)
- ❌ More potential failure points
- ❌ Higher latency (3 hops)
- ❌ More debugging needed

---

## **Why LiveKit Doesn't Provide AI Itself**

LiveKit focuses on what they're best at:
- ✅ Real-time WebRTC infrastructure
- ✅ Low-latency audio/video streaming
- ✅ NAT traversal and connection management
- ✅ Orchestrating AI services together

They let you choose the best AI providers for your use case rather than lock you into one option.

---

## **Comparison Table**

| Feature | OpenAI Realtime | Separate Pipeline |
|---------|----------------|-------------------|
| **API Keys Needed** | 2 (LiveKit + OpenAI) | 4 (LiveKit + Deepgram + Anthropic + Cartesia) |
| **Setup Time** | 15 minutes | 30-45 minutes |
| **Latency** | Lower (1 hop) | Higher (3 hops) |
| **Cost per intake** | $0.16 | $0.10 |
| **LLM** | GPT-4o | Claude (better for medical) |
| **Medical STT** | No | Yes (Deepgram medical) |
| **Debugging** | Easier (1 service) | Harder (3 services) |
| **Voice Quality** | Good | Excellent |
| **Interruption Handling** | Built-in | Built-in |

---

## **My Recommendation**

### **Start with OpenAI Realtime API** for these reasons:

1. **Get it working faster** - Only 2 API keys needed
2. **Simpler debugging** - Fewer moving parts
3. **Good enough quality** - GPT-4o is excellent for medical conversations
4. **Easy to switch later** - If you need Claude, you can swap to Option 2

### **Switch to Separate Pipeline if:**
- You absolutely need Claude's medical reasoning
- Cost is critical ($0.06 savings per intake)
- You need Deepgram's medical-specific transcription
- You have time for more complex setup

---

## **What I Implemented**

I've updated the code to use **OpenAI Realtime API** (Option 1) because:
- You're building an MVP
- Simpler is better for initial testing
- You can always switch to Claude later

The files now reflect this simpler approach:
- `backend/app/agents/intake_agent.py` - Uses OpenAI Realtime
- `backend/requirements.txt` - Only OpenAI plugin
- `backend/.env.local.template` - Only needs OpenAI key

---

## **FAQ**

**Q: Can I use Claude with LiveKit?**
A: Yes! Use Option 2 (separate pipeline). Just need to add Deepgram/Cartesia.

**Q: Is OpenAI good enough for medical use?**
A: Yes, GPT-4o is excellent. But Claude may be slightly better for complex medical reasoning.

**Q: Can I switch later?**
A: Absolutely! Just change a few lines in the agent code.

**Q: Which voice sounds better?**
A: Cartesia (Option 2) has slightly more natural voices. OpenAI (Option 1) is still very good.

---

## **Quick Decision Guide**

Choose **OpenAI Realtime** if:
- ✅ You want to test quickly
- ✅ You're okay with GPT-4o
- ✅ Simplicity matters more than $0.06 savings

Choose **Separate Pipeline** if:
- ✅ You must use Claude
- ✅ You need medical-specific STT
- ✅ You're comfortable managing multiple services
- ✅ Every penny counts
