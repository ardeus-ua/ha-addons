#!/bin/sh

# Start Cloudflare Tunnel in background
cloudflared tunnel run --url http://localhost:5000 ${tunnel_id} &

# Start Flask server
python app.py
