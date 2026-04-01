#!/usr/bin/env python3
"""
InfoGram Daily Post Generator (Gemini Free Tier)
Generates 30 knowledge articles using Google Gemini API — completely free.

Free tier: 15 requests/min, 1M tokens/day, 1500 requests/day.
We only use 30 requests/day, well within limits.

Usage:
  GEMINI_API_KEY=AIza... python generate.py
"""

import json, os, sys, time, random, hashlib
from datetime import datetime, date
from pathlib import Path
import urllib.request, urllib.error

API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL = "gemini-2.0-flash-lite"  # More generous free tier limits
POSTS_DIR = Path("posts")
NUM_POSTS = 30
MAX_RETRIES = 5

TOPICS = [
    {"id":"ai","label":"Artificial Intelligence","category":"AI & Computing"},
    {"id":"machine-learning","label":"Machine Learning","category":"AI & Computing"},
    {"id":"deep-learning","label":"Deep Learning","category":"AI & Computing"},
    {"id":"robotics","label":"Robotics","category":"AI & Computing"},
    {"id":"computer-vision","label":"Computer Vision","category":"AI & Computing"},
    {"id":"nlp","label":"Natural Language Processing","category":"AI & Computing"},
    {"id":"cybersecurity","label":"Cybersecurity","category":"AI & Computing"},
    {"id":"quantum-computing","label":"Quantum Computing","category":"AI & Computing"},
    {"id":"blockchain","label":"Blockchain & Crypto","category":"AI & Computing"},
    {"id":"cloud-computing","label":"Cloud & Edge Computing","category":"AI & Computing"},
    {"id":"investing","label":"Investing & Markets","category":"Business & Finance"},
    {"id":"startup","label":"Startups & VC","category":"Business & Finance"},
    {"id":"economics","label":"Economics","category":"Business & Finance"},
    {"id":"supply-chain","label":"Supply Chain","category":"Business & Finance"},
    {"id":"procurement","label":"Procurement","category":"Business & Finance"},
    {"id":"real-estate","label":"Real Estate Investing","category":"Business & Finance"},
    {"id":"personal-finance","label":"Personal Finance","category":"Business & Finance"},
    {"id":"crypto-defi","label":"DeFi & Web3","category":"Business & Finance"},
    {"id":"marketing","label":"Marketing & Growth","category":"Business & Finance"},
    {"id":"negotiation","label":"Negotiation & Persuasion","category":"Business & Finance"},
    {"id":"mechanical-eng","label":"Mechanical Engineering","category":"Engineering"},
    {"id":"electrical-eng","label":"Electrical Engineering","category":"Engineering"},
    {"id":"civil-eng","label":"Civil Engineering","category":"Engineering"},
    {"id":"aerospace","label":"Aerospace Engineering","category":"Engineering"},
    {"id":"automotive","label":"Automotive Engineering","category":"Engineering"},
    {"id":"3d-printing","label":"3D Printing","category":"Engineering"},
    {"id":"materials-sci","label":"Materials Science","category":"Engineering"},
    {"id":"renewable-energy","label":"Renewable Energy","category":"Engineering"},
    {"id":"nuclear-energy","label":"Nuclear Energy","category":"Engineering"},
    {"id":"naval-eng","label":"Naval & Marine Engineering","category":"Engineering"},
    {"id":"physics","label":"Physics","category":"Science"},
    {"id":"chemistry","label":"Chemistry","category":"Science"},
    {"id":"biology","label":"Biology","category":"Science"},
    {"id":"astronomy","label":"Astronomy & Space","category":"Science"},
    {"id":"geology","label":"Geology","category":"Science"},
    {"id":"ocean-science","label":"Ocean Science","category":"Science"},
    {"id":"climate-science","label":"Climate Science","category":"Science"},
    {"id":"neuroscience","label":"Neuroscience","category":"Science"},
    {"id":"genetics","label":"Genetics & Genomics","category":"Science"},
    {"id":"paleontology","label":"Paleontology","category":"Science"},
    {"id":"mathematics","label":"Pure Mathematics","category":"Mathematics"},
    {"id":"statistics","label":"Statistics & Probability","category":"Mathematics"},
    {"id":"game-theory","label":"Game Theory","category":"Mathematics"},
    {"id":"cryptography","label":"Cryptography","category":"Mathematics"},
    {"id":"topology","label":"Topology","category":"Mathematics"},
    {"id":"medicine","label":"Medicine & Surgery","category":"Health & Medicine"},
    {"id":"nutrition","label":"Nutrition Science","category":"Health & Medicine"},
    {"id":"psychology","label":"Psychology","category":"Health & Medicine"},
    {"id":"pharmacology","label":"Pharmacology","category":"Health & Medicine"},
    {"id":"epidemiology","label":"Epidemiology","category":"Health & Medicine"},
    {"id":"fitness-science","label":"Exercise Science","category":"Health & Medicine"},
    {"id":"longevity","label":"Longevity & Aging","category":"Health & Medicine"},
    {"id":"biotech","label":"Biotech & Gene Therapy","category":"Health & Medicine"},
    {"id":"space-exploration","label":"Space Exploration","category":"Space"},
    {"id":"moon-missions","label":"Moon Missions","category":"Space"},
    {"id":"mars-colonization","label":"Mars Colonization","category":"Space"},
    {"id":"black-holes","label":"Black Holes & Cosmology","category":"Space"},
    {"id":"satellites","label":"Satellites & GPS","category":"Space"},
    {"id":"astrobiology","label":"Alien Life & Astrobiology","category":"Space"},
    {"id":"geopolitics","label":"Geopolitics","category":"Geopolitics & History"},
    {"id":"ancient-history","label":"Ancient Civilizations","category":"Geopolitics & History"},
    {"id":"world-wars","label":"World Wars","category":"Geopolitics & History"},
    {"id":"cold-war","label":"Cold War & Espionage","category":"Geopolitics & History"},
    {"id":"conspiracy","label":"Conspiracy Theories","category":"Geopolitics & History"},
    {"id":"intelligence","label":"Intelligence Agencies","category":"Geopolitics & History"},
    {"id":"empires","label":"Rise & Fall of Empires","category":"Geopolitics & History"},
    {"id":"future-war","label":"Future of Warfare","category":"Geopolitics & History"},
    {"id":"ux-design","label":"UX/UI Design","category":"Design & Creativity"},
    {"id":"architecture","label":"Architecture","category":"Design & Creativity"},
    {"id":"photography","label":"Photography","category":"Design & Creativity"},
    {"id":"filmmaking","label":"Filmmaking & Cinema","category":"Design & Creativity"},
    {"id":"music-theory","label":"Music Theory","category":"Design & Creativity"},
    {"id":"game-design","label":"Game Design","category":"Design & Creativity"},
    {"id":"philosophy","label":"Philosophy","category":"Philosophy & Mind"},
    {"id":"consciousness","label":"Consciousness","category":"Philosophy & Mind"},
    {"id":"stoicism","label":"Stoicism & Mindset","category":"Philosophy & Mind"},
    {"id":"decision-making","label":"Decision Making & Biases","category":"Philosophy & Mind"},
    {"id":"sleep-science","label":"Sleep Science","category":"Philosophy & Mind"},
    {"id":"meditation","label":"Meditation & Mindfulness","category":"Philosophy & Mind"},
    {"id":"ocean-mammals","label":"Ocean Mammals","category":"Animals & Nature"},
    {"id":"predators","label":"Apex Predators","category":"Animals & Nature"},
    {"id":"deep-sea","label":"Deep Sea Mysteries","category":"Animals & Nature"},
    {"id":"rainforests","label":"Rainforests & Ecosystems","category":"Animals & Nature"},
    {"id":"animal-intelligence","label":"Animal Intelligence","category":"Animals & Nature"},
    {"id":"extinction","label":"Extinction & Conservation","category":"Animals & Nature"},
    {"id":"mega-projects","label":"Mega Engineering Projects","category":"Infrastructure"},
    {"id":"urban-planning","label":"Urban Planning","category":"Infrastructure"},
    {"id":"transportation","label":"Transportation Systems","category":"Infrastructure"},
    {"id":"water-systems","label":"Water & Sanitation","category":"Infrastructure"},
    {"id":"power-grid","label":"Power Grid & Energy","category":"Infrastructure"},
    {"id":"food-science","label":"Food Science","category":"Food & Agriculture"},
    {"id":"fermentation","label":"Fermentation & Brewing","category":"Food & Agriculture"},
    {"id":"agriculture","label":"Agriculture & Farming","category":"Food & Agriculture"},
    {"id":"food-supply","label":"Global Food Systems","category":"Food & Agriculture"},
    {"id":"semiconductors","label":"Semiconductors","category":"Tech & Hardware"},
    {"id":"ev-tech","label":"Electric Vehicles","category":"Tech & Hardware"},
    {"id":"ar-vr","label":"AR/VR & Spatial Computing","category":"Tech & Hardware"},
    {"id":"drones","label":"Drones & UAVs","category":"Tech & Hardware"},
    {"id":"biocomputing","label":"Biocomputing","category":"Tech & Hardware"},
    {"id":"internet-infra","label":"Internet Infrastructure","category":"Tech & Hardware"},
    {"id":"sports-analytics","label":"Sports Analytics","category":"Sports"},
    {"id":"f1","label":"Formula 1 Engineering","category":"Sports"},
    {"id":"human-performance","label":"Human Performance","category":"Sports"},
    {"id":"sports-psychology","label":"Sports Psychology","category":"Sports"},
    {"id":"memory-learning","label":"Memory & Learning","category":"Learning & Leadership"},
    {"id":"speed-reading","label":"Speed Reading","category":"Learning & Leadership"},
    {"id":"systems-thinking","label":"Systems Thinking","category":"Learning & Leadership"},
    {"id":"leadership","label":"Leadership","category":"Learning & Leadership"},
]

PROMPT_TEMPLATES = [
    "Explain the most fundamental concept in {label}. What must every beginner understand first? Include real-world examples and actual numbers.",
    "What is the most counterintuitive or mind-blowing fact about {label}? Explain why it defies common sense with the science/math behind it.",
    "How is {label} changing RIGHT NOW in 2025-2026? Cover the latest breakthroughs, trends, and expert predictions. Be specific with names and numbers.",
    "What is the most important formula, equation, or principle in {label}? Derive it from first principles and show a practical worked example.",
    "What is the biggest unsolved mystery or open debate in {label}? Why hasn't it been solved? What are the competing theories?",
    "Tell the story of the most important breakthrough in {label} history. Who did it, what obstacles, and why does it still matter today?",
    "Explain how something in {label} works at a DEEP technical level. Pick one specific mechanism and walk through it step-by-step with math.",
    "What are the 3 biggest misconceptions about {label}? Debunk each with hard evidence, real data, and clear logic.",
]


def daily_seed():
    return int(hashlib.md5(str(date.today()).encode()).hexdigest()[:8], 16)


def pick_topics_and_prompts(n=30):
    rng = random.Random(daily_seed())
    by_cat = {}
    for t in TOPICS:
        by_cat.setdefault(t["category"], []).append(t)

    selections = []
    for cat, topics in by_cat.items():
        topic = rng.choice(topics)
        prompt = rng.choice(PROMPT_TEMPLATES).format(**topic)
        selections.append((topic, prompt))

    used = {(s[0]["id"], s[1][:50]) for s in selections}
    all_topics = list(TOPICS)
    rng.shuffle(all_topics)
    idx = 0
    while len(selections) < n:
        topic = all_topics[idx % len(all_topics)]
        prompt = rng.choice(PROMPT_TEMPLATES).format(**topic)
        key = (topic["id"], prompt[:50])
        if key not in used:
            selections.append((topic, prompt))
            used.add(key)
        idx += 1
        if idx > n * 5:
            break
    return selections[:n]


def call_gemini(topic, prompt):
    """Call Google Gemini API (free tier) with grounding via Google Search."""

    user_prompt = f"""You are a brilliant knowledge content creator for InfoGram, an addictive learning feed app. Create an in-depth educational article.

TOPIC: {topic['label']} (Category: {topic['category']})
PROMPT: {prompt}

CRITICAL REQUIREMENTS:
- Write 600-1000 words (4-6 minute read, NOT a short blurb)
- Be SPECIFIC: real names, real numbers, real dates, real formulas
- Include at least one worked mathematical example or numerical calculation
- Hook the reader in the first sentence — make them unable to stop reading
- Use current 2024-2025 information where relevant

FORMAT — Respond ONLY with valid JSON, no markdown fences, no extra text:
{{
  "title": "Catchy specific headline, max 10 words",
  "content": "Full article. Use ## for section headers. Use **bold** for key terms. Use `backtick` for formulas/code/values. Use [FORMULA] ... [/FORMULA] for standalone equations. Use [INSIGHT] ... [/INSIGHT] for 1-2 key takeaways. Must be 600-1000 words.",
  "difficulty": "Fundamentals" or "Intermediate" or "Advanced",
  "readTime": "4-6",
  "imageQuery": "2-3 word unsplash search query for a relevant hero image"
}}"""

    body = json.dumps({
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json",
        },
        "tools": [{"google_search": {}}],
    }).encode()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=120)
    data = json.loads(resp.read())

    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError(f"No candidates: {json.dumps(data)[:300]}")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = ""
    for part in parts:
        if "text" in part:
            text += part["text"]

    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    return json.loads(text)


def generate_post(topic, prompt, index):
    for attempt in range(MAX_RETRIES):
        try:
            print(f"  [{index+1}/{NUM_POSTS}] {topic['label']}: {prompt[:60]}...")
            result = call_gemini(topic, prompt)

            post_id = hashlib.md5(
                f"{date.today()}-{topic['id']}-{prompt[:30]}".encode()
            ).hexdigest()[:12]
            result["id"] = post_id
            result["topicId"] = topic["id"]
            result["category"] = topic["category"]
            result["generatedAt"] = datetime.utcnow().isoformat() + "Z"

            word_count = len(result.get("content", "").split())
            print(f"    ✓ \"{result['title']}\" ({word_count} words, {result.get('difficulty', '')})")
            return result

        except Exception as e:
            print(f"    ✗ Attempt {attempt+1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                wait = 10 * (attempt + 1)  # 10s, 20s, 30s, 40s backoff
                print(f"    ⏳ Waiting {wait}s before retry...")
                time.sleep(wait)
    return None


def main():
    if not API_KEY:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        print("Get your FREE key at: https://aistudio.google.com/apikey")
        sys.exit(1)

    today = str(date.today())
    print(f"\n🔬 InfoGram Daily Generator (Gemini Free) — {today}")
    print(f"   Model: {MODEL}")
    print(f"   Generating {NUM_POSTS} articles...\n")

    POSTS_DIR.mkdir(exist_ok=True)

    selections = pick_topics_and_prompts(NUM_POSTS)
    posts = []
    failed = 0

    for i, (topic, prompt) in enumerate(selections):
        post = generate_post(topic, prompt, i)
        if post:
            posts.append(post)
        else:
            failed += 1
        # 8s delay between requests — safe for new API keys
        if i < len(selections) - 1:
            time.sleep(8)

    output_path = POSTS_DIR / f"{today}.json"
    with open(output_path, "w") as f:
        json.dump(posts, f, indent=2)

    print(f"\n{'='*50}")
    print(f"✅ Generated {len(posts)} posts ({failed} failed)")
    print(f"📁 Saved to {output_path}")
    print(f"💰 Cost: $0.00 (Gemini free tier)")

    cats = {}
    for p in posts:
        cats[p["category"]] = cats.get(p["category"], 0) + 1
    print(f"\n📊 Category breakdown:")
    for cat, count in sorted(cats.items()):
        print(f"   {cat}: {count}")

    words = [len(p.get("content", "").split()) for p in posts]
    if words:
        print(f"\n📝 Words: min={min(words)}, max={max(words)}, avg={sum(words)//len(words)}")

    if failed > 5:
        print(f"\n⚠️  {failed} posts failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
