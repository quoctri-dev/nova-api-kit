"""
NoVa API Kit — AI API Integration Toolkit
Product #4 | novasentio.com
Demonstrates: Provider swap, self-healing, structured output
"""

import streamlit as st
import os
import json
import time
from typing import Optional

# ─── PAGE CONFIG ─────────────────────────────────────────
st.set_page_config(
    page_title="NoVa API Kit",
    page_icon=":material/bolt:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS (dark mode — UX-REFERENCE v1) ───────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Plus Jakarta Sans', sans-serif; letter-spacing: -0.02em; }
.stApp { background: linear-gradient(135deg, #0f0f0f, #1a1a2e); }
div[data-testid="stSidebar"] { background: #1a1a1a; border-right: 1px solid #333; }
.stButton>button {
    border-radius: 8px; transition: all 0.2s ease;
    background: #06b6d4; color: white; border: none; font-weight: 500;
}
.stButton>button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(6,182,212,0.3); }
div[data-testid="stMetric"] {
    background: #1a1a1a; border: 1px solid #333;
    border-radius: 12px; padding: 16px;
}
div[data-testid="stExpander"] {
    background: #0d1117; border: 1px solid #30363d; border-radius: 8px;
}
</style>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# CONFIG (swap here) — Stage 1: all-in-one dict
# Stage 2: tách config.py + providers/ folder
# ═══════════════════════════════════════════════════════════
PROVIDERS_CONFIG = {
    "gemini": {
        "name": "Google Gemini",
        "model": "gemini-2.5-flash",
        "env_key": "GOOGLE_AI_API_KEY",
    },
    "claude": {
        "name": "Anthropic Claude",
        "model": "claude-haiku-4-5-20251001",
        "env_key": "ANTHROPIC_API_KEY",
    },
}


# ═══════════════════════════════════════════════════════════
# ADAPTER (abstract here) — each provider = 1 function
# Swap provider = swap function, business logic untouched
# ═══════════════════════════════════════════════════════════
def _call_gemini(prompt: str, api_key: str, model: str) -> str:
    from google import genai
    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(model=model, contents=prompt)
    return resp.text


def _call_claude(prompt: str, api_key: str, model: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model, max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


_ADAPTERS = {"gemini": _call_gemini, "claude": _call_claude}


# ═══════════════════════════════════════════════════════════
# SELF-HEALING ENGINE — retry + fallback + diagnose
# Pattern: dev-delivery M2 (SH1-SH5, V6-V7)
# ═══════════════════════════════════════════════════════════
def _classify_error(e: Exception) -> dict:
    """Error → what / why / fix / retryable (V6-V7)."""
    s = str(e).lower()
    if "rate" in s or "429" in s:
        return {"what": "Rate limited", "why": "Too many requests", "fix": "Wait and retry", "retry": True}
    if "auth" in s or "401" in s or "key" in s or "permission" in s:
        return {"what": "Auth failed", "why": "Invalid or missing API key", "fix": "Check your API key in sidebar", "retry": False}
    if "timeout" in s or "connect" in s or "network" in s:
        return {"what": "Connection error", "why": "Network issue or service down", "fix": "Check internet connection", "retry": True}
    if "quota" in s or "billing" in s or "exceeded" in s:
        return {"what": "Quota exceeded", "why": "Usage limit or billing issue", "fix": "Check provider billing dashboard", "retry": False}
    if "not found" in s or "404" in s:
        return {"what": "Model not found", "why": "Model ID may have changed", "fix": "Check model availability", "retry": False}
    return {"what": f"{type(e).__name__}", "why": str(e)[:120], "fix": "Check logs below", "retry": True}


def call_ai(prompt: str, provider: str, api_key: str,
            fallback_provider: Optional[str] = None,
            fallback_key: Optional[str] = None,
            max_retries: int = 3) -> dict:
    """
    Self-healing AI call: retry → fallback → diagnose.
    Returns {"text", "provider_used", "heal_log"}.
    """
    heal_log: list[str] = []
    cfg = PROVIDERS_CONFIG[provider]

    # ── Primary provider with retry (SH4: exponential backoff) ──
    for attempt in range(1, max_retries + 1):
        try:
            heal_log.append(f":material/sync: Attempt {attempt}/{max_retries} → {cfg['name']} ({cfg['model']})")
            result = _ADAPTERS[provider](prompt, api_key, cfg["model"])
            heal_log.append(f":material/check_circle: Success on attempt {attempt}")
            return {"text": result, "provider_used": provider, "heal_log": heal_log}
        except Exception as e:
            ec = _classify_error(e)
            heal_log.append(f":material/warning: {ec['what']} — {ec['why']}")
            if ec["retry"] and attempt < max_retries:
                delay = 2 ** (attempt - 1)
                heal_log.append(f":material/hourglass_empty: Backoff {delay}s...")
                time.sleep(delay)
            elif not ec["retry"]:
                heal_log.append(f":material/block: Non-retryable — skipping retries")
                break

    # ── Fallback provider (SH5) ──
    if fallback_provider and fallback_key:
        fb_cfg = PROVIDERS_CONFIG[fallback_provider]
        heal_log.append(f":material/swap_horiz: Fallback → {fb_cfg['name']} ({fb_cfg['model']})")
        try:
            result = _ADAPTERS[fallback_provider](prompt, fallback_key, fb_cfg["model"])
            heal_log.append(f":material/check_circle: Fallback success")
            return {"text": result, "provider_used": fallback_provider, "heal_log": heal_log}
        except Exception as e:
            ec = _classify_error(e)
            heal_log.append(f":material/error: Fallback failed — {ec['what']}: {ec['why']}")

    heal_log.append(":material/error: All providers exhausted")
    return {"text": None, "provider_used": None, "heal_log": heal_log}


# ═══════════════════════════════════════════════════════════
# PROMPTS — business logic (never touches provider directly)
# ═══════════════════════════════════════════════════════════
PROMPTS = {
    "analyze": """Analyze this text and return ONLY a valid JSON object (no markdown, no code fences):
{{"summary": "2-3 sentence summary", "sentiment": "positive|negative|neutral|mixed", "confidence": 0.0, "key_entities": ["max 5"], "language": "detected language", "topics": ["max 3"]}}

Text:
{text}""",

    "extract": """Extract structured data from this text. Return ONLY valid JSON matching this schema (no markdown):
{schema}

Text:
{text}""",

    "generate": """Generate a {format} about: {topic}
Tone: {tone}
Length: {length}
Return the content directly. No meta-commentary, no markdown code fences.""",
}

SCHEMAS = {
    "Contact Info": '{{"name":"string","email":"string","phone":"string","company":"string","role":"string"}}',
    "Invoice Data": '{{"vendor":"string","invoice_no":"string","date":"string","items":[{{"desc":"string","amount":0}}],"total":0,"currency":"string"}}',
    "Product Info": '{{"name":"string","price":0,"currency":"string","features":["string"],"category":"string"}}',
}


# ═══════════════════════════════════════════════════════════
# SIDEBAR — provider config + API keys
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### :material/tune: Configuration")

    primary = st.selectbox(
        "Primary Provider", list(PROVIDERS_CONFIG),
        format_func=lambda x: PROVIDERS_CONFIG[x]["name"],
    )
    fb_opts = [k for k in PROVIDERS_CONFIG if k != primary]
    fallback = st.selectbox(
        "Fallback Provider", ["none"] + fb_opts,
        format_func=lambda x: "None" if x == "none" else PROVIDERS_CONFIG[x]["name"],
    )

    st.markdown("---")
    st.markdown("### :material/key: API Keys")
    st.caption("Keys stay in your browser. Set here or via .env")

    api_keys = {}
    for pid, pcfg in PROVIDERS_CONFIG.items():
        env_val = os.getenv(pcfg["env_key"], "")
        api_keys[pid] = st.text_input(
            pcfg["name"], value=env_val, type="password", key=f"k_{pid}",
        )

    st.markdown("---")
    st.caption(":material/bolt: **NoVa API Kit** v1.0")
    st.caption("Provider-agnostic · Self-healing · Swap-ready")
    st.caption("[novasentio.com](https://novasentio.com)")


# ═══════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════
st.markdown("# :material/bolt: NoVa API Kit")
st.caption("AI API Integration Toolkit — swap providers in 1 click, auto-retry & fallback, structured output")


# ═══════════════════════════════════════════════════════════
# SHARED DISPLAY HELPER
# ═══════════════════════════════════════════════════════════
def _show_result(result: dict):
    """Display heal log + provider badge."""
    with st.expander(":material/healing: Self-Healing Log", expanded=False):
        for line in result["heal_log"]:
            st.markdown(line)
        if result["provider_used"]:
            pname = PROVIDERS_CONFIG[result["provider_used"]]["name"]
            st.success(f"Served by: {pname}")
        elif result["text"] is None:
            st.error("All providers failed. Check API keys and try again.")


def _get_keys():
    """Return (primary_key, fallback_provider_or_none, fallback_key_or_none)."""
    pk = api_keys.get(primary, "")
    fb = fallback if fallback != "none" else None
    fk = api_keys.get(fallback, "") if fb else None
    return pk, fb, fk


# ═══════════════════════════════════════════════════════════
# USE-CASE TABS
# ═══════════════════════════════════════════════════════════
tab = st.segmented_control(
    "Use Case",
    [":material/analytics: Text Analyzer", ":material/find_in_page: Data Extractor", ":material/edit_note: Content Generator"],
    default=":material/analytics: Text Analyzer",
)

# ── TAB 1: TEXT ANALYZER ─────────────────────────────────
if tab == ":material/analytics: Text Analyzer":
    st.markdown("#### Analyze any text → structured insights")
    text_in = st.text_area("Paste text to analyze", height=150,
                           placeholder="Paste an article, email, review, report...")

    if st.button(":material/play_arrow: Analyze", type="primary", use_container_width=True):
        if not text_in.strip():
            st.warning("Please enter some text.")
        else:
            pk, fb, fk = _get_keys()
            if not pk:
                st.error(f"No API key for {PROVIDERS_CONFIG[primary]['name']}. Set in sidebar.")
            else:
                prompt = PROMPTS["analyze"].format(text=text_in[:4000])
                with st.spinner("Analyzing..."):
                    res = call_ai(prompt, primary, pk, fb, fk)
                _show_result(res)
                if res["text"]:
                    try:
                        # Strip markdown fences if any
                        raw = res["text"].strip()
                        if raw.startswith("```"):
                            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
                        data = json.loads(raw)

                        cols = st.columns(3)
                        cols[0].metric("Sentiment", data.get("sentiment", "—").title())
                        cols[1].metric("Confidence", f"{float(data.get('confidence', 0)):.0%}")
                        cols[2].metric("Language", data.get("language", "—"))

                        st.markdown("**Summary**")
                        st.info(data.get("summary", "No summary returned"))

                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("**Key Entities**")
                            for e in data.get("key_entities", []):
                                st.markdown(f"- {e}")
                        with c2:
                            st.markdown("**Topics**")
                            for t in data.get("topics", []):
                                st.markdown(f"- {t}")
                    except (json.JSONDecodeError, ValueError):
                        st.warning("AI returned non-JSON. Raw output:")
                        st.code(res["text"])

# ── TAB 2: DATA EXTRACTOR ───────────────────────────────
elif tab == ":material/find_in_page: Data Extractor":
    st.markdown("#### Extract structured data from unstructured text")
    schema_type = st.selectbox("Extraction Schema", list(SCHEMAS))
    text_in = st.text_area("Paste unstructured text", height=150,
                           placeholder="Paste an email, invoice, product listing...")

    if st.button(":material/play_arrow: Extract", type="primary", use_container_width=True):
        if not text_in.strip():
            st.warning("Please enter text to extract from.")
        else:
            pk, fb, fk = _get_keys()
            if not pk:
                st.error(f"No API key for {PROVIDERS_CONFIG[primary]['name']}. Set in sidebar.")
            else:
                prompt = PROMPTS["extract"].format(text=text_in[:4000], schema=SCHEMAS[schema_type])
                with st.spinner("Extracting..."):
                    res = call_ai(prompt, primary, pk, fb, fk)
                _show_result(res)
                if res["text"]:
                    try:
                        raw = res["text"].strip()
                        if raw.startswith("```"):
                            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
                        data = json.loads(raw)
                        st.json(data)
                        st.download_button(
                            ":material/download: Download JSON",
                            json.dumps(data, indent=2, ensure_ascii=False),
                            file_name="extracted.json",
                            mime="application/json",
                        )
                    except (json.JSONDecodeError, ValueError):
                        st.warning("AI returned non-JSON. Raw output:")
                        st.code(res["text"])

# ── TAB 3: CONTENT GENERATOR ────────────────────────────
elif tab == ":material/edit_note: Content Generator":
    st.markdown("#### Generate content with AI")
    c1, c2 = st.columns(2)
    with c1:
        topic = st.text_input("Topic", placeholder="e.g., Benefits of AI automation for SMBs")
        tone = st.selectbox("Tone", ["Professional", "Casual", "Technical", "Creative", "Persuasive"])
    with c2:
        fmt = st.selectbox("Format", ["Blog post", "Email", "Social media post", "Product description", "Executive summary"])
        length = st.selectbox("Length", ["Short (~100 words)", "Medium (~250 words)", "Long (~500 words)"])

    if st.button(":material/play_arrow: Generate", type="primary", use_container_width=True):
        if not topic.strip():
            st.warning("Please enter a topic.")
        else:
            pk, fb, fk = _get_keys()
            if not pk:
                st.error(f"No API key for {PROVIDERS_CONFIG[primary]['name']}. Set in sidebar.")
            else:
                prompt = PROMPTS["generate"].format(topic=topic, tone=tone.lower(), format=fmt.lower(), length=length)
                with st.spinner("Generating..."):
                    res = call_ai(prompt, primary, pk, fb, fk)
                _show_result(res)
                if res["text"]:
                    st.markdown(res["text"])
                    st.download_button(
                        ":material/download: Download Text",
                        res["text"],
                        file_name="generated.txt",
                        mime="text/plain",
                    )

# ═══════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════
st.markdown("---")
st.columns(3)[1].caption("Built by [NoVa](https://novasentio.com) — AI Integration Patterns")
