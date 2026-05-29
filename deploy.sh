#!/bin/bash
set -e
echo "==> Pulling latest..."
git pull origin main
echo "==> Building and restarting..."
docker-compose down
docker-compose up -d --build
echo "==> Done! Swim Trainer running on :8020"
docker-compose ps
