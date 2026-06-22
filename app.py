import streamlit as st
import anthropic
import json
import re
import zipfile
import io

st.set_page_config(
    page_title="RegCoPilot – AI Compliance Assistant",
    page_icon="🔬",
    layout="wide",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #f8f9fb; }
  .hero { background: linear-gradient(135deg, #1a2e5a 0%, #0d6efd 100%);
          color: white; padding: 1.1rem 1.75rem; border-radius: 10px;
          margin-bottom: 1.25rem; display:flex; align-items:center; gap:1rem; }
  .hero h1 { font-size: 1.4rem; font-weight: 700; margin: 0 0 0.15rem; }
  .hero p  { font-size: 0.82rem; opacity: 0.82; margin: 0; }
  .card    { background: white; border-radius: 10px; padding: 1.25rem 1.5rem;
             margin-bottom: 1rem; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
  .card h3 { margin: 0 0 0.75rem; font-size: 1rem; color: #1a2e5a; }
  .sample-card { background: white; border: 1.5px solid #e5e7eb; border-radius: 10px;
                 padding: 1rem 1.1rem 0.85rem; height: 130px;
                 box-shadow: 0 1px 3px rgba(0,0,0,0.06); display:flex;
                 flex-direction:column; justify-content:space-between; }
  .sample-card-inner { display:flex; align-items:flex-start; gap:0.75rem; }
  .sample-card h4 { margin: 0 0 0.2rem; color: #1a2e5a; font-size: 0.84rem;
                    font-weight: 600; line-height:1.3; }
  .sample-card p  { margin: 0; color: #6b7280; font-size: 0.76rem; }
  .badge-green  { background:#d1fae5; color:#065f46; padding:3px 10px;
                  border-radius:999px; font-size:0.82rem; font-weight:600; }
  .badge-amber  { background:#fef3c7; color:#92400e; padding:3px 10px;
                  border-radius:999px; font-size:0.82rem; font-weight:600; }
  .badge-red    { background:#fee2e2; color:#991b1b; padding:3px 10px;
                  border-radius:999px; font-size:0.82rem; font-weight:600; }
  .score-box    { text-align:center; padding:1.5rem; border-radius:10px; }
  .score-green  { background:#d1fae5; border: 2px solid #34d399; }
  .score-amber  { background:#fef3c7; border: 2px solid #fbbf24; }
  .score-red    { background:#fee2e2; border: 2px solid #f87171; }
  .score-num    { font-size:3rem; font-weight:800; line-height:1; }
  .score-label  { font-size:0.85rem; font-weight:600; margin-top:0.3rem; }
  .tag { display:inline-block; background:#e0e7ff; color:#3730a3;
         border-radius:6px; padding:2px 8px; font-size:0.8rem;
         margin:2px; font-weight:500; }
  footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Product SVG illustrations ─────────────────────────────────────────────────
SVG_SPRAY = """<svg width="44" height="68" viewBox="0 0 44 68" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="22" width="24" height="40" rx="5" fill="#0d6efd"/>
  <rect x="14" y="26" width="6" height="12" rx="2" fill="#ffffff" opacity="0.25"/>
  <rect x="18" y="8" width="10" height="16" rx="3" fill="#1a2e5a"/>
  <rect x="28" y="10" width="10" height="5" rx="2" fill="#1a2e5a"/>
  <rect x="36" y="8" width="3" height="3" rx="1" fill="#60a5fa"/>
  <circle cx="37" cy="5" r="1.2" fill="#93c5fd" opacity="0.7"/>
  <circle cx="40" cy="7" r="0.9" fill="#93c5fd" opacity="0.5"/>
  <circle cx="38" cy="2" r="0.7" fill="#93c5fd" opacity="0.4"/>
  <text x="22" y="52" text-anchor="middle" font-size="7" fill="white" font-family="Arial" font-weight="bold">AVON</text>
</svg>"""

SVG_PALETTE = """<svg width="54" height="48" viewBox="0 0 54 48" xmlns="http://www.w3.org/2000/svg">
  <rect x="3" y="6" width="48" height="36" rx="5" fill="#1a2e5a"/>
  <rect x="6" y="9" width="42" height="30" rx="3" fill="#2d3f6b"/>
  <circle cx="16" cy="20" r="7" fill="#f87171"/>
  <circle cx="27" cy="20" r="7" fill="#fbbf24"/>
  <circle cx="38" cy="20" r="7" fill="#f9a8d4"/>
  <circle cx="16" cy="20" r="4" fill="#ef4444" opacity="0.6"/>
  <circle cx="27" cy="20" r="4" fill="#f59e0b" opacity="0.6"/>
  <circle cx="38" cy="20" r="4" fill="#ec4899" opacity="0.6"/>
  <rect x="10" y="33" width="34" height="3" rx="1.5" fill="#60a5fa" opacity="0.3"/>
  <text x="27" y="36.5" text-anchor="middle" font-size="4.5" fill="#93c5fd" font-family="Arial">RIMMEL LONDON</text>
</svg>"""

SVG_MASCARA = """<svg width="32" height="72" viewBox="0 0 32 72" xmlns="http://www.w3.org/2000/svg">
  <rect x="7" y="30" width="18" height="36" rx="5" fill="#1a2e5a"/>
  <rect x="9" y="34" width="5" height="10" rx="1.5" fill="#ffffff" opacity="0.15"/>
  <rect x="7" y="24" width="18" height="8" rx="2" fill="#0d6efd"/>
  <rect x="11" y="4" width="10" height="22" rx="3" fill="#374151"/>
  <line x1="16" y1="4" x2="12" y2="2" stroke="#9ca3af" stroke-width="1.2" stroke-linecap="round"/>
  <line x1="16" y1="7" x2="11" y2="5" stroke="#9ca3af" stroke-width="1.2" stroke-linecap="round"/>
  <line x1="16" y1="10" x2="11" y2="9" stroke="#9ca3af" stroke-width="1.2" stroke-linecap="round"/>
  <line x1="16" y1="13" x2="11" y2="12" stroke="#9ca3af" stroke-width="1.2" stroke-linecap="round"/>
  <line x1="16" y1="4" x2="20" y2="2" stroke="#9ca3af" stroke-width="1.2" stroke-linecap="round"/>
  <line x1="16" y1="7" x2="21" y2="5" stroke="#9ca3af" stroke-width="1.2" stroke-linecap="round"/>
  <line x1="16" y1="10" x2="21" y2="9" stroke="#9ca3af" stroke-width="1.2" stroke-linecap="round"/>
  <line x1="16" y1="13" x2="21" y2="12" stroke="#9ca3af" stroke-width="1.2" stroke-linecap="round"/>
  <text x="16" y="56" text-anchor="middle" font-size="4" fill="white" font-family="Arial" font-weight="bold">MAX</text>
  <text x="16" y="62" text-anchor="middle" font-size="4" fill="white" font-family="Arial" font-weight="bold">FACTOR</text>
</svg>"""

SAMPLE_SVGS = [SVG_SPRAY, SVG_PALETTE, SVG_MASCARA]

# ── Sample Concepts ───────────────────────────────────────────────────────────
SAMPLE_CONCEPTS = [
    {
        "name": "Avon Skin So Soft – Original Dry Oil Spray",
        "category": "Body Oil Spray",
        "full_text": """Concept Name: Avon Skin So Soft, Original Dry Oil Spray

Insight: I just want my skin to feel soft and look healthy without having to spend ages rubbing in loads of greasy stuff. There's never enough time!

Reasons to believe: Infused with jojoba oil, known for its exceptional moisturizing and skin-softening properties, and vitamin E; absorbs quickly without a greasy feel; loads of people already love it.

Benefit: Finally, I can quickly get that hydrated, smooth, and glowing skin I want, so I feel good and my skin actually feels amazing, without any fuss.

Primary Claim: Achieve instantly soft, smooth, and glowing skin.

Discriminator: A lightweight, quick-drying oil spray, featuring jojoba oil as a hero ingredient, along with vitamin E, that instantly delivers lasting softness and a healthy glow.""",
    },
    {
        "name": "Rimmel London Sculpting Highlighter Palette – Coral Glow",
        "category": "Face Highlighter / Palette",
        "full_text": """Concept Name: Rimmel London Sculpting Highlighter Palette 3-tone, Coral Glow

Insight: "I want to look naturally sculpted and glowing without spending ages trying to figure out different products and techniques."

Reasons to believe: The long-lasting, blendable formula, containing Mica for luminosity and a smooth application, seamlessly integrates with skin, and the curated shades work together to create a natural-looking sculpted effect.

Benefit: Achieve a professional-looking sculpted and glowing complexion quickly and easily, ideal for both everyday wear and special occasions, leaving you feeling confident and effortlessly put-together, just like you've achieved that coveted "London look."

Discriminator: A 3-in-1 palette designed by Kate Moss, offering perfectly coordinated shades for highlighting, contouring, and blush in one easy-to-use kit.

Primary Claim: Achieve a professionally sculpted, radiant look with a simple, all-in-one palette.""",
    },
    {
        "name": "Max Factor Masterpiece Max Mascara",
        "category": "Eye Mascara",
        "full_text": """Concept Name: Max Factor Masterpiece Max

Insight: Ugh, I just want my lashes to look amazing without spending ages layering on mascara and then worrying it's going to smudge halfway through the day.

Reasons to believe: The clever brush design grabs every lash for even coverage, and the formula, with Acrylates Copolymer and Copernicia Cerifera Cera (Carnauba Wax) doing their thing, means no smudges or clumps, just seriously boosted volume that stays put.

Benefit: Imagine having bold, gorgeous lashes that look professionally done but take seconds, so you can feel totally confident without any of the usual mascara hassle.

Discriminator: A unique IFX wand and volume-boosting formula, featuring Acrylates Copolymer for film-forming volume and Copernicia Cerifera Cera (Carnauba Wax) for lash thickening and smooth application, delivers up to 4x thicker, defined lashes with just one swipe, even reaching those annoying inner corners.

Primary Claim: Get dramatically thicker, beautifully defined lashes that last all day with just one quick swipe. This high-impact, volumising mascara thickens lashes by up to 4 times for a vivid look.""",
    },
]

# ── Constants ─────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are RegCoPilot, an expert EU and UK cosmetics regulatory compliance AI assistant.
You analyse product concepts for compliance with EU Cosmetics Regulation 1223/2009 (and its UK equivalent UKCR),
COSING ingredient database requirements, and ASA/CAP advertising claims standards.

Always respond with valid JSON only — no markdown, no prose outside the JSON structure."""

ANALYSIS_PROMPT = """Analyse this cosmetics product concept for regulatory compliance. Return ONLY a JSON object with this exact structure:

{
  "product_name": "string",
  "product_category": "string (e.g. Eye Mascara)",
  "overall_score": number (0-100, where 100 = fully compliant),
  "overall_rag": "GREEN" | "AMBER" | "RED",
  "summary": "2-3 sentence plain-English summary of the compliance picture",
  "claims": [
    {
      "claim_text": "exact quote from the concept",
      "claim_type": "Performance" | "Ingredient" | "Sensory" | "Comparative",
      "rag": "GREEN" | "AMBER" | "RED",
      "issue": "brief description of the compliance issue, or 'No issues identified'",
      "action_required": "what the brand team must do, or 'None'"
    }
  ],
  "ingredients": [
    {
      "inci_name": "INCI name",
      "function": "e.g. Film Former, Wax, Preservative",
      "rag": "GREEN" | "AMBER" | "RED",
      "restriction": "relevant EU/UK restriction or 'No restrictions under EU Reg 1223/2009'",
      "note": "any compliance note"
    }
  ],
  "required_testing": [
    {
      "test_name": "string",
      "reason": "string",
      "typical_timeline": "string"
    }
  ],
  "key_risks": ["string array of top 3-4 risks in plain English"],
  "next_steps": ["string array of 4-5 prioritised actions for the brand team"]
}

Be specific and accurate about EU Cosmetics Regulation requirements. Flag quantified performance claims (like '4x') as AMBER because they require clinical substantiation data. Flag 'all day' and 'instantly' claims as AMBER — they need wear-test or clinical evidence. Use RED only for genuine prohibition issues. Keep all string values concise — max 1-2 sentences each. Do not pad responses.

Product concept to analyse:
"""


# ── Helpers ───────────────────────────────────────────────────────────────────
def extract_concepts_from_pptx(file_bytes: bytes) -> list[dict]:
    """Extract one concept per slide from a PPTX file."""
    concepts = []
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
        slides = sorted([n for n in z.namelist()
                         if n.startswith("ppt/slides/slide") and n.endswith(".xml")])
        for i, slide_path in enumerate(slides, 1):
            with z.open(slide_path) as f:
                xml = f.read().decode("utf-8")
            text = re.sub(r"<[^>]+>", " ", xml)
            text = re.sub(r"\s+", " ", text).strip()
            if not text:
                continue
            # Try to extract concept name from "Concept Name: X" pattern
            name_match = re.search(r"Concept Name[:\s]+([^\n]+?)(?:\s+Insight|\s+Reasons|\s+Benefit|$)",
                                   text, re.IGNORECASE)
            name = name_match.group(1).strip() if name_match else f"Concept {i}"
            # Brief preview (first ~120 chars after name)
            preview_start = name_match.end() if name_match else 0
            preview = text[preview_start:preview_start + 120].strip()
            concepts.append({"name": name, "preview": preview, "full_text": text, "slide": i})
    return concepts


def badge(rag: str) -> str:
    cls = {"GREEN": "badge-green", "AMBER": "badge-amber", "RED": "badge-red"}.get(rag, "badge-amber")
    icon = {"GREEN": "✅", "AMBER": "⚠️", "RED": "🚫"}.get(rag, "⚠️")
    return f'<span class="{cls}">{icon} {rag}</span>'


def score_box(score: int, rag: str) -> str:
    cls = {"GREEN": "score-green", "AMBER": "score-amber", "RED": "score-red"}.get(rag, "score-amber")
    label = {"GREEN": "LOW RISK", "AMBER": "REVIEW REQUIRED", "RED": "HIGH RISK"}.get(rag, "REVIEW REQUIRED")
    colour = {"GREEN": "#065f46", "AMBER": "#92400e", "RED": "#991b1b"}.get(rag, "#92400e")
    return f"""
    <div class="score-box {cls}">
      <div class="score-num" style="color:{colour}">{score}</div>
      <div class="score-label" style="color:{colour}">{label}</div>
      <div style="font-size:0.75rem;color:#6b7280;margin-top:0.2rem;">Compliance Score / 100</div>
    </div>"""


def run_analysis(api_key: str, concept: str) -> dict:
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": ANALYSIS_PROMPT + concept}],
    )
    raw = message.content[0].text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def render_results(result: dict):
    r_col1, r_col2, r_col3 = st.columns([2, 1, 1])

    with r_col1:
        st.markdown(f"""
        <div class="card">
          <h3>📦 {result.get('product_name', 'Product')} &nbsp;
              <span class="tag">{result.get('product_category', '')}</span></h3>
          <p style="color:#374151;margin:0">{result.get('summary', '')}</p>
        </div>
        """, unsafe_allow_html=True)

    with r_col2:
        st.markdown(score_box(result.get("overall_score", 0), result.get("overall_rag", "AMBER")),
                    unsafe_allow_html=True)

    with r_col3:
        risks = result.get("key_risks", [])
        risk_html = "".join(f"<li style='margin-bottom:0.3rem;font-size:0.85rem'>{r}</li>" for r in risks)
        st.markdown(f"""
        <div class="card" style="height:100%;box-sizing:border-box">
          <h3>⚡ Key Risks</h3>
          <ul style="padding-left:1.2rem;margin:0">{risk_html}</ul>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["📣 Claims Analysis", "🧪 Ingredients", "🔬 Required Testing", "✅ Next Steps"])

    with tab1:
        claims = result.get("claims", [])
        if claims:
            for claim in claims:
                rag = claim.get("rag", "AMBER")
                icon = {"GREEN": "✅", "AMBER": "⚠️", "RED": "🚫"}.get(rag, "⚠️")
                with st.expander(f"{icon} \"{claim.get('claim_text', '')}\"", expanded=(rag != "GREEN")):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown(f"**Type:** {claim.get('claim_type', '')}")
                        st.markdown(badge(rag), unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"**Issue:** {claim.get('issue', '')}")
                        action = claim.get("action_required", "None")
                        if action and action != "None":
                            st.info(f"**Action required:** {action}")
        else:
            st.info("No claims identified.")

    with tab2:
        ingredients = result.get("ingredients", [])
        if ingredients:
            for ing in ingredients:
                rag = ing.get("rag", "GREEN")
                icon = {"GREEN": "✅", "AMBER": "⚠️", "RED": "🚫"}.get(rag, "⚠️")
                with st.expander(f"{icon} {ing.get('inci_name', '')} — {ing.get('function', '')}",
                                 expanded=(rag != "GREEN")):
                    st.markdown(badge(rag), unsafe_allow_html=True)
                    st.markdown(f"**EU/UK Restriction:** {ing.get('restriction', '')}")
                    note = ing.get("note", "")
                    if note:
                        st.markdown(f"**Note:** {note}")
        else:
            st.info("No ingredients identified.")

    with tab3:
        tests = result.get("required_testing", [])
        if tests:
            for test in tests:
                st.markdown(f"""
                <div class="card">
                  <h3>🔬 {test.get('test_name', '')}</h3>
                  <p style="margin:0 0 0.5rem;color:#374151">{test.get('reason', '')}</p>
                  <span class="tag">⏱ {test.get('typical_timeline', '')}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No additional testing flagged.")

    with tab4:
        steps = result.get("next_steps", [])
        if steps:
            for i, step in enumerate(steps, 1):
                st.markdown(f"**{i}.** {step}")
        else:
            st.info("No next steps identified.")

    st.markdown("---")
    st.caption(
        "⚠️ RegCoPilot is an AI-powered screening tool and does not constitute legal or regulatory advice. "
        "Always verify outputs with a qualified cosmetics regulatory consultant."
    )


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div style="font-size:1.6rem;line-height:1">🔬</div>
  <div>
    <h1>RegCoPilot.ai</h1>
    <p>AI-powered regulatory compliance for cosmetics brand managers</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Get your key at console.anthropic.com",
    )
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown(
        "RegCoPilot analyses cosmetics product concepts against EU & UK regulatory requirements, "
        "flags compliance risks, and generates testing roadmaps — in seconds."
    )
    st.markdown("---")
    st.caption("Proof of Concept · RegCoPilot.ai · 2025")
    st.caption("⚠️ For demonstration only. Always verify with a qualified regulatory consultant.")

def run_and_render(api_key: str, concept_text: str, concept_name: str):
    if not api_key:
        st.error("Please enter your Anthropic API key in the sidebar.")
        st.stop()
    with st.spinner(f"Analysing '{concept_name}' against EU/UK regulations…"):
        try:
            result = run_analysis(api_key, concept_text)
        except json.JSONDecodeError as e:
            st.error(f"Could not parse the AI response. Please try again. ({e})")
            st.stop()
        except anthropic.AuthenticationError:
            st.error("Invalid API key. Please check your key in the sidebar.")
            st.stop()
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.stop()
    st.markdown("---")
    render_results(result)


# ── Try it out ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:white;border-left:4px solid #0d6efd;border-radius:6px;
            padding:0.85rem 1.1rem;margin-bottom:1.25rem;
            box-shadow:0 1px 3px rgba(0,0,0,0.06)">
  <p style="margin:0;font-size:0.95rem;color:#1a2e5a;font-weight:500">
    RegCoPilot analyses cosmetics product concepts before they go into development —
    checking marketing claims, hero ingredients, and product classification against
    EU &amp; UK regulations in seconds, so brand teams can identify compliance risks
    early and avoid costly reformulations down the line.
    Each concept is scored and assigned a traffic light rating:
    <span style="color:#065f46;font-weight:700">● Green</span> (proceed),
    <span style="color:#92400e;font-weight:700">● Amber</span> (rework required), or
    <span style="color:#991b1b;font-weight:700">● Red</span> (stop — compliance issue identified).
  </p>
  <ul style="margin:0.75rem 0 0;padding-left:1.1rem;font-size:0.88rem;color:#1a2e5a">
    <li style="margin-bottom:0.4rem">
      <strong>EU Cosmetics Regulation 1223/2009</strong> — the primary legal framework
      governing cosmetic products sold in the EU and UK, covering permitted ingredients,
      prohibited substances, and product safety requirements.
    </li>
    <li style="margin-bottom:0.4rem">
      <strong>COSING (Cosmetic Ingredients Database)</strong> — the European Commission's
      official database of cosmetic ingredients, used to verify ingredient functions,
      restrictions, and maximum permitted concentrations.
    </li>
    <li>
      <strong>ASA/CAP Advertising Standards</strong> — the UK rules governing what
      claims can be made in marketing material, ensuring performance claims are
      substantiated and not misleading to consumers.
    </li>
  </ul>
  <p style="display:none">
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown("### 💡 See How It Works")
st.markdown("Select one of our sample brand concepts and run an instant compliance check.")
st.markdown(" ")

s_cols = st.columns(3)
for i, concept in enumerate(SAMPLE_CONCEPTS):
    with s_cols[i]:
        st.markdown(f"""
        <div class="sample-card">
          <div class="sample-card-inner">
            <div style="flex-shrink:0;display:flex;align-items:center;justify-content:center;
                        width:52px;height:68px">{SAMPLE_SVGS[i]}</div>
            <div>
              <h4>{concept['name']}</h4>
              <p>{concept['category']}</p>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Try this concept →", key=f"sample_{i}", use_container_width=True):
            st.session_state["queued_concept"] = concept

if "queued_concept" in st.session_state:
    qc = st.session_state["queued_concept"]
    with st.expander(f"📋 {qc['name']}", expanded=True):
        st.text(qc["full_text"])
    if st.button("🔍 Analyse This Concept", type="primary", key="btn_queued"):
        run_and_render(api_key, qc["full_text"], qc["name"])
        del st.session_state["queued_concept"]

st.markdown("---")

# ── Main upload area ──────────────────────────────────────────────────────────
st.markdown("### 📂 Analyse Your Own Concept")
st.markdown("Upload a PowerPoint file — one concept per slide. RegCoPilot reads every slide and lets you choose which to analyse.")

uploaded_file = st.file_uploader(
    "Drop your .pptx concept deck here",
    type=["pptx"],
    label_visibility="collapsed",
)

if uploaded_file:
    concepts = extract_concepts_from_pptx(uploaded_file.read())
    if not concepts:
        st.warning("No slides found in the uploaded file.")
    else:
        st.success(f"**{len(concepts)} concept{'s' if len(concepts) != 1 else ''} found.** Select one to analyse:")
        upload_idx = st.radio(
            "Select concept",
            options=list(range(len(concepts))),
            format_func=lambda i: f"Slide {concepts[i]['slide']} — {concepts[i]['name']}",
            label_visibility="collapsed",
            key="upload_radio",
        )
        sel = concepts[upload_idx]
        with st.expander("Preview selected concept", expanded=True):
            st.text(sel["full_text"][:600] + ("…" if len(sel["full_text"]) > 600 else ""))
        st.markdown(" ")
        if st.button("🔍 Analyse Selected Concept", type="primary", use_container_width=True, key="btn_upload"):
            run_and_render(api_key, sel["full_text"], sel["name"])
else:
    st.markdown("""
    <div style="text-align:center;padding:3rem 1rem;color:#6b7280;
                border:2px dashed #d1d5db;border-radius:12px;background:white;">
      <div style="font-size:2.8rem;margin-bottom:0.75rem">📂</div>
      <p style="font-weight:600;color:#374151;font-size:1.05rem;margin:0 0 0.3rem">
        Drag and drop your concept deck here
      </p>
      <p style="font-size:0.875rem;margin:0">Supports .pptx · One concept per slide</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ── Manual paste (secondary) ──────────────────────────────────────────────────
with st.expander("✏️ Or paste a concept manually"):
    manual_text = st.text_area(
        "Product concept",
        placeholder="Concept Name: ...\nInsight: ...\nIngredients: ...\nClaims: ...",
        height=220,
        label_visibility="collapsed",
    )
    if st.button("🔍 Analyse Concept", type="primary", use_container_width=True, key="btn_manual"):
        if not manual_text.strip():
            st.error("Please paste a product concept to analyse.")
            st.stop()
        run_and_render(api_key, manual_text, "concept")
