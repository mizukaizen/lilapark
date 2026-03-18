#!/usr/bin/env python3
"""
The 3am Protocol — PDF Builder v4
===================================
Approach : HTML/CSS → PDF via Playwright (Chromium)
Design   : 12-column grid · 4mm baseline · Perfect Fourth type scale
Brand    : LILA-BRAND.md — warm off-white pages, #5FA86A green accents
"""

import os, json
from pathlib import Path
from playwright.sync_api import sync_playwright
import pypdf

# ── Inline SVG icons ───────────────────────────────────────────────────────────
ICON_SUN = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#4D9559" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4" fill="#4D9559"/><line x1="12" y1="2" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="22"/><line x1="4.22" y1="4.22" x2="6.34" y2="6.34"/><line x1="17.66" y1="17.66" x2="19.78" y2="19.78"/><line x1="2" y1="12" x2="5" y2="12"/><line x1="19" y1="12" x2="22" y2="12"/><line x1="4.22" y1="19.78" x2="6.34" y2="17.66"/><line x1="17.66" y1="6.34" x2="19.78" y2="4.22"/></svg>'
ICON_MOON = '<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="#6B5D45" stroke="none"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
ICON_CHECK = '<svg xmlns="http://www.w3.org/2000/svg" width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
ICON_SCIENCE = '<svg xmlns="http://www.w3.org/2000/svg" width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="#5FA86A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3v4l-4 5a2 2 0 0 0 1.7 3h12.6A2 2 0 0 0 20 12l-4-5V3"/><line x1="8" y1="3" x2="16" y2="3"/></svg>'

# ── Paths ─────────────────────────────────────────────────────────────────────
FONTS  = Path("/sessions/epic-awesome-gates/fonts")
IMGS   = Path("/sessions/epic-awesome-gates/images")
OUT    = Path("/sessions/epic-awesome-gates/mnt/Documents/_cowork/outputs")
FINAL  = OUT / "the-3am-protocol-v9.pdf"

def font_url(f): return f"file://{FONTS}/{f}"
def img_url(f):  return f"file://{IMGS}/{f}"

# ── Day content ───────────────────────────────────────────────────────────────
DAYS = [
    {
        "num": "01", "img": "days.jpg", "title": "Sleep Anchor",
        "hangul": "기정", "roman": "Gijeong", "meaning": "The fixed daily point",
        "intro": "The single most evidence-supported thing you can do for sleep quality has nothing to do with what you take or what you avoid. It's about <em>when</em> you wake. A fixed wake time anchors your entire circadian rhythm — adenosine clearance, cortisol timing, melatonin onset.",
        "morning": "Set one wake time. Pick the earliest time you can maintain on both weekdays and weekends. Set two alarms and get up on the first one. Do not adjust for 7 days.",
        "evening": "Calculate your target bedtime: wake time minus 7.5 hours. Write it down. Tonight, aim to be in bed 30 minutes before this time. No screens, no eating after this point.",
        "science": "Roenneberg et al. documented that even a 1-hour social jetlag — different weekend/weekday wake times — is associated with metabolic dysfunction and mood disruption independent of total sleep hours. Consistency beats duration.",
        "check": "Did you wake in the night? Note the time and duration.",
    },
    {
        "num": "02", "img": "intro.jpg", "title": "Dim the Light Signal",
        "hangul": "불빛", "roman": "Bulbit", "meaning": "The light that signals",
        "intro": "Light is the primary input to the suprachiasmatic nucleus — the master clock governing your cortisol rhythm. Bright light at night tells your brain it's still daytime. Two hours of reduced light before bed can shift melatonin onset by up to 90 minutes.",
        "morning": "Within 30–60 minutes of waking, get 10 minutes of bright outdoor light. No sunglasses. This is your cortisol anchor for the day — it tells your body when the day begins.",
        "evening": "Two hours before bed: dim all lights to below 50 lux. Use warm bulbs (2700K or lower), turn off overhead lighting, use lamps. Enable night mode on all screens. If possible, use candlelight in the final 30 minutes.",
        "science": "Gooley et al. (2011) demonstrated that room light before bedtime suppresses melatonin onset by ~90 minutes and reduces melatonin duration. Blue-light-blocking glasses help but reducing overall light intensity is the primary lever.",
        "check": "Was your evening environment noticeably dimmer than usual?",
    },
    {
        "num": "03", "img": "days.jpg", "title": "Cool the Body",
        "hangul": "체온", "roman": "Cheon", "meaning": "Body temperature regulation",
        "intro": "Sleep onset requires a core body temperature drop of 1–3°F. The Korean ondol tradition — floor heating that warms the body from below — achieves this paradoxically: warming the extremities causes peripheral vasodilation, accelerating core cooling.",
        "morning": "Continue Day 1 and 2 practices. Add: open bedroom windows for 10 minutes upon waking to air out the sleep environment.",
        "evening": "Take a warm bath or shower 60–90 minutes before bed. Water temperature: comfortably warm (40–42°C), not hot. 10–15 minutes is sufficient. After emerging, allow natural cooling — don't rush. Set bedroom temperature to 18–20°C.",
        "science": "Haghayegh et al. (2019) meta-analysis confirmed that warm bathing 1–2 hours before bed reduces sleep-onset latency by ~10 minutes on average. The mechanism is distal vasodilation triggering core heat loss — the same process ondol floor heating leverages.",
        "check": "Note your estimated sleep-onset time compared to previous nights.",
    },
    {
        "num": "04", "img": "intro.jpg", "title": "The Evening Practice",
        "hangul": "저녁", "roman": "Jeonyeok", "meaning": "The evening as its own time",
        "intro": "In the saenghwal framework, jeonyeok is a distinct phase — not 'the period before bed' but an active wind-down with its own character. The nervous system cannot transition from stimulation to sleep without a deliberate deceleration phase.",
        "morning": "Continue Days 1–3. Add: after morning light exposure, write your three priorities for the day. This externalises cognitive load and reduces evening rumination.",
        "evening": "The 20-minute jeonyeok sequence: (1) Dim lights fully. (2) Make ssuk (mugwort) or chamomile tea — sit with it for 5 minutes, no phone. (3) Write tomorrow's top three priorities. (4) Do 5 minutes of slow nasal breathing. (5) Move to bed.",
        "science": "The pre-sleep cognitive arousal model (Harvey, 2000) identifies worry and planning as primary sleep disruptors. Externalising tomorrow's agenda reduces rumination. The ritual structure itself is the primary mechanism.",
        "check": "Did you complete the jeonyeok sequence? How long did it take?",
    },
    {
        "num": "05", "img": "days.jpg", "title": "Morning First Light",
        "hangul": "아침 빛", "roman": "Achim Bit", "meaning": "Morning light as medicine",
        "intro": "By Day 5, you have an anchor, reduced evening light, thermal regulation, and a wind-down practice. Today we maximise the morning light signal — the cortisol anchor that determines when your entire circadian rhythm fires.",
        "morning": "Extended morning light: 20 minutes of outdoor light within 30 minutes of waking. Walk if possible — movement amplifies the cortisol response. No sunglasses. If overcast, double the duration.",
        "evening": "Continue all previous practices. This evening, lay out everything you need for your morning walk before bed. Reduce the friction of the practice you most need to protect.",
        "science": "Satchin Panda's research established that light timing is the dominant zeitgeber for the SCN. Morning light within 60 minutes of waking advances circadian phase — meaning your cortisol peak, sleep pressure, and melatonin onset all shift forward together.",
        "check": "Did you get outdoor light within 30 minutes? Duration?",
    },
    {
        "num": "06", "img": "intro.jpg", "title": "Food & Timing",
        "hangul": "음식", "roman": "Eumsik", "meaning": "Food as a circadian signal",
        "intro": "The gut has its own circadian clock — the peripheral oscillator — that receives timing signals from food intake. Eating late at night sends a 'daytime' signal to your gut clock while your central SCN clock is receiving 'night' signals. This misalignment disrupts sleep architecture.",
        "morning": "Continue all practices. Add: delay your first meal by 30–60 minutes after waking. Allow the morning light and cortisol peak to complete their arc before introducing the food signal.",
        "evening": "Eat your final meal at least 3 hours before bed. If hungry later, a small handful of nuts is fine — but avoid anything that triggers significant insulin release. Alcohol, even moderate amounts, fragments sleep architecture directly.",
        "science": "Mistlberger & Skene (2005) demonstrated that food timing is a secondary zeitgeber that can override light-driven circadian signals. Late eating shifts peripheral clock timing independently of light exposure — creating internal circadian desynchrony.",
        "check": "What time was your last meal? How many hours before bed?",
    },
    {
        "num": "07", "img": "days.jpg", "title": "The Full Protocol",
        "hangul": "전체", "roman": "Jeonche", "meaning": "The complete integrated practice",
        "intro": "Today you run everything together. This is not a more demanding day — it's exactly what you've been doing, now experienced as a coherent whole. The protocol takes about 45 minutes of your day. Most of it is woven into things you already do.",
        "morning": "On waking: (1) Rise at your fixed anchor time. (2) 20 minutes outdoor light, ideally a walk. (3) Delay breakfast 30–60 min. Write your three daily priorities. The whole sequence: 25 minutes.",
        "evening": "3 hours before bed: last meal. 2 hours before: dim all lights. 90 minutes before: warm bath. 20 minutes before: jeonyeok sequence (tea, priorities, slow breathing). Bedroom at 18–20°C. In bed 30 minutes before your target sleep time.",
        "science": "The cumulative effect of circadian alignment across multiple channels — light, temperature, food, activity timing — is larger than any single intervention. This is the saenghwal principle in biological terms: health emerges from the integrated rhythm of daily life.",
        "check": "Compare tonight's sleep to Day 1. What has shifted?",
    },
]

# ── CSS ────────────────────────────────────────────────────────────────────────
CSS = f"""
@font-face {{
  font-family: 'Fraunces';
  src: url('{font_url("CrimsonText-Regular.ttf")}') format('truetype');
  font-weight: 400; font-style: normal;
}}
@font-face {{
  font-family: 'Fraunces';
  src: url('{font_url("CrimsonText-Bold.ttf")}') format('truetype');
  font-weight: 700; font-style: normal;
}}
@font-face {{
  font-family: 'Fraunces';
  src: url('{font_url("CrimsonText-Italic.ttf")}') format('truetype');
  font-weight: 400; font-style: italic;
}}
/* ── Plus Jakarta Sans — exact website body font ── */
@font-face {{
  font-family: 'Jakarta';
  src: url('{font_url("PlusJakartaSans-Regular.ttf")}') format('truetype');
  font-weight: 400; font-style: normal;
}}
@font-face {{
  font-family: 'Jakarta';
  src: url('{font_url("PlusJakartaSans-Medium.ttf")}') format('truetype');
  font-weight: 500; font-style: normal;
}}
@font-face {{
  font-family: 'Jakarta';
  src: url('{font_url("PlusJakartaSans-SemiBold.ttf")}') format('truetype');
  font-weight: 600; font-style: normal;
}}
@font-face {{
  font-family: 'Jakarta';
  src: url('{font_url("PlusJakartaSans-Bold.ttf")}') format('truetype');
  font-weight: 700; font-style: normal;
}}
@font-face {{
  font-family: 'NanumGothic';
  src: url('{font_url("NanumGothic-Regular.ttf")}') format('truetype');
  font-weight: 400; font-style: normal;
}}

@page {{
  size: A4;
  margin: 0;
}}

:root {{
  /* ── Website design tokens (direct from lilapark.xyz source) ── */
  --bg:          #FAFAF7;
  --surface:     #FFFFFF;
  --warm:        #F3F0E8;
  --warm-deep:   #EAE6D8;
  --text-1:      #18180F;
  --text-2:      #64635A;
  --text-3:      #AEAC9C;
  --accent:      #5FA86A;
  --accent-hover:#4D9559;
  --accent-mid:  #8DC096;
  --accent-lt:   #C4DFC8;
  --accent-dim:  rgba(95,168,106,0.10);
  --gold:        #C89B2A;
  /* border matches website: rgba(20,19,14,0.08) */
  --border:      rgba(20,19,14,0.09);
  --border-h:    rgba(20,19,14,0.18);
  --dark-1:      #141410;
  --dark-2:      #1A1209;
  /* Spacing */
  --sp-xs:  4mm;
  --sp-sm:  8mm;
  --sp-md:  12mm;
  --sp-lg:  16mm;
  --sp-xl:  24mm;
  --sp-2xl: 32mm;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

/* Explicit dimensions on html root — prevents Chromium sub-pixel edge gaps.
   Background matches cover page dark so any sub-pixel gaps are invisible. */
html {{
  width: 210mm;
  max-width: 210mm;
  margin: 0;
  padding: 0;
  overflow: hidden;
  background: var(--dark-1);
}}

body {{
  width: 210mm;
  margin: 0;
  padding: 0;
  font-family: 'Jakarta', sans-serif;
  font-size: 10pt;
  line-height: 1.65;
  color: var(--text-1);
  background: var(--dark-1);
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
  -webkit-font-smoothing: antialiased;
}}

/* ── Page wrapper ── */
.page {{
  width: 210mm;
  height: 297mm;
  background: var(--bg);
  position: relative;
  break-after: page;
  break-inside: avoid;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}}
.page-cover {{ background: var(--dark-1); height: 297mm; }}

/* ── Header bar — nav-style, matches website ── */
.page-header {{
  background: rgba(250,250,247,0.97);
  border-bottom: 1pt solid var(--border);
  padding: 2.5mm 20mm;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 7pt;
}}
.nav-dot {{
  width: 6pt;
  height: 6pt;
  border-radius: 50%;
  background: var(--accent);
  flex-shrink: 0;
}}
.page-header .breadcrumb {{
  font-family: 'Jakarta', sans-serif;
  font-size: 7pt;
  font-weight: 500;
  letter-spacing: 0.05em;
  color: var(--text-3);
}}

/* ── Footer ── */
.page-footer {{
  margin-top: auto;
  padding: var(--sp-sm) 20mm 5mm 20mm;
  border-top: 0.4pt solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}}
.page-footer span {{
  font-family: 'Inter', sans-serif;
  font-size: var(--t-eyebrow);
  color: var(--text-3);
}}

/* ── Content area ── */
.page-body {{
  padding: 5mm 20mm 4mm 20mm;
  flex: 1;
  display: flex;
  flex-direction: column;
}}

/* ── Typography — mirrors website type system ── */
h1 {{
  font-family: 'Fraunces', serif;
  font-size: 20pt;
  font-weight: 600;
  line-height: 1.2;
  color: var(--text-1);
  margin-bottom: 3pt;
}}
h1 em {{ font-style: italic; color: var(--accent); }}
h2 {{
  font-family: 'Fraunces', serif;
  font-size: 16pt;
  font-weight: 600;
  line-height: 1.25;
  color: var(--text-1);
  margin-top: var(--sp-sm);
  margin-bottom: var(--sp-xs);
}}
h3 {{
  font-family: 'Fraunces', serif;
  font-size: 12pt;
  font-weight: 600;
  line-height: 1.3;
  color: var(--text-1);
  margin-bottom: 3pt;
}}
p {{
  font-size: 10pt;
  line-height: 1.65;
  color: var(--text-1);
  margin-bottom: var(--sp-xs);
}}
p.secondary {{
  color: var(--text-2);
  font-size: 9pt;
  line-height: 1.6;
}}

/* Website eyebrow: 0.72rem equivalent = 8pt */
.sec-eye {{
  font-family: 'Jakarta', sans-serif;
  font-size: 7.5pt;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 5pt;
}}
.sec-eye-muted {{
  font-family: 'Jakarta', sans-serif;
  font-size: 7.5pt;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-3);
  margin-bottom: 5pt;
}}
/* Legacy eyebrow alias */
.eyebrow {{
  font-family: 'Jakarta', sans-serif;
  font-size: 7.5pt;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 4pt;
}}
.subtitle {{
  font-size: 9pt;
  color: var(--text-2);
  line-height: 1.6;
  margin-bottom: 0;
}}

/* ══════════════════════════════════════════════════════
   DAY PAGE COMPONENTS — ported from lilapark.xyz source
   ══════════════════════════════════════════════════════ */

/* ── Day header ── */
.day-header {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 5mm;
  position: relative;
  z-index: 1;
}}
.day-header-left {{ flex: 1; }}

/* ── Day badge — dark stat card from website ── */
.day-badge {{
  background: var(--dark-1);
  border-radius: 12pt;
  padding: 9pt 16pt;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-left: 8mm;
  box-shadow: 0 4pt 20pt rgba(0,0,0,0.22);
  min-width: 50pt;
}}
.day-badge-label {{
  font-family: 'Jakarta', sans-serif;
  font-size: 6pt;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--accent-mid);
  margin-bottom: 2pt;
}}
.day-badge-num {{
  font-family: 'Fraunces', serif;
  font-size: 30pt;
  font-weight: 700;
  line-height: 1;
  color: var(--accent);
}}

/* ── Korean concept — origin-pill row (website .about-origin pattern) ── */
.origin-row {{
  display: flex;
  align-items: center;
  gap: 5pt;
  margin-top: 5pt;
  flex-wrap: wrap;
}}
.origin-pill {{
  font-family: 'Jakarta', sans-serif;
  font-size: 8pt;
  font-weight: 500;
  padding: 3pt 9pt;
  border-radius: 9pt;
  background: var(--surface);
  border: 1pt solid var(--border-h);
  color: var(--text-2);
  line-height: 1.2;
}}
.origin-pill.kr {{
  font-family: 'NanumGothic', sans-serif;
  font-size: 9.5pt;
  color: var(--accent-hover);
  border-color: rgba(95,168,106,0.35);
  background: var(--accent-dim);
  font-weight: 700;
}}
.origin-arr {{ color: var(--text-3); font-size: 9pt; }}

/* ── Section opener number (non-day pages) ── */
.section-num {{
  font-family: 'Fraunces', serif;
  font-size: 52pt;
  font-weight: 700;
  line-height: 1;
  color: var(--accent-lt);
  text-align: right;
  margin: 0;
  flex-shrink: 0;
  padding-left: 8mm;
}}

/* ── Rule ── */
.rule {{
  border: none;
  border-top: 0.5pt solid var(--accent);
  margin: 0;
}}
.rule-light {{
  border: none;
  border-top: 0.4pt solid var(--border);
  margin: var(--sp-sm) 0;
}}

/* ── Banner image ── */
.banner {{
  width: 100%;
  display: block;
  object-fit: cover;
  margin: 0;
}}
/* Full-bleed: escape the 20mm body padding */
.banner-wrap {{
  margin-left: -20mm;
  margin-right: -20mm;
  line-height: 0;
}}
.banner-wrap .rule {{
  margin: 0;
  width: 100%;
}}

/* ── Morning Check callout — product card accent style ── */
.callout {{
  display: flex;
  margin: 6pt 0 0 0;
  background: var(--surface);
  border: 1pt solid var(--border);
  border-radius: 12pt;
  overflow: hidden;
  box-shadow: 0 2pt 8pt rgba(0,0,0,0.05);
}}
.callout-border {{
  width: 4pt;
  background: var(--accent);
  flex-shrink: 0;
  border-radius: 0;
}}
.callout-body {{
  padding: 9pt 13pt;
  flex: 1;
}}
.callout-head {{
  display: flex;
  align-items: center;
  gap: 6pt;
  margin-bottom: 4pt;
}}
.callout-icon-badge {{
  width: 15pt;
  height: 15pt;
  border-radius: 50%;
  background: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  line-height: 0;
}}
.callout-body p {{ font-size: 9pt; color: var(--text-2); line-height: 1.6; margin: 0; }}

/* ── Two-column morning/evening — card style from website ── */
.two-col {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8pt;
  margin: 5mm 0 0 0;
}}
.col-morning, .col-evening {{
  background: var(--surface);
  border: 1pt solid var(--border);
  border-radius: 14pt;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 2pt 10pt rgba(0,0,0,0.05);
}}
/* Gradient thumbnail header — from website .pt-sage / .pt-warm */
.col-thumb {{
  display: flex;
  align-items: center;
  gap: 6pt;
  padding: 7pt 13pt;
}}
.col-morning .col-thumb {{
  background: linear-gradient(135deg, #E8F4EA, #C4DFC8);
}}
.col-evening .col-thumb {{
  background: linear-gradient(135deg, #F5F0E8, #E8E0CC);
}}
.col-thumb-icon {{
  display: flex; align-items: center; flex-shrink: 0; line-height: 0;
}}
.col-thumb-label {{
  font-family: 'Jakarta', sans-serif;
  font-size: 7pt;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}}
.col-morning .col-thumb-label {{ color: var(--accent-hover); }}
.col-evening .col-thumb-label {{ color: #6B5D45; }}
/* Card body */
.col-body {{
  padding: 10pt 13pt 12pt;
  flex: 1;
}}
.col-body p {{
  font-size: 9pt;
  color: var(--text-2);
  line-height: 1.6;
  margin: 0;
}}

/* ── Korean concept (legacy — kept for intro/other pages) ── */
.korean-block {{
  text-align: left;
  margin: 3mm 0 0 0;
}}
.korean-hangul {{
  font-family: 'NanumGothic', sans-serif;
  font-size: 14pt;
  line-height: 1.3;
  color: var(--accent);
  display: block;
}}
.korean-meaning {{
  font-size: 7.5pt;
  color: var(--text-3);
  font-family: 'Jakarta', sans-serif;
  letter-spacing: 0.04em;
}}

/* ── Why this works — bridge-strip style from website ── */
.why-block {{
  margin: 6pt 0 0 0;
  background: var(--accent-dim);
  border: 1pt solid var(--accent-lt);
  border-radius: 12pt;
  padding: 9pt 13pt;
}}
.why-head {{
  display: flex;
  align-items: center;
  gap: 6pt;
  margin-bottom: 4pt;
}}
.why-icon {{
  width: 16pt;
  height: 16pt;
  border-radius: 50%;
  background: rgba(95,168,106,0.18);
  border: 1pt solid var(--accent-mid);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  line-height: 0;
}}
.why-block p {{ font-size: 9pt; color: var(--text-2); line-height: 1.6; margin: 0; }}

/* ── Progress strip ── */
.progress-strip {{
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border-top: 0.4pt solid var(--border);
  border-bottom: 0.4pt solid var(--border);
  margin-top: auto;
  margin-left: -20mm;
  margin-right: -20mm;
  width: calc(100% + 40mm);
  padding: 4pt 20mm;
}}
.progress-step {{
  text-align: center;
  font-family: 'Inter', sans-serif;
  font-size: var(--t-eyebrow);
  font-weight: 700;
  padding: 3pt 0;
  color: var(--border);
}}
.progress-step.done   {{ color: var(--accent); }}
.progress-step.active {{ color: var(--gold); }}

/* ── Data table (overview) ── */
.data-table {{
  width: 100%;
  border-collapse: collapse;
  margin: var(--sp-sm) 0;
  border: 0.6pt solid var(--accent-mid);
}}
.data-table thead tr {{
  background: var(--accent);
}}
.data-table thead th {{
  color: white;
  font-family: 'Inter', sans-serif;
  font-size: var(--t-eyebrow);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 5pt 7pt;
  text-align: left;
}}
.data-table tbody tr:nth-child(even) {{ background: var(--warm); }}
.data-table tbody tr:nth-child(odd)  {{ background: var(--surface); }}
.data-table tbody td {{
  font-size: var(--t-sm);
  color: var(--text-1);
  padding: 5.5pt 7pt;
  border-bottom: 0.4pt solid var(--border);
  vertical-align: top;
}}
.data-table tbody td:first-child {{
  font-weight: 700;
  color: var(--text-3);
  font-family: 'Inter', sans-serif;
}}
.data-table .td-korean {{
  font-family: 'NanumGothic', sans-serif;
  color: var(--accent);
}}

/* ── Numbered list (how-to) ── */
.num-list {{ margin: var(--sp-sm) 0; }}
.num-item {{
  display: grid;
  grid-template-columns: 10mm 1fr;
  gap: 0;
  padding-bottom: var(--sp-sm);
  border-bottom: 0.4pt solid var(--border);
  margin-bottom: var(--sp-sm);
}}
.num-item:last-child {{ border-bottom: none; margin-bottom: 0; }}
.num-item .num {{
  font-family: 'Inter', sans-serif;
  font-size: var(--t-caption);
  font-weight: 700;
  color: var(--accent);
  padding-top: 1pt;
}}
.num-item h3 {{ margin-bottom: 3pt; margin-top: 0; }}
.num-item p  {{ margin: 0; font-size: var(--t-sm); color: var(--text-2); line-height: 13pt; }}

/* ── Pull quote ── */
.pull-quote {{
  display: flex;
  margin: var(--sp-md) 0;
}}
.pull-quote-border {{
  width: 3pt;
  background: var(--accent);
  flex-shrink: 0;
  margin-right: 8mm;
}}
.pull-quote blockquote {{
  font-family: 'Fraunces', serif;
  font-size: 10.5pt;
  font-style: italic;
  line-height: 16pt;
  color: var(--text-2);
}}

/* ── Cover page ── */
.cover-content {{
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  padding: var(--sp-md) 20mm var(--sp-lg) 20mm;
}}
/* Cover rules and image bleed to page edge */
.cover-rule {{
  width: calc(100% + 40mm);
  margin-left: -20mm;
}}
.cover-eyebrow {{
  font-family: 'Inter', sans-serif;
  font-size: var(--t-eyebrow);
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--accent-mid);
  text-align: center;
  margin-bottom: var(--sp-xs);
}}
.cover-title {{
  font-family: 'Fraunces', serif;
  font-size: var(--t-display);
  font-weight: 700;
  line-height: 1.1;
  color: #FAF7F0;
  text-align: center;
  margin: var(--sp-sm) 0 var(--sp-xs) 0;
}}
.cover-sub {{
  font-family: 'Fraunces', serif;
  font-size: 13pt;
  font-style: italic;
  color: var(--accent-lt);
  text-align: center;
  margin-bottom: var(--sp-xl);
}}
.cover-rule {{
  width: 100%;
  border-top: 0.5pt solid var(--accent);
  margin: 0;
}}
.cover-korean {{
  text-align: center;
  padding: var(--sp-sm) 0;
  flex: 0;
}}
.cover-korean .korean-hangul {{ font-size: 13pt; color: var(--accent-lt); }}
.cover-korean .korean-meaning {{ color: var(--text-3); }}
.cover-meta {{
  text-align: center;
  margin-top: var(--sp-lg);
}}
.cover-meta p {{
  font-family: 'Inter', sans-serif;
  font-size: var(--t-caption);
  color: #6A6A5A;
  line-height: 13pt;
  margin: 0;
}}
.cover-meta .cover-author {{
  font-size: var(--t-sm);
  color: #8A8A7A;
  margin-bottom: 4pt;
}}
.cover-meta .ng {{ font-family: 'NanumGothic', sans-serif; }}

/* ── CTA page ── */
.cta-body {{
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--sp-lg) 20mm;
  flex: 1;
}}
.cta-sup {{
  font-family: 'Fraunces', serif;
  font-size: 12pt;
  font-style: italic;
  color: var(--text-2);
  margin-bottom: var(--sp-md);
}}
.cta-title {{
  font-family: 'Fraunces', serif;
  font-size: 28pt;
  font-weight: 700;
  line-height: 1.15;
  color: var(--text-1);
  margin-bottom: var(--sp-sm);
}}
.cta-desc {{
  font-family: 'Fraunces', serif;
  font-size: 12pt;
  font-style: italic;
  color: var(--text-2);
  line-height: 17pt;
  max-width: 130mm;
  margin: 0 auto var(--sp-xl) auto;
}}
.cta-box {{
  display: flex;
  width: 100%;
  max-width: 120mm;
}}
.cta-box .callout-border {{ background: var(--gold); }}
.cta-box .callout-body {{ background: var(--warm); text-align: center; }}
.cta-link {{
  font-family: 'Fraunces', serif;
  font-size: 13pt;
  font-weight: 700;
  color: var(--accent);
  display: block;
  margin-bottom: 4pt;
}}
.cta-price {{
  font-family: 'Inter', sans-serif;
  font-size: var(--t-caption);
  color: var(--text-3);
  letter-spacing: 0.05em;
}}
"""

# ── HTML helpers ──────────────────────────────────────────────────────────────

def page(content, section_tag="", page_num="", cls=""):
    header = f"""
    <header class="page-header">
      <div class="nav-dot"></div>
      <span class="breadcrumb">Lila Park{"  ·  " + section_tag if section_tag else ""}</span>
    </header>""" if not cls else ""

    footer = f"""
    <footer class="page-footer">
      <span>© 2026 Lila Park · lilapark.xyz</span>
      <span>{page_num}</span>
    </footer>""" if page_num else ""

    return f'<div class="page {cls}">{header}{content}{footer}</div>\n'


def progress(active_day):
    steps = ""
    for i in range(1, 8):
        if i < active_day:   cls = "done"
        elif i == active_day: cls = "active"
        else:                  cls = ""
        steps += f'<div class="progress-step {cls}">{i}</div>'
    return f'<div class="progress-strip">{steps}</div>'


# ── Page builders ─────────────────────────────────────────────────────────────

def cover_page():
    img = img_url("cover.jpg")
    html = f"""
    <div class="cover-content">
      <p class="cover-eyebrow">The 3am Protocol</p>
      <hr class="cover-rule">
      <img src="{img}" style="width:calc(100% + 40mm);margin-left:-20mm;height:88mm;object-fit:cover;display:block;" alt="">
      <hr class="cover-rule">
      <h1 class="cover-title">The 3am Protocol</h1>
      <p class="cover-sub">7 days to stop waking in the night</p>
      <hr class="cover-rule" style="width:100%;">
      <div class="cover-korean">
        <span class="korean-hangul">새벽 세 시의 비밀</span>
        <span class="korean-meaning">The secret of 3am</span>
      </div>
      <hr class="cover-rule" style="width:100%;">
      <div class="cover-meta">
        <p class="cover-author">Lila Park &nbsp;·&nbsp; <span class="ng">박리라</span></p>
        <p>V1.0 · MARCH 2026 · lilapark.xyz</p>
      </div>
    </div>
    """
    return page(html, cls="page-cover")


def intro_page():
    img = img_url("intro.jpg")
    html = f"""
    <div class="page-body">
      <span class="section-num">01</span>
      <h1>Why 3am?</h1>
      <p class="subtitle">The mechanism behind the wake-up</p>

      <hr class="rule" style="margin: var(--sp-sm) 0 0 0;">
      <div class="banner-wrap">
        <img src="{img}" class="banner" style="height:36mm;" alt="">
      </div>
      <hr class="rule" style="margin: 0 0 var(--sp-md) 0;">

      <p>Waking between 2 and 4am is not random. It follows a predictable biological pattern — one that most sleep advice completely misses. Understanding the mechanism is the first step to breaking it.</p>

      <h2>The Cortisol-Adenosine Window</h2>
      <p>Your body runs two opposing systems to manage sleep and waking. Adenosine is the pressure signal — it accumulates while you're awake and is cleared during sleep. Cortisol is the alerting signal — it begins rising in the early morning hours to prepare you to wake.</p>
      <p>In a well-regulated system, the cortisol rise and the final adenosine clearance align perfectly around your natural wake time. In a disrupted system — inconsistent sleep schedule, chronic stress, late eating — cortisol rises prematurely. The body mistakes 3am for dawn.</p>

      <div class="callout">
        <div class="callout-border"></div>
        <div class="callout-body">
          <p class="eyebrow">Why melatonin won't fix this</p>
          <p>Melatonin signals darkness to the brain — it supports sleep onset. But the 3am wake isn't a sleep onset problem. It's a cortisol rebound problem. Taking melatonin at 3am addresses the wrong mechanism entirely.</p>
        </div>
      </div>

      <p class="eyebrow" style="margin-top: var(--sp-sm);">The Saenghwal Framework</p>
      <p>Korean wellness has a concept called <strong><span style="font-family:'NanumGothic',sans-serif;">생활</span> (saenghwal)</strong> — the idea that health emerges from the <em>rhythm</em> of daily life, not from interventions layered onto chaos. Rather than adding sleep aids, this protocol rebuilds the daily rhythm so cortisol and adenosine realign naturally. You don't need to do them perfectly — you need to do them <em>consistently</em>.</p>
    </div>
    """
    return page(html, "INTRODUCTION", "1")


def overview_page():
    rows = [
        ("01", "Sleep Anchor — fix your wake time",   "기정", "Gijeong",  "5 min"),
        ("02", "Dim the Light Signal",                "불빛", "Bulbit",   "10 min"),
        ("03", "Cool the Body",                       "체온", "Cheon",    "15 min"),
        ("04", "The Evening Practice",                "저녁", "Jeonyeok", "20 min"),
        ("05", "Morning First Light",                 "아침 빛","Achim Bit","10 min"),
        ("06", "Food &amp; Timing",                   "음식", "Eumsik",   "5 min"),
        ("07", "The Full Protocol",                   "전체", "Jeonche",  "45 min"),
    ]
    table_rows = ""
    for r in rows:
        table_rows += f"""<tr>
          <td>{r[0]}</td>
          <td>{r[1]}</td>
          <td class="td-korean"><span style="font-family:'NanumGothic',sans-serif;">{r[2]}</span> {r[3]}</td>
          <td>{r[4]}</td>
        </tr>"""

    html = f"""
    <div class="page-body">
      <span class="section-num">02</span>
      <h1>The 7-Day Plan</h1>
      <p class="subtitle">One variable per day. All compounding.</p>
      <p style="margin-top:var(--sp-sm);">Each day introduces one new practice. You keep everything from previous days — by Day 7 you're running the full integrated protocol. Most people notice a difference by Day 3.</p>

      <table class="data-table">
        <thead><tr><th>Day</th><th>Focus</th><th>Korean Concept</th><th>Time</th></tr></thead>
        <tbody>{table_rows}</tbody>
      </table>

      <h2>How to Use This Protocol</h2>
      <div class="num-list">
        <div class="num-item">
          <span class="num">01</span>
          <div><h3>Start on Day 1, not Day 7</h3><p>Resist the urge to jump to the 'full protocol.' Each day builds on the previous one. The compounding effect is the point.</p></div>
        </div>
        <div class="num-item">
          <span class="num">02</span>
          <div><h3>Do it for 7 full days before judging</h3><p>The cortisol rhythm takes 3–5 days to begin shifting. Assess on Day 8, not Day 2.</p></div>
        </div>
        <div class="num-item">
          <span class="num">03</span>
          <div><h3>Keep a one-line morning note</h3><p>Each morning, write one sentence: did you wake in the night? What time? This pattern data is useful. Don't skip it.</p></div>
        </div>
      </div>
    </div>
    """
    return page(html, "THE 7-DAY PLAN", "2")


def day_page(d, page_num):
    img = img_url(d["img"])
    n   = int(d["num"])
    html = f"""
    <div class="page-body">

      <!-- ── Day header ── -->
      <div class="day-header">
        <div class="day-header-left">
          <p class="sec-eye">The 3am Protocol</p>
          <h1>{d['title']}</h1>
          <!-- Origin pills — website .about-origin pattern -->
          <div class="origin-row">
            <span class="origin-pill kr"><span style="font-family:'NanumGothic',sans-serif;">{d['hangul']}</span> ({d['roman']})</span>
            <span class="origin-arr">→</span>
            <span class="origin-pill">{d['meaning']}</span>
          </div>
        </div>
        <!-- Dark stat card badge -->
        <div class="day-badge">
          <span class="day-badge-label">DAY</span>
          <span class="day-badge-num">{d['num']}</span>
        </div>
      </div>

      <!-- ── Full-bleed image with gradient overlay ── -->
      <div class="banner-wrap" style="position:relative;">
        <img src="{img}" class="banner" style="height:38mm;" alt="">
        <div style="position:absolute;inset:0;background:linear-gradient(to bottom,transparent 55%,rgba(0,0,0,0.28) 100%);pointer-events:none;"></div>
      </div>

      <!-- ── Intro paragraph ── -->
      <p style="margin-top:5mm;">{d['intro']}</p>

      <!-- ── Morning / Evening cards (website card style) ── -->
      <div class="two-col">
        <div class="col-morning">
          <div class="col-thumb">
            <span class="col-thumb-icon">{ICON_SUN}</span>
            <span class="col-thumb-label">Morning</span>
          </div>
          <div class="col-body"><p>{d['morning']}</p></div>
        </div>
        <div class="col-evening">
          <div class="col-thumb">
            <span class="col-thumb-icon">{ICON_MOON}</span>
            <span class="col-thumb-label">Evening</span>
          </div>
          <div class="col-body"><p>{d['evening']}</p></div>
        </div>
      </div>

      <!-- ── Why this works — bridge strip ── -->
      <div class="why-block">
        <div class="why-head">
          <div class="why-icon">{ICON_SCIENCE}</div>
          <p class="sec-eye" style="margin:0;">Why this works</p>
        </div>
        <p>{d['science']}</p>
      </div>

      <!-- ── Morning check — product card style ── -->
      <div class="callout">
        <div class="callout-border"></div>
        <div class="callout-body">
          <div class="callout-head">
            <div class="callout-icon-badge">{ICON_CHECK}</div>
            <p class="sec-eye" style="margin:0;">Morning check</p>
          </div>
          <p>{d['check']}</p>
        </div>
      </div>

      {progress(n)}
    </div>
    """
    return page(html, f"DAY {d['num']}", str(page_num))


def toolkit_page():
    html = f"""
    <div class="page-body">
      <span class="section-num">08</span>
      <h1>The 3am Toolkit</h1>
      <p class="subtitle">What to do when you wake up anyway</p>

      <p style="margin-top:var(--sp-sm);">Even with the full protocol running, you may still wake occasionally. This is normal — the goal is fewer and shorter wakes, not perfection. What matters is your response. These three responses don't amplify cortisol.</p>

      <div class="num-list" style="margin-top:var(--sp-md);">
        <div class="num-item">
          <span class="num">01</span>
          <div>
            <h3>Stay still and stay dark</h3>
            <p>Do not turn on any light. Do not check your phone or the time. Darkness is the most important signal — light will further suppress melatonin and extend the cortisol response.</p>
          </div>
        </div>
        <div class="num-item">
          <span class="num">02</span>
          <div>
            <h3>4-7-8 breathing</h3>
            <p>Inhale through nose for 4 counts. Hold for 7. Exhale through mouth for 8. Repeat 4 cycles. This activates the parasympathetic nervous system and reduces cortisol within 3–5 minutes.</p>
          </div>
        </div>
        <div class="num-item" style="border-bottom:none;">
          <span class="num">03</span>
          <div>
            <h3>Body scan, not sleep pressure</h3>
            <p>Do not try to force sleep — sleep pressure increases arousal. Scan slowly from feet to head, noticing sensations. This is the Korean myeongseong (<span style="font-family:'NanumGothic',sans-serif;">명상</span>) approach: rest as the goal, not sleep.</p>
          </div>
        </div>
      </div>

      <div class="pull-quote" style="margin-top:auto;">
        <div class="pull-quote-border"></div>
        <blockquote>"After 7 days you will have rebuilt the architecture. The protocol doesn't suppress the waking — it removes the conditions that cause it. There is a difference."</blockquote>
      </div>
    </div>
    """
    return page(html, "THE 3AM TOOLKIT", "10")


def cta_page():
    img = img_url("cta.jpg")
    html = f"""
    <hr class="rule" style="margin:0;">
    <img src="{img}" class="banner" style="height:76mm;" alt="">
    <hr class="rule" style="margin:0 0 0 0;">
    <div class="cta-body">
      <p class="cta-sup">The 3am Protocol is the beginning.</p>
      <h1 class="cta-title">Deep Sleep in 28 Days</h1>
      <p class="cta-desc">The full 28-day circadian reset. Nine modules covering light, temperature, circadian nutrition, Korean evening rituals, HRV tracking, and the integrated daily protocol.</p>

      <div class="cta-box callout">
        <div class="callout-border" style="background:var(--gold);"></div>
        <div class="callout-body" style="text-align:center;">
          <span class="cta-link">lilapark.xyz / products</span>
          <p class="cta-price">$97 · One-time · Instant download</p>
        </div>
      </div>

      <div style="margin-top:auto;text-align:center;">
        <p style="font-family:'Inter',sans-serif;font-size:var(--t-caption);color:var(--text-3);margin-bottom:3pt;">Questions: lila@lilapark.xyz</p>
        <p style="font-family:'Inter',sans-serif;font-size:var(--t-eyebrow);color:var(--text-3);letter-spacing:0.06em;">© 2026 LILA PARK · EVIDENCE-BASED WELLNESS, KOREAN-ROOTED</p>
      </div>
    </div>
    """
    return page(html, "", "11", cls="page-cta")


# ── Build full HTML ────────────────────────────────────────────────────────────
def build_html():
    pages = []
    pages.append(cover_page())
    pages.append(intro_page())
    pages.append(overview_page())
    for i, d in enumerate(DAYS):
        pages.append(day_page(d, i + 3))
    pages.append(toolkit_page())
    pages.append(cta_page())

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
{CSS}
</style>
</head>
<body>
{"".join(pages)}
</body>
</html>"""


# ── Render ─────────────────────────────────────────────────────────────────────
def render():
    html = build_html()
    html_path = Path("/sessions/epic-awesome-gates/3am_v4.html")
    html_path.write_text(html, encoding="utf-8")
    print(f"HTML written: {html_path}")

    out = str(FINAL)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page_   = browser.new_page()
        page_.goto(f"file://{html_path}", wait_until="networkidle")
        page_.pdf(
            path=out,
            format="A4",
            margin={"top":"0","right":"0","bottom":"0","left":"0"},
            print_background=True,
            prefer_css_page_size=True,
        )
        browser.close()

    print(f"✅ PDF: {out}")
    return out


if __name__ == "__main__":
    import sys
    out = render()

    # Quick page-count check
    reader = pypdf.PdfReader(out)
    print(f"Pages: {len(reader.pages)}")
