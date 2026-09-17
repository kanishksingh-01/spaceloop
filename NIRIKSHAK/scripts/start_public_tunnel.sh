#!/bin/bash
# ==============================================================================
# NIRIKSHAK & PRAHARAK — Public Tunnel Launcher
# Exposes localhost:3001 to a live, secure, publicly accessible HTTPS URL.
# ==============================================================================

echo "Starting Cloudflare Public Tunnel for NIRIKSHAK & PRAHARAK..."
/opt/homebrew/bin/cloudflared tunnel --url http://localhost:3001
