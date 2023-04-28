#!/usr/bin/env bash

PLUGINS_PATH="$HOME/Library/Application Support/cura/4.12/plugins/"
#PLUGINS_PATH="$HOME/Library/Application Support/cura/5.3/plugins/"
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
#killall UltiMaker-Cura
#osascript -e 'tell application "Ultimaker Cura" to quit'
sleep 1

# Open the test file after 10 seconds
sleep 10 && open -a Ultimaker\ Cura.app banana-split.3mf &

# Open Cura for debug 4.xx
/Applications/Ultimaker\ Cura.app/Contents/MacOS/cura --debug
#open -b "nl.ultimaker.cura"

# Open Cura for debug 5.xx
#/Applications/Ultimaker\ Cura.app/Contents/MacOS/UltiMaker-Cura --debug
#open -b "nl.ultimaker.cura_UltiMaker_Cura_5.3.1"

