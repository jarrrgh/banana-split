#!/usr/bin/env bash

PLUGINS_PATH="$HOME/Library/Application Support/cura/4.12/plugins/"
DEPLOY_PATH="$PLUGINS_PATH/BananaSplit"

echo "Deploy location: $DEPLOY_PATH"
mkdir -p "$DEPLOY_PATH"

echo
echo "Prepare BananaSplit"
zip -r BananaSplit.plugin BananaSplit/ -x "*.DS_Store"

# echo
echo "Serve BananaSplit"
unzip -o BananaSplit.plugin -d "$DEPLOY_PATH"

echo
echo "Restart Cura"
killall cura
#osascript -e 'tell application "Ultimaker Cura" to quit'
sleep 1
open -b "nl.ultimaker.cura"
