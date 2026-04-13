# SwarmDash

Local Swarm & Bee dashboard for Ollama-hosted models.

## Run

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/bootstrap.py
uvicorn app.main:app --host 0.0.0.0 --port 8008
# swarm-dash
