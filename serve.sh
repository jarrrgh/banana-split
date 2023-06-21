#!/usr/bin/env bash

SCRIPT_DIR="$(dirname $0)"

CURA_VERSION=$1
echo "version now $CURA_VERSION"

# Default to 5.3
if [ -z "$CURA_VERSION" ]; then CURA_VERSION="5.3"; fi

echo "Use Cura version $CURA_VERSION"

PLUGINS_PATH="$HOME/Library/Application Support/cura/$CURA_VERSION/plugins/"
DEPLOY_PATH="$PLUGINS_PATH/BananaSplit"

echo "Deploy location: $DEPLOY_PATH"
mkdir -p "$DEPLOY_PATH"

echo
echo "Prepare BananaSplit"
zip -r "${SCRIPT_DIR}/BananaSplit.plugin" "${SCRIPT_DIR}/BananaSplit/" -x "*.DS_Store"

# echo
echo "Serve BananaSplit"
unzip -o "${SCRIPT_DIR}/BananaSplit.plugin" -d "$DEPLOY_PATH"

echo
echo "Restart Cura"

if [[ $CURA_VERSION == 5* ]]; then
    killall UltiMaker-Cura
    sleep 1

    # Open Cura for debug 5.xx
    /Applications/Ultimaker\ Cura.app/Contents/MacOS/UltiMaker-Cura --debug
    #open -b "nl.ultimaker.cura_UltiMaker_Cura_5.3.1"
else
    killall cura
    #osascript -e 'tell application "Ultimaker Cura" to quit'
    sleep 1

    # Open the test file after 10 seconds
    #sleep 10 && open -a Ultimaker\ Cura.app ${SCRIPT_DIR}/banana-split.3mf &

    # Open Cura for debug 4.xx
    #/Applications/Ultimaker\ Cura.app/Contents/MacOS/cura --debug
    ${HOME}/Tools/Ultimaker\ Cura\ ${CURA_VERSION}.app/Contents/MacOS/cura --debug
    #open -b "nl.ultimaker.cura"
fi
