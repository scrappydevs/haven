#!/bin/bash
# Development script - runs backend with Infisical secrets

echo "🚀 Starting backend with Infisical secrets..."

# Run with Infisical CLI (uses dev environment by default)
cd "$(dirname "$0")"
infisical run --env=dev -- python3 main.py

