#!/usr/bin/env bash

# Apparently relative paths mess up zip files, so run this in the project root.

echo
echo "Compressing..."
rm -f BananaSplit.zip
zip -r BananaSplit.zip BananaSplit -x "*.DS_Store"
echo "Done"
