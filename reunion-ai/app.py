"""ReunionAI - picks the fairest city for a scattered friend group to meet in,
then asks Claude to write the itinerary and the invitation message.

Works without an API key too (falls back to a simple template plan), so you can
test the whole flow before adding your key.
"""
import math
import os

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# City -> (latitude, longitude). Add more cities here any time.
CITIES = {
    "New York, NY": (40.7128, -74.0060),
    "Boston, MA": (42.3601, -71.0589),
    "Washington, DC": (38.9072, -77.0369),
    "Atlanta, GA": (33.7490, -84.3880),
    "Miami, FL": (25.7617, -80.1918),
    "Orlando, FL": (28.5383, -81.3792),
    "Nashville, TN": (36.1627, -86.7816),
    "Charlotte, NC": (35.2271, -80.8431),
    "Chicago, IL": (41.8781, -87.6298),
    "Detroit, MI": (42.3314, -83.0458),
    "Minneapolis, MN": (44.9778, -93.2650),
    "St. Louis, MO": (38.6270, -90.1994),
    "Kansas City, MO": (39.0997, -94.5786),
    "Dallas, TX": (32.7767, -96.7970),
    "Houston, TX": (29.7604, -95.3698),
    "Austin, TX": (30.2672, -97.7431),
    "New Orleans, LA": (29.9511, -90.0715),
    "Denver, CO": (39.7392, -104.9903),
    "Salt Lake City, UT": (40.7608, -111.8910),
    "Phoenix, AZ": (33.4484, -112.0740),
    "Las Vegas, NV": (36.1699, -115.1398),
    "Los Angeles, CA": (34.0522, -118.2437),
    "San Diego, CA": (32.7157, -117.1611),
    "San Francisco, CA": (37.7749, -122.4194),
    "Portland, OR": (45.5152, -122.6784),
    "Seattle, WA": (47.6062, -122.3321),
    "Philadelphia, PA": (39.9526, -75.1652),
    "Pittsburgh, PA": (40.4406, -79.9959),
    "Columbus, OH": (39.9612, -82.9988),
    "Indianapolis, IN": (39.7684, -86.1581),
}


def miles(a, b):
    """Great-circle distance between two (lat, lon) points in miles."""
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def rank_cities(friends, top=3):
    """Score every candidate city. Lower is better.

    Score = total miles everyone travels + half the longest single trip, so the
    pick is efficient overall but doesn't make one person cross the country.
    """
    results = []
    for city, coords in CITIES.items():
        trips = [
            {"name": f["name"], "from": f["city"], "miles": round(miles(CITIES[f["city"]], coords))}
            for f in friends
        ]
        total = sum(t["miles"] for t in trips)
        longest = max(t["miles"] for t in trips)
        results.append(
            {
                "city": city,
                "total_miles": total,
                "longest_trip": longest,
                "average_miles": round(total / len(trips)),
                "score": total + 0.5 * longest,
                "trips": trips,
            }
        )
    results.sort(key=lambda r: r["score"])
    return results[:top]


def fallback_plan(best, friends, dates, vibe):
    names = ", ".join(f["name"] for f in friends)
    return (
        f"INVITATION\n"
        f"Hey {names}! Reunion time. I checked where everyone is flying from and "
        f"{best['city']} is the fairest meeting spot. Dates: {dates or 'TBD'}. "
        f"Vibe: {vibe or 'relaxed'}. Reply with a yes and I'll lock in the plan.\n\n"
        f"ITINERARY\n"
        f"Day 1: Arrive, check in, group dinner.\n"
        f"Day 2: Explore the city together, long catch-up lunch, evening games.\n"
        f"Day 3: Brunch, group photo, goodbyes.\n\n"
        f"(Add ANTHROPIC_API_KEY to get a full AI-written plan.)"
    )


def ask_claude(best, friends, dates, vibe, budget):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    import anthropic  # imported here so the app still runs without the package/key

    trips = "; ".join(f"{t['name']} from {t['from']} (~{t['miles']} mi)" for t in best["trips"])
    prompt = (
        "You are helping organize a reunion of close college friends who live in "
        "different cities across the US.\n"
        f"Chosen city: {best['city']}\n"
        f"Travel: {trips}\n"
        f"Dates: {dates or 'not decided'}\n"
        f"Vibe: {vibe or 'relaxed and fun'}\n"
        f"Budget per person: {budget or 'moderate'}\n\n"
        "Write two sections, using exactly these headings in capitals:\n"
        "INVITATION - a warm, short group message (under 90 words) the organizer can send today.\n"
        "ITINERARY - a day-by-day plan with 2-3 specific ideas per day, suited to the vibe and "
        "budget, with one low-key option for people who arrive tired.\n"
        "Plain text only, no markdown symbols."
    )
    client = anthropic.Anthropic(api_key=key)
    msg = client.messages.create(
        model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5"),
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


@app.get("/")
def index():
    return render_template("index.html", cities=sorted(CITIES))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/plan")
def plan():
    data = request.get_json(silent=True) or {}
    friends = [
        {"name": str(f.get("name", "")).strip()[:40], "city": str(f.get("city", "")).strip()}
        for f in data.get("friends", [])
    ]
    friends = [f for f in friends if f["name"] and f["city"]]
    if len(friends) < 2:
        return jsonify(error="Add at least two friends with a name and a city."), 400
    unknown = [f["city"] for f in friends if f["city"] not in CITIES]
    if unknown:
        return jsonify(error=f"Pick cities from the list: {', '.join(unknown)}"), 400

    dates = str(data.get("dates", ""))[:80]
    vibe = str(data.get("vibe", ""))[:120]
    budget = str(data.get("budget", ""))[:40]

    ranked = rank_cities(friends)
    best = ranked[0]
    try:
        text = ask_claude(best, friends, dates, vibe, budget)
    except Exception as exc:  # network/key problems shouldn't break the app
        app.logger.warning("Claude call failed: %s", exc)
        text = None
    ai = text is not None
    return jsonify(ranked=ranked, plan=text or fallback_plan(best, friends, dates, vibe), ai=ai)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
