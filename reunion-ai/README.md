# ReunionAI

Finds the fairest city for a scattered friend group to meet in, then uses Claude
to write the invitation and a day-by-day itinerary.

## Run locally

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then paste your key into .env (optional)
export ANTHROPIC_API_KEY=your-key # Windows PowerShell: $env:ANTHROPIC_API_KEY="your-key"
python app.py
```

Open http://localhost:5000. Without an API key the app still works and shows a
starter plan.

## Deploy on Render (free)

1. Push this folder to a new GitHub repo.
2. On render.com: New > Web Service > connect the repo.
3. Runtime: Python 3. Build command: `pip install -r requirements.txt`.
4. Start command: `gunicorn app:app`.
5. Environment > add `ANTHROPIC_API_KEY`.
6. Deploy. Your live URL appears at the top of the page.

Never commit your API key. `.env` is already in `.gitignore`.
