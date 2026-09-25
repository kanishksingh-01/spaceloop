#!/bin/bash
set -e
RESTORE_DIR=".restore_points/SL-PRE-SYS-COLOR-2026-V1"
if [ ! -d "$RESTORE_DIR" ]; then
  echo "Error: Restore point $RESTORE_DIR does not exist."
  exit 1
fi

echo "Rolling back to $RESTORE_DIR..."
cp -r $RESTORE_DIR/src/* frontend/src/
cp $RESTORE_DIR/tailwind.config.js frontend/
cp $RESTORE_DIR/index.html frontend/
cp -r $RESTORE_DIR/templates/* templates/
cp -r $RESTORE_DIR/static/* static/
cp $RESTORE_DIR/app.py app.py
rm -rf public/*
cp -r $RESTORE_DIR/public/* public/

echo "Rebuilding frontend..."
cd frontend && npm run build && cd ..
rm -rf public/*
cp -r frontend/dist/* public/

echo "Rollback successful: SpaceLoop restored to exact pre-theme state."
