#!/bin/bash
cd "/Volumes/JARVIS HUB3/hub3-jarvis"
git add .
git commit -m "Auto-push: $(date '+%d/%m/%Y %H:%M') - Hub3 v4.2"
git push origin main
