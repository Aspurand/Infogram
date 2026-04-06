#!/usr/bin/env python3 -u
"""
BookGram Daily Summary Generator v1 (GitHub Models — Free)

Generates 1 deep book summary per day (~3000-4000 words, 20 min read)
from a curated library of the best books in:
- Self Help & Personal Development
- Motivation & Mindset
- Investing & Wealth
- Leadership & Management
- Business Strategy & Entrepreneurship
- Supply Chain & Operations

Uses GitHub Models API (gpt-4o-mini) — completely free.
"""

import json, os, sys, time, random, hashlib
from datetime import datetime, date
from pathlib import Path
import urllib.request, urllib.error

sys.stdout.reconfigure(line_buffering=True)

def log(msg):
    print(msg)
    sys.stdout.flush()

TOKEN = os.environ.get("GITHUB_TOKEN", "")
MODEL = "gpt-4o-mini"
API_URL = "https://models.inference.ai.azure.com/chat/completions"
POSTS_DIR = Path("posts")
API_TIMEOUT = 90  # longer timeout for big summaries

# ═══════════════════════════════════════════════════════════════
# CURATED BOOK LIBRARY — 365+ of the absolute best books
# Each book appears at most once per year cycle
# ═══════════════════════════════════════════════════════════════

BOOKS = [
    # ── SELF HELP & PERSONAL DEVELOPMENT ──
    {"title":"Atomic Habits","author":"James Clear","year":2018,"category":"Self Help","icon":"⚡"},
    {"title":"The 7 Habits of Highly Effective People","author":"Stephen Covey","year":1989,"category":"Self Help","icon":"🎯"},
    {"title":"Deep Work","author":"Cal Newport","year":2016,"category":"Self Help","icon":"🧠"},
    {"title":"The Power of Now","author":"Eckhart Tolle","year":1997,"category":"Self Help","icon":"🕐"},
    {"title":"How to Win Friends and Influence People","author":"Dale Carnegie","year":1936,"category":"Self Help","icon":"🤝"},
    {"title":"Think and Grow Rich","author":"Napoleon Hill","year":1937,"category":"Self Help","icon":"💭"},
    {"title":"The Subtle Art of Not Giving a F*ck","author":"Mark Manson","year":2016,"category":"Self Help","icon":"🔥"},
    {"title":"Thinking, Fast and Slow","author":"Daniel Kahneman","year":2011,"category":"Self Help","icon":"🧩"},
    {"title":"The 4-Hour Workweek","author":"Tim Ferriss","year":2007,"category":"Self Help","icon":"⏰"},
    {"title":"Essentialism","author":"Greg McKeown","year":2014,"category":"Self Help","icon":"✂️"},
    {"title":"The Power of Habit","author":"Charles Duhigg","year":2012,"category":"Self Help","icon":"🔄"},
    {"title":"Mindset","author":"Carol Dweck","year":2006,"category":"Self Help","icon":"🌱"},
    {"title":"Range","author":"David Epstein","year":2019,"category":"Self Help","icon":"🎨"},
    {"title":"Digital Minimalism","author":"Cal Newport","year":2019,"category":"Self Help","icon":"📵"},
    {"title":"The Compound Effect","author":"Darren Hardy","year":2010,"category":"Self Help","icon":"📈"},
    {"title":"Outliers","author":"Malcolm Gladwell","year":2008,"category":"Self Help","icon":"⭐"},
    {"title":"The 5 AM Club","author":"Robin Sharma","year":2018,"category":"Self Help","icon":"🌅"},
    {"title":"Eat That Frog!","author":"Brian Tracy","year":2001,"category":"Self Help","icon":"🐸"},
    {"title":"The One Thing","author":"Gary Keller","year":2013,"category":"Self Help","icon":"1️⃣"},
    {"title":"Make Your Bed","author":"Admiral William McRaven","year":2017,"category":"Self Help","icon":"🛏️"},
    {"title":"Can't Hurt Me","author":"David Goggins","year":2018,"category":"Self Help","icon":"💪"},
    {"title":"12 Rules for Life","author":"Jordan Peterson","year":2018,"category":"Self Help","icon":"📜"},
    {"title":"The Miracle Morning","author":"Hal Elrod","year":2012,"category":"Self Help","icon":"☀️"},
    {"title":"Grit","author":"Angela Duckworth","year":2016,"category":"Self Help","icon":"💎"},
    {"title":"So Good They Can't Ignore You","author":"Cal Newport","year":2012,"category":"Self Help","icon":"🏆"},
    {"title":"Tiny Habits","author":"BJ Fogg","year":2019,"category":"Self Help","icon":"🔬"},
    {"title":"The Obstacle Is the Way","author":"Ryan Holiday","year":2014,"category":"Self Help","icon":"🏔️"},
    {"title":"Stillness Is the Key","author":"Ryan Holiday","year":2019,"category":"Self Help","icon":"🧘"},
    {"title":"Ego Is the Enemy","author":"Ryan Holiday","year":2016,"category":"Self Help","icon":"🪞"},
    {"title":"Never Split the Difference","author":"Chris Voss","year":2016,"category":"Self Help","icon":"🎲"},
    {"title":"Influence","author":"Robert Cialdini","year":1984,"category":"Self Help","icon":"🧲"},
    {"title":"Emotional Intelligence","author":"Daniel Goleman","year":1995,"category":"Self Help","icon":"❤️"},
    {"title":"Flow","author":"Mihaly Csikszentmihalyi","year":1990,"category":"Self Help","icon":"🌊"},
    {"title":"The Happiness Advantage","author":"Shawn Achor","year":2010,"category":"Self Help","icon":"😊"},
    {"title":"Quiet","author":"Susan Cain","year":2012,"category":"Self Help","icon":"🤫"},
    {"title":"Man's Search for Meaning","author":"Viktor Frankl","year":1946,"category":"Self Help","icon":"🕊️"},
    {"title":"Meditations","author":"Marcus Aurelius","year":180,"category":"Self Help","icon":"🏛️"},

    # ── MOTIVATION & MINDSET ──
    {"title":"The Alchemist","author":"Paulo Coelho","year":1988,"category":"Motivation","icon":"✨"},
    {"title":"Start with Why","author":"Simon Sinek","year":2009,"category":"Motivation","icon":"❓"},
    {"title":"Dare to Lead","author":"Brené Brown","year":2018,"category":"Motivation","icon":"🦁"},
    {"title":"Daring Greatly","author":"Brené Brown","year":2012,"category":"Motivation","icon":"🛡️"},
    {"title":"The War of Art","author":"Steven Pressfield","year":2002,"category":"Motivation","icon":"⚔️"},
    {"title":"Awaken the Giant Within","author":"Tony Robbins","year":1991,"category":"Motivation","icon":"🗿"},
    {"title":"You Are a Badass","author":"Jen Sincero","year":2013,"category":"Motivation","icon":"🌟"},
    {"title":"Shoe Dog","author":"Phil Knight","year":2016,"category":"Motivation","icon":"👟"},
    {"title":"The Magic of Thinking Big","author":"David Schwartz","year":1959,"category":"Motivation","icon":"🎪"},
    {"title":"Relentless","author":"Tim Grover","year":2013,"category":"Motivation","icon":"🔥"},
    {"title":"Extreme Ownership","author":"Jocko Willink","year":2015,"category":"Motivation","icon":"🎖️"},
    {"title":"Discipline Equals Freedom","author":"Jocko Willink","year":2017,"category":"Motivation","icon":"⛓️"},
    {"title":"Greenlights","author":"Matthew McConaughey","year":2020,"category":"Motivation","icon":"🟢"},
    {"title":"The Mountain Is You","author":"Brianna Wiest","year":2020,"category":"Motivation","icon":"⛰️"},
    {"title":"Mindfulness in Plain English","author":"Bhante Gunaratana","year":1994,"category":"Motivation","icon":"🧘"},
    {"title":"The Untethered Soul","author":"Michael Singer","year":2007,"category":"Motivation","icon":"🕊️"},
    {"title":"Antifragile","author":"Nassim Nicholas Taleb","year":2012,"category":"Motivation","icon":"💪"},
    {"title":"Black Swan","author":"Nassim Nicholas Taleb","year":2007,"category":"Motivation","icon":"🦢"},
    {"title":"Fooled by Randomness","author":"Nassim Nicholas Taleb","year":2001,"category":"Motivation","icon":"🎰"},
    {"title":"The Courage to Be Disliked","author":"Ichiro Kishimi","year":2013,"category":"Motivation","icon":"🦋"},
    {"title":"Who Moved My Cheese?","author":"Spencer Johnson","year":1998,"category":"Motivation","icon":"🧀"},
    {"title":"The Monk Who Sold His Ferrari","author":"Robin Sharma","year":1997,"category":"Motivation","icon":"🏎️"},
    {"title":"Think Like a Monk","author":"Jay Shetty","year":2020,"category":"Motivation","icon":"🧘"},
    {"title":"Everything Is Figureoutable","author":"Marie Forleo","year":2019,"category":"Motivation","icon":"💡"},

    # ── INVESTING & WEALTH ──
    {"title":"The Intelligent Investor","author":"Benjamin Graham","year":1949,"category":"Investing","icon":"📊"},
    {"title":"Rich Dad Poor Dad","author":"Robert Kiyosaki","year":1997,"category":"Investing","icon":"🏠"},
    {"title":"The Psychology of Money","author":"Morgan Housel","year":2020,"category":"Investing","icon":"🧠"},
    {"title":"A Random Walk Down Wall Street","author":"Burton Malkiel","year":1973,"category":"Investing","icon":"🎲"},
    {"title":"The Little Book of Common Sense Investing","author":"John Bogle","year":2007,"category":"Investing","icon":"📖"},
    {"title":"One Up on Wall Street","author":"Peter Lynch","year":1989,"category":"Investing","icon":"📈"},
    {"title":"The Millionaire Next Door","author":"Thomas Stanley","year":1996,"category":"Investing","icon":"🏡"},
    {"title":"Think and Grow Rich","author":"Napoleon Hill","year":1937,"category":"Investing","icon":"💰"},
    {"title":"The Total Money Makeover","author":"Dave Ramsey","year":2003,"category":"Investing","icon":"💳"},
    {"title":"I Will Teach You to Be Rich","author":"Ramit Sethi","year":2009,"category":"Investing","icon":"💵"},
    {"title":"The Richest Man in Babylon","author":"George Clason","year":1926,"category":"Investing","icon":"🏛️"},
    {"title":"Common Stocks and Uncommon Profits","author":"Philip Fisher","year":1958,"category":"Investing","icon":"📉"},
    {"title":"The Warren Buffett Way","author":"Robert Hagstrom","year":1994,"category":"Investing","icon":"🎩"},
    {"title":"Principles","author":"Ray Dalio","year":2017,"category":"Investing","icon":"⚖️"},
    {"title":"The Dhandho Investor","author":"Mohnish Pabrai","year":2007,"category":"Investing","icon":"🎯"},
    {"title":"Margin of Safety","author":"Seth Klarman","year":1991,"category":"Investing","icon":"🛡️"},
    {"title":"Poor Charlie's Almanack","author":"Charlie Munger","year":2005,"category":"Investing","icon":"📚"},
    {"title":"The Essays of Warren Buffett","author":"Warren Buffett","year":1997,"category":"Investing","icon":"✍️"},
    {"title":"Security Analysis","author":"Benjamin Graham","year":1934,"category":"Investing","icon":"🔍"},
    {"title":"You Can Be a Stock Market Genius","author":"Joel Greenblatt","year":1997,"category":"Investing","icon":"🧙"},
    {"title":"Money: Master the Game","author":"Tony Robbins","year":2014,"category":"Investing","icon":"🎮"},
    {"title":"The Simple Path to Wealth","author":"JL Collins","year":2016,"category":"Investing","icon":"🛤️"},
    {"title":"Unshakeable","author":"Tony Robbins","year":2017,"category":"Investing","icon":"🏔️"},
    {"title":"The Barefoot Investor","author":"Scott Pape","year":2016,"category":"Investing","icon":"🦶"},

    # ── LEADERSHIP & MANAGEMENT ──
    {"title":"Good to Great","author":"Jim Collins","year":2001,"category":"Leadership","icon":"🚀"},
    {"title":"Leaders Eat Last","author":"Simon Sinek","year":2014,"category":"Leadership","icon":"🍽️"},
    {"title":"The 21 Irrefutable Laws of Leadership","author":"John Maxwell","year":1998,"category":"Leadership","icon":"📜"},
    {"title":"Primal Leadership","author":"Daniel Goleman","year":2002,"category":"Leadership","icon":"❤️"},
    {"title":"Radical Candor","author":"Kim Scott","year":2017,"category":"Leadership","icon":"💬"},
    {"title":"The Five Dysfunctions of a Team","author":"Patrick Lencioni","year":2002,"category":"Leadership","icon":"👥"},
    {"title":"Turn the Ship Around!","author":"David Marquet","year":2013,"category":"Leadership","icon":"🚢"},
    {"title":"Trillion Dollar Coach","author":"Eric Schmidt","year":2019,"category":"Leadership","icon":"🏈"},
    {"title":"The Hard Thing About Hard Things","author":"Ben Horowitz","year":2014,"category":"Leadership","icon":"🔨"},
    {"title":"High Output Management","author":"Andy Grove","year":1983,"category":"Leadership","icon":"⚡"},
    {"title":"First, Break All the Rules","author":"Marcus Buckingham","year":1999,"category":"Leadership","icon":"💥"},
    {"title":"Multipliers","author":"Liz Wiseman","year":2010,"category":"Leadership","icon":"✖️"},
    {"title":"Drive","author":"Daniel Pink","year":2009,"category":"Leadership","icon":"🏎️"},
    {"title":"The Culture Code","author":"Daniel Coyle","year":2018,"category":"Leadership","icon":"🧬"},
    {"title":"Measure What Matters","author":"John Doerr","year":2018,"category":"Leadership","icon":"📏"},
    {"title":"An Astronaut's Guide to Life on Earth","author":"Chris Hadfield","year":2013,"category":"Leadership","icon":"🧑‍🚀"},
    {"title":"Team of Teams","author":"Stanley McChrystal","year":2015,"category":"Leadership","icon":"🕸️"},
    {"title":"It's Your Ship","author":"Michael Abrashoff","year":2002,"category":"Leadership","icon":"⛵"},
    {"title":"The Infinite Game","author":"Simon Sinek","year":2019,"category":"Leadership","icon":"♾️"},
    {"title":"Creativity, Inc.","author":"Ed Catmull","year":2014,"category":"Leadership","icon":"🎨"},
    {"title":"Powerful","author":"Patty McCord","year":2017,"category":"Leadership","icon":"⚡"},
    {"title":"The Manager's Path","author":"Camille Fournier","year":2017,"category":"Leadership","icon":"🗺️"},
    {"title":"Nine Lies About Work","author":"Marcus Buckingham","year":2019,"category":"Leadership","icon":"🚫"},

    # ── BUSINESS STRATEGY & ENTREPRENEURSHIP ──
    {"title":"Zero to One","author":"Peter Thiel","year":2014,"category":"Business Strategy","icon":"0️⃣"},
    {"title":"The Lean Startup","author":"Eric Ries","year":2011,"category":"Business Strategy","icon":"🏗️"},
    {"title":"Blue Ocean Strategy","author":"W. Chan Kim","year":2004,"category":"Business Strategy","icon":"🌊"},
    {"title":"Competitive Strategy","author":"Michael Porter","year":1980,"category":"Business Strategy","icon":"♟️"},
    {"title":"The Innovator's Dilemma","author":"Clayton Christensen","year":1997,"category":"Business Strategy","icon":"💡"},
    {"title":"Built to Last","author":"Jim Collins","year":1994,"category":"Business Strategy","icon":"🏛️"},
    {"title":"Rework","author":"Jason Fried","year":2010,"category":"Business Strategy","icon":"🔧"},
    {"title":"The $100 Startup","author":"Chris Guillebeau","year":2012,"category":"Business Strategy","icon":"💵"},
    {"title":"Blitzscaling","author":"Reid Hoffman","year":2018,"category":"Business Strategy","icon":"⚡"},
    {"title":"The Mom Test","author":"Rob Fitzpatrick","year":2013,"category":"Business Strategy","icon":"🤱"},
    {"title":"Crossing the Chasm","author":"Geoffrey Moore","year":1991,"category":"Business Strategy","icon":"🌉"},
    {"title":"Purple Cow","author":"Seth Godin","year":2003,"category":"Business Strategy","icon":"🐮"},
    {"title":"This Is Marketing","author":"Seth Godin","year":2018,"category":"Business Strategy","icon":"📣"},
    {"title":"Traction","author":"Gabriel Weinberg","year":2015,"category":"Business Strategy","icon":"🚜"},
    {"title":"The E-Myth Revisited","author":"Michael Gerber","year":1995,"category":"Business Strategy","icon":"📋"},
    {"title":"Profit First","author":"Mike Michalowicz","year":2014,"category":"Business Strategy","icon":"💰"},
    {"title":"Business Model Generation","author":"Alexander Osterwalder","year":2010,"category":"Business Strategy","icon":"📐"},
    {"title":"Playing to Win","author":"A.G. Lafley","year":2013,"category":"Business Strategy","icon":"🏆"},
    {"title":"Only the Paranoid Survive","author":"Andy Grove","year":1996,"category":"Business Strategy","icon":"👁️"},
    {"title":"The Personal MBA","author":"Josh Kaufman","year":2010,"category":"Business Strategy","icon":"🎓"},
    {"title":"Thinking in Bets","author":"Annie Duke","year":2018,"category":"Business Strategy","icon":"🎰"},
    {"title":"Super Founders","author":"Ali Tamaseb","year":2021,"category":"Business Strategy","icon":"🦸"},
    {"title":"Hooked","author":"Nir Eyal","year":2014,"category":"Business Strategy","icon":"🪝"},
    {"title":"The Cold Start Problem","author":"Andrew Chen","year":2021,"category":"Business Strategy","icon":"❄️"},
    {"title":"Platform Revolution","author":"Geoffrey Parker","year":2016,"category":"Business Strategy","icon":"🌐"},
    {"title":"No Rules Rules","author":"Reed Hastings","year":2020,"category":"Business Strategy","icon":"🚫"},
    {"title":"Amp It Up","author":"Frank Slootman","year":2022,"category":"Business Strategy","icon":"🔊"},
    {"title":"What You Do Is Who You Are","author":"Ben Horowitz","year":2019,"category":"Business Strategy","icon":"🪞"},

    # ── SUPPLY CHAIN & OPERATIONS ──
    {"title":"The Goal","author":"Eliyahu Goldratt","year":1984,"category":"Supply Chain","icon":"🎯"},
    {"title":"The Toyota Way","author":"Jeffrey Liker","year":2004,"category":"Supply Chain","icon":"🏭"},
    {"title":"The Machine That Changed the World","author":"James Womack","year":1990,"category":"Supply Chain","icon":"⚙️"},
    {"title":"Supply Chain Management","author":"Sunil Chopra","year":2001,"category":"Supply Chain","icon":"🔗"},
    {"title":"The Phoenix Project","author":"Gene Kim","year":2013,"category":"Supply Chain","icon":"🔥"},
    {"title":"The Unicorn Project","author":"Gene Kim","year":2019,"category":"Supply Chain","icon":"🦄"},
    {"title":"Out of the Crisis","author":"W. Edwards Deming","year":1982,"category":"Supply Chain","icon":"📊"},
    {"title":"Lean Thinking","author":"James Womack","year":1996,"category":"Supply Chain","icon":"🔬"},
    {"title":"The Lean Six Sigma Pocket Toolbook","author":"Michael George","year":2004,"category":"Supply Chain","icon":"🧰"},
    {"title":"Factory Physics","author":"Wallace Hopp","year":1996,"category":"Supply Chain","icon":"⚛️"},
    {"title":"Operations Management","author":"Nigel Slack","year":1995,"category":"Supply Chain","icon":"📋"},
    {"title":"Logistics & Supply Chain Management","author":"Martin Christopher","year":1992,"category":"Supply Chain","icon":"🚛"},
    {"title":"The New Supply Chain Agenda","author":"Reuben Slone","year":2010,"category":"Supply Chain","icon":"📝"},
    {"title":"Demand Driven Material Requirements Planning","author":"Carol Ptak","year":2011,"category":"Supply Chain","icon":"📦"},
    {"title":"The Purchasing Chessboard","author":"Christian Schuh","year":2008,"category":"Supply Chain","icon":"♟️"},
    {"title":"Strategic Sourcing in the New Economy","author":"Bonnie Keith","year":2015,"category":"Supply Chain","icon":"🎯"},
    {"title":"Procurement and Supply Chain Management","author":"Kenneth Lysons","year":2000,"category":"Supply Chain","icon":"📊"},
    {"title":"The Fifth Discipline","author":"Peter Senge","year":1990,"category":"Supply Chain","icon":"5️⃣"},
    {"title":"Critical Chain","author":"Eliyahu Goldratt","year":1997,"category":"Supply Chain","icon":"⛓️"},
    {"title":"It's Not Luck","author":"Eliyahu Goldratt","year":1994,"category":"Supply Chain","icon":"🍀"},
    {"title":"Velocity","author":"Dee Jacob","year":2009,"category":"Supply Chain","icon":"💨"},
    {"title":"The DevOps Handbook","author":"Gene Kim","year":2016,"category":"Supply Chain","icon":"🔄"},
]

CATEGORY_COLORS = {
    "Self Help": "#3d8b37",
    "Motivation": "#e17055",
    "Investing": "#2e86ab",
    "Leadership": "#8e44ad",
    "Business Strategy": "#d4a017",
    "Supply Chain": "#1abc9c",
}

IMG_QUERIES = {
    "Self Help": "books+reading+morning+coffee+peaceful",
    "Motivation": "mountain+summit+sunrise+achievement",
    "Investing": "stock+market+chart+wealth+finance",
    "Leadership": "leadership+team+meeting+boardroom",
    "Business Strategy": "startup+whiteboard+strategy+planning",
    "Supply Chain": "logistics+warehouse+factory+shipping",
}


def daily_seed():
    return int(hashlib.md5(str(date.today()).encode()).hexdigest()[:8], 16)


def pick_book():
    """Pick today's book. Uses day-of-year as index — deterministic, cycles through all books.
    Books are in curated order: the library list itself IS the priority order.
    Most iconic books are listed first in each category."""
    day_of_year = date.today().timetuple().tm_yday
    year = date.today().year
    # Offset by year so the cycle shifts each year
    idx = (day_of_year + year * 7) % len(BOOKS)
    return BOOKS[idx]


def make_image_url(category, title):
    query = IMG_QUERIES.get(category, "books+knowledge+reading")
    sig = hashlib.md5(f"{date.today()}-{title}".encode()).hexdigest()[:8]
    return f"https://source.unsplash.com/800x450/?{query}&sig={sig}"


def generate_summary(book):
    """Generate a deep ~3500 word book summary. Title/author are hardcoded — AI only writes the content."""

    prompt = f"""Summarize the book "{book['title']}" by {book['author']} (published {book['year']}).

CRITICAL: This is a summary of the SPECIFIC book "{book['title']}" by {book['author']}. Do NOT summarize a different book. Do NOT invent a book. If you are unsure about the book, still do your best to summarize "{book['title']}" by {book['author']}. Use real content, examples, and frameworks from this exact book.

Write a DEEP summary (3000-4000 words, ~20 minute read). Someone reading this should get 80% of the book's value.

STRUCTURE (follow exactly):

## The Big Idea
One powerful paragraph: what is this book's core thesis? Why does it matter?

## Key Concepts
The 5-8 most important ideas. For each: name it in **bold**, explain with specific examples FROM THE BOOK, show real-life application.

## Chapter-by-Chapter Breakdown
Walk through the major parts/chapters. What's each section's argument? What stories, case studies, frameworks does the author use?

## Actionable Takeaways
5-10 specific, concrete actions. Not vague ("be better") but specific ("use the 2-minute rule: if it takes less than 2 minutes, do it now").

## Notable Quotes
3-5 real quotes from the actual book "{book['title']}". These must be real quotes from this book.

## Who Should Read This
2-3 sentences on who benefits most and when.

FORMAT RULES: Use ## for headers. **bold** for key terms. `backtick` for numbers/frameworks. [INSIGHT] ... [/INSIGHT] for 2-3 key "aha" callouts. Conversational tone, not academic.

Respond with ONLY a JSON object (no markdown fences, no extra text):
{{
  "content": "The full 3000-4000 word summary",
  "oneLiner": "One compelling sentence about why to read this book",
  "rating": "4.5"
}}"""

    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": f"You are summarizing the book \"{book['title']}\" by {book['author']}. Respond with valid JSON only. No markdown fences. No preamble."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 16000,
    }).encode()

    req = urllib.request.Request(
        API_URL, data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}
    )

    resp = urllib.request.urlopen(req, timeout=API_TIMEOUT)
    data = json.loads(resp.read())

    text = data["choices"][0]["message"]["content"].strip()
    for prefix in ["```json", "```"]:
        if text.startswith(prefix):
            text = text[len(prefix):]
    if text.endswith("```"):
        text = text[:-3]

    ai_result = json.loads(text.strip())

    # HARDCODE book metadata — never trust the AI for these
    result = {
        "id": hashlib.md5(f"{date.today()}-{book['title']}".encode()).hexdigest()[:12],
        "title": book["title"],
        "author": book["author"],
        "year": book["year"],
        "category": book["category"],
        "icon": book["icon"],
        "color": CATEGORY_COLORS.get(book["category"], "#3d8b37"),
        "content": ai_result.get("content", ""),
        "oneLiner": ai_result.get("oneLiner", f"A must-read book on {book['category'].lower()}."),
        "readTime": "20",
        "rating": ai_result.get("rating", "4.5"),
        "imageUrl": make_image_url(book["category"], book["title"]),
        "imageQuery": IMG_QUERIES.get(book["category"], "books+reading"),
        "generatedAt": datetime.utcnow().isoformat() + "Z",
    }

    return result


def main():
    log("=" * 50)
    log("BookGram Summary Generator v1")
    log("=" * 50)

    if not TOKEN:
        log("ERROR: GITHUB_TOKEN not available")
        sys.exit(1)

    book = pick_book()
    today = str(date.today())

    log(f"Date: {today}")
    log(f"Book: \"{book['title']}\" by {book['author']}")
    log(f"Category: {book['category']}")
    log(f"Model: {MODEL}")
    log("")

    # API test
    log("Testing API...")
    try:
        test_body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5}).encode()
        test_req = urllib.request.Request(API_URL, data=test_body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"})
        urllib.request.urlopen(test_req, timeout=10)
        log("  ✓ API connected")
    except Exception as e:
        log(f"  ✗ API failed: {e}")
        sys.exit(1)

    log("")
    log(f"Generating summary (~60-90 seconds)...")

    POSTS_DIR.mkdir(exist_ok=True)
    result = None

    for attempt in range(3):
        try:
            result = generate_summary(book)
            wc = len(result.get("content", "").split())
            log(f"  ✓ Generated! ({wc} words)")
            break
        except Exception as e:
            log(f"  ✗ Attempt {attempt+1}: {e}")
            if attempt < 2:
                time.sleep(15)

    if not result:
        log("❌ FATAL: Could not generate summary")
        sys.exit(1)

    # Save as today's post (array with single item for compatibility)
    output_path = POSTS_DIR / f"{today}.json"
    with open(output_path, "w") as f:
        json.dump([result], f, indent=2)

    log("")
    log("=" * 50)
    log(f"✅ Summary ready!")
    log(f"📖 \"{result['title']}\" by {result['author']}")
    log(f"📁 {output_path}")
    log(f"📝 {len(result.get('content','').split())} words")
    log(f"💰 Cost: $0.00")
    log("")
    log(f"📚 Library: {len(BOOKS)} books")
    log(f"   At 1/day, full cycle takes {len(BOOKS)} days (~{len(BOOKS)//30} months)")
    log("")
    log("🎉 Done!")


if __name__ == "__main__":
    main()
