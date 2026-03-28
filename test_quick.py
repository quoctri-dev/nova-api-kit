"""Quick test — verify Gemini API calls work for all 3 use cases."""
import os, json, sys

# Load key from cc-scripts/.env
env_path = os.path.expanduser("~/Documents/claude-memory/cc-scripts/.env")
for line in open(env_path):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ.get("GOOGLE_AI_API_KEY")
if not API_KEY:
    print("FAIL: GOOGLE_AI_API_KEY not found")
    sys.exit(1)

from google import genai
client = genai.Client(api_key=API_KEY)
MODEL = "gemini-2.5-flash"
passed = 0
total = 3


def test_call(name, prompt):
    global passed
    print(f"\n{'='*50}")
    print(f"TEST: {name}")
    print(f"{'='*50}")
    try:
        resp = client.models.generate_content(model=MODEL, contents=prompt)
        raw = resp.text.strip()
        print(f"Raw ({len(raw)} chars): {raw[:200]}...")

        # Strip markdown fences if any
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]

        data = json.loads(raw)
        print(f"JSON parse: OK")
        print(f"Keys: {list(data.keys())}")
        passed += 1
        return data
    except json.JSONDecodeError as e:
        print(f"JSON parse FAIL: {e}")
        print(f"Raw output: {raw[:500]}")
    except Exception as e:
        print(f"API FAIL: {type(e).__name__}: {e}")


# --- Test 1: Text Analyzer ---
test_call("Text Analyzer", """Analyze this text and return ONLY a valid JSON object (no markdown, no code fences):
{"summary": "2-3 sentence summary", "sentiment": "positive|negative|neutral|mixed", "confidence": 0.0, "key_entities": ["max 5"], "language": "detected language", "topics": ["max 3"]}

Text:
Apple announced its new M4 chip today, promising 50% faster CPU performance and 2x GPU throughput compared to M3. The chip will power the next MacBook Pro lineup starting in November. Analysts are optimistic about Apple's continued silicon leadership.""")

# --- Test 2: Data Extractor ---
test_call("Data Extractor", """Extract structured data from this text. Return ONLY valid JSON matching this schema (no markdown):
{"name":"string","email":"string","phone":"string","company":"string","role":"string"}

Text:
Hi, I'm Sarah Chen, VP of Engineering at TechFlow Inc. You can reach me at sarah.chen@techflow.io or call 415-555-0142. Looking forward to our partnership discussion.""")

# --- Test 3: Content Generator (plain text, not JSON) ---
print(f"\n{'='*50}")
print("TEST: Content Generator")
print(f"{'='*50}")
try:
    resp = client.models.generate_content(model=MODEL, contents="""Generate a blog post about: Benefits of API abstraction layers
Tone: professional
Length: Short (~100 words)
Return the content directly. No meta-commentary, no markdown code fences.""")
    text = resp.text.strip()
    print(f"Output ({len(text)} chars): {text[:300]}...")
    if len(text) > 20:
        print("Content Generator: OK")
        passed += 1
    else:
        print("Content Generator: FAIL (too short)")
except Exception as e:
    print(f"API FAIL: {type(e).__name__}: {e}")

# --- Summary ---
print(f"\n{'='*50}")
print(f"RESULT: {passed}/{total} passed")
print(f"{'='*50}")
sys.exit(0 if passed == total else 1)
