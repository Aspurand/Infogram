#!/usr/bin/env python3 -u
"""
InfoGram Daily Post Generator v4 (Gemini Free Tier)

v4 fixes:
- FORCE UNBUFFERED OUTPUT (this is why v3 showed no logs in GitHub Actions)
- Shorter API timeout (30s instead of 120s) so failed calls don't hang
- sys.stdout.flush() after every print
- No google_search grounding (caused all 429s)
- Batch generation: 3 batches of 10 with 60s cooldown

Usage: GEMINI_API_KEY=AIza... python -u generate.py
"""

import json, os, sys, time, random, hashlib
from datetime import datetime, date
from pathlib import Path
import urllib.request, urllib.error

# CRITICAL: Force unbuffered stdout so GitHub Actions shows output in real time
sys.stdout.reconfigure(line_buffering=True)

def log(msg):
    """Print with guaranteed flush."""
    print(msg)
    sys.stdout.flush()

API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL = "gemini-2.0-flash"
POSTS_DIR = Path("posts")
NUM_POSTS = 30
MAX_RETRIES = 3
BATCH_SIZE = 10
BATCH_COOLDOWN = 60
API_TIMEOUT = 30  # seconds — fail fast, don't hang

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

IMG_QUERIES = {
    "ai":"artificial+intelligence+neural+network","machine-learning":"machine+learning+algorithm+data",
    "deep-learning":"deep+learning+neural+network+layers","robotics":"robot+arm+automation+factory",
    "computer-vision":"computer+vision+object+detection","nlp":"natural+language+processing+chatbot",
    "cybersecurity":"cybersecurity+hacking+digital+lock","quantum-computing":"quantum+computer+processor+chip",
    "blockchain":"blockchain+cryptocurrency+bitcoin+ledger","cloud-computing":"cloud+computing+server+data+center",
    "investing":"stock+market+trading+chart+wall+street","startup":"startup+office+silicon+valley+team",
    "economics":"economics+market+graph+finance","supply-chain":"logistics+warehouse+shipping+container",
    "procurement":"procurement+contract+business+negotiation","real-estate":"real+estate+property+house+skyline",
    "personal-finance":"savings+money+budget+piggy+bank","crypto-defi":"defi+crypto+ethereum+web3",
    "marketing":"marketing+advertising+digital+campaign","negotiation":"negotiation+handshake+business+deal",
    "mechanical-eng":"engine+gears+machinery+mechanical","electrical-eng":"circuit+board+electronics+wiring",
    "civil-eng":"bridge+construction+steel+engineering","aerospace":"jet+engine+aerospace+aircraft",
    "automotive":"car+engine+turbo+automotive+racing","3d-printing":"3d+printing+additive+manufacturing",
    "materials-sci":"materials+science+alloy+microscope","renewable-energy":"solar+panel+wind+turbine+energy",
    "nuclear-energy":"nuclear+power+plant+reactor+cooling","naval-eng":"ship+engineering+naval+vessel+ocean",
    "physics":"physics+particle+accelerator+quantum","chemistry":"chemistry+molecules+laboratory+flask",
    "biology":"biology+cell+microscope+dna+organism","astronomy":"space+galaxy+nebula+telescope+stars",
    "geology":"volcano+geology+earth+rocks+layers","ocean-science":"ocean+research+submarine+marine",
    "climate-science":"climate+earth+atmosphere+global","neuroscience":"brain+neuron+synapse+scan",
    "genetics":"dna+genetics+genome+helix+sequencing","paleontology":"dinosaur+fossil+excavation+skeleton",
    "mathematics":"mathematics+fractal+geometry+equation","statistics":"statistics+data+chart+bell+curve",
    "game-theory":"chess+strategy+game+theory+board","cryptography":"cryptography+cipher+code+encryption",
    "topology":"topology+mobius+strip+geometry+knot","medicine":"hospital+surgery+medical+doctor",
    "nutrition":"nutrition+healthy+food+vitamins","psychology":"psychology+mind+therapy+brain+couch",
    "pharmacology":"pharmacy+medicine+drug+pill+molecular","epidemiology":"virus+pandemic+disease+spread+map",
    "fitness-science":"fitness+gym+exercise+muscle+training","longevity":"aging+longevity+science+health",
    "biotech":"biotech+laboratory+gene+therapy+dna","space-exploration":"space+shuttle+launch+rocket+nasa",
    "moon-missions":"moon+landing+lunar+apollo+astronaut","mars-colonization":"mars+planet+rover+colony+red",
    "black-holes":"black+hole+cosmos+singularity+space","satellites":"satellite+orbit+earth+space+gps",
    "astrobiology":"alien+exoplanet+telescope+search+life","geopolitics":"geopolitics+world+map+globe+diplomacy",
    "ancient-history":"ancient+rome+egypt+pyramid+ruins","world-wars":"world+war+military+tank+history",
    "cold-war":"cold+war+spy+berlin+wall+espionage","conspiracy":"conspiracy+mystery+eye+pyramid+secret",
    "intelligence":"spy+intelligence+secret+agent+cia","empires":"empire+castle+kingdom+medieval+throne",
    "future-war":"military+drone+cyber+warfare+future","ux-design":"ux+design+interface+wireframe+app",
    "architecture":"architecture+modern+building+design","photography":"photography+camera+lens+portrait",
    "filmmaking":"filmmaking+cinema+director+movie+set","music-theory":"music+piano+notes+sheet+theory",
    "game-design":"game+design+controller+development","philosophy":"philosophy+thinker+ancient+wisdom",
    "consciousness":"consciousness+mind+awareness+light","stoicism":"stoic+marble+statue+philosophy",
    "decision-making":"decision+brain+choices+bias+fork","sleep-science":"sleep+brain+dreams+night+bed",
    "meditation":"meditation+zen+peaceful+nature+calm","ocean-mammals":"dolphin+whale+ocean+marine+humpback",
    "predators":"lion+predator+wildlife+safari+hunt","deep-sea":"deep+sea+anglerfish+abyss+ocean",
    "rainforests":"rainforest+tropical+jungle+canopy+green","animal-intelligence":"octopus+intelligent+animal+brain",
    "extinction":"endangered+species+conservation+panda","mega-projects":"bridge+dam+mega+engineering+project",
    "urban-planning":"city+skyline+urban+planning+aerial","transportation":"bullet+train+railway+transportation",
    "water-systems":"water+dam+reservoir+treatment+clean","power-grid":"power+grid+electricity+tower+lines",
    "food-science":"food+science+molecular+gastronomy","fermentation":"fermentation+brewing+craft+beer+yeast",
    "agriculture":"farm+agriculture+harvest+field+tractor","food-supply":"food+supply+global+market+grain",
    "semiconductors":"semiconductor+chip+silicon+wafer+clean","ev-tech":"electric+car+tesla+battery+charging",
    "ar-vr":"virtual+reality+headset+ar+immersive","drones":"drone+uav+aerial+quadcopter+flying",
    "biocomputing":"biocomputing+dna+molecular+storage","internet-infra":"internet+submarine+cable+fiber+optic",
    "sports-analytics":"sports+analytics+stadium+data+screen","f1":"formula+one+racing+pit+stop+car",
    "human-performance":"athlete+running+performance+track","sports-psychology":"athlete+mental+focus+training+meditation",
    "memory-learning":"memory+brain+study+learning+books","speed-reading":"books+library+reading+knowledge+fast",
    "systems-thinking":"systems+diagram+flow+thinking+map","leadership":"leadership+ceo+business+meeting+team",
}

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


def make_image_url(topic_id, title):
    query = IMG_QUERIES.get(topic_id, "knowledge+science+technology")
    sig = hashlib.md5(f"{date.today()}-{title}".encode()).hexdigest()[:8]
    return f"https://source.unsplash.com/800x450/?{query}&sig={sig}"


def call_gemini(topic, prompt):
    """Call Gemini API. No grounding tools. Short timeout."""

    user_prompt = f"""You are a brilliant knowledge content creator for InfoGram, an addictive learning feed. Create an in-depth educational article.

TOPIC: {topic['label']} (Category: {topic['category']})
PROMPT: {prompt}

REQUIREMENTS:
- Write 600-1000 words (4-6 minute deep read)
- Be SPECIFIC: real names, real numbers, real dates, real formulas
- Include at least one worked mathematical example with actual numbers
- Hook the reader in the first sentence
- Write as if you have the latest 2025 knowledge

Respond ONLY with valid JSON, no markdown fences:
{{
  "title": "Catchy specific headline, max 10 words",
  "content": "Full 600-1000 word article. Use ## for section headers. Use **bold** for key terms. Use `backtick` for formulas/values. Use [FORMULA] ... [/FORMULA] for standalone equations. Use [INSIGHT] ... [/INSIGHT] for 1-2 key takeaways.",
  "difficulty": "Fundamentals" or "Intermediate" or "Advanced",
  "readTime": "5"
}}"""

    body = json.dumps({
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json",
        },
    }).encode()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=API_TIMEOUT)
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
    for prefix in ["```json", "```"]:
        if text.startswith(prefix):
            text = text[len(prefix):]
    if text.endswith("```"):
        text = text[:-3]

    return json.loads(text.strip())


def generate_post(topic, prompt, index):
    for attempt in range(MAX_RETRIES):
        try:
            log(f"  [{index+1}/{NUM_POSTS}] {topic['label']}: {prompt[:55]}...")
            result = call_gemini(topic, prompt)

            post_id = hashlib.md5(
                f"{date.today()}-{topic['id']}-{prompt[:30]}".encode()
            ).hexdigest()[:12]

            result["id"] = post_id
            result["topicId"] = topic["id"]
            result["category"] = topic["category"]
            result["imageUrl"] = make_image_url(topic["id"], result.get("title", ""))
            result["imageQuery"] = IMG_QUERIES.get(topic["id"], "knowledge+science")
            result["generatedAt"] = datetime.utcnow().isoformat() + "Z"

            wc = len(result.get("content", "").split())
            log(f"    ✓ \"{result['title']}\" ({wc} words)")
            return result

        except urllib.error.HTTPError as e:
            log(f"    ✗ Attempt {attempt+1}: HTTP {e.code}")
            if e.code == 429 and attempt < MAX_RETRIES - 1:
                wait = 30 * (attempt + 1)
                log(f"    ⏳ Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            elif attempt < MAX_RETRIES - 1:
                time.sleep(5)
            else:
                log(f"    ✗ All {MAX_RETRIES} attempts failed")

        except Exception as e:
            log(f"    ✗ Attempt {attempt+1}: {type(e).__name__}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(5)
            else:
                log(f"    ✗ All {MAX_RETRIES} attempts failed")
    return None


def main():
    log("=" * 50)
    log("InfoGram Generator v4")
    log("=" * 50)

    if not API_KEY:
        log("ERROR: GEMINI_API_KEY not set")
        log("Get free key: https://aistudio.google.com/apikey")
        sys.exit(1)

    log(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]}")
    log(f"Model: {MODEL}")
    log(f"Date: {date.today()}")
    log(f"Posts: {NUM_POSTS}")
    log(f"Batches: {NUM_POSTS // BATCH_SIZE} x {BATCH_SIZE}")
    log(f"Timeout per request: {API_TIMEOUT}s")
    log("")

    POSTS_DIR.mkdir(exist_ok=True)

    # Quick API test first
    log("Testing API connection...")
    try:
        test_url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}?key={API_KEY}"
        test_req = urllib.request.Request(test_url)
        test_resp = urllib.request.urlopen(test_req, timeout=10)
        log(f"  ✓ API connected (status {test_resp.status})")
    except Exception as e:
        log(f"  ✗ API connection failed: {e}")
        log("  Check your GEMINI_API_KEY secret")
        sys.exit(1)

    log("")
    selections = pick_topics_and_prompts(NUM_POSTS)
    posts = []
    failed = 0

    for batch_num in range(0, len(selections), BATCH_SIZE):
        batch = selections[batch_num:batch_num + BATCH_SIZE]
        batch_idx = batch_num // BATCH_SIZE + 1
        total_batches = (len(selections) + BATCH_SIZE - 1) // BATCH_SIZE

        log(f"── Batch {batch_idx}/{total_batches} ({len(batch)} articles) ──")

        for i, (topic, prompt) in enumerate(batch):
            post = generate_post(topic, prompt, batch_num + i)
            if post:
                posts.append(post)
            else:
                failed += 1
            if i < len(batch) - 1:
                time.sleep(3)

        if batch_num + BATCH_SIZE < len(selections):
            log(f"  ⏸️  Cooling down {BATCH_COOLDOWN}s...")
            time.sleep(BATCH_COOLDOWN)

    output_path = POSTS_DIR / f"{date.today()}.json"
    with open(output_path, "w") as f:
        json.dump(posts, f, indent=2)

    log("")
    log("=" * 50)
    log(f"✅ Done! {len(posts)} articles, {failed} failed")
    log(f"📁 {output_path}")
    log(f"💰 Cost: $0.00")

    cats = {}
    for p in posts:
        cats[p["category"]] = cats.get(p["category"], 0) + 1
    log("\nBreakdown:")
    for cat, count in sorted(cats.items()):
        log(f"  {cat}: {count}")

    words = [len(p.get("content", "").split()) for p in posts]
    if words:
        log(f"\nWords: min={min(words)} max={max(words)} avg={sum(words)//len(words)}")

    if len(posts) == 0:
        log("\n❌ FATAL: Zero posts generated!")
        sys.exit(1)
    if failed > 10:
        log(f"\n⚠️  {failed} failures")
        sys.exit(1)

    log("\n🎉 Feed ready!")


if __name__ == "__main__":
    main()
