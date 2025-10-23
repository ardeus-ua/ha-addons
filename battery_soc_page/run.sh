#!/bin/sh

# Start Cloudflare Tunnel in background
cloudflared tunnel run --token "${tunnel_token}" &

# Start Flask server
python app.py