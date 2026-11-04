ReunionAI
Finds the fairest city for a scattered friend group to meet in, then uses Claude to write the invitation and a day-by-day itinerary.

Run locally
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then paste your key into .env (optional)
export ANTHROPIC_API_KEY=your-key # Windows PowerShell: $env:ANTHROPIC_API_KEY="your-key"
python app.py
