#!/bin/bash
## setup command=wget -q --no-check-certificate https://raw.githubusercontent.com/Belfagor2005/AdvancedScreenshot/main/installer.sh -O - | /bin/sh

version='1.2'
changelog='\nSet Config - locale add'
TMPPATH=/tmp/AdvancedScreenshot-main
FILEPATH=/tmp/main.tar.gz

if [ ! -d /usr/lib64 ]; then
    PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/AdvancedScreenshot
else
    PLUGINPATH=/usr/lib64/enigma2/python/Plugins/Extensions/AdvancedScreenshot
fi

# Detect OS type
if [ -f /var/lib/dpkg/status ]; then
    STATUS=/var/lib/dpkg/status
    OSTYPE=DreamOs
else
    STATUS=/var/lib/opkg/status
    OSTYPE=Dream
fi
echo ""

# Install wget if missing
if ! command -v wget >/dev/null 2>&1; then
    echo "Installing wget..."
    if [ "$OSTYPE" = "DreamOs" ]; then
        apt-get update && apt-get install -y wget
    else
        opkg update && opkg install wget
    fi || { echo "Failed to install wget"; exit 1; }
fi

# Detect Python version
if python --version 2>&1 | grep -q '^Python 3\.'; then
    echo "You have Python3 image"
    PYTHON=PY3
    Packagerequests=python3-requests
else
    echo "You have Python2 image"
    PYTHON=PY2
    Packagerequests=python-requests
fi
echo ""

# Install required requests package
if ! grep -qs "Package: $Packagerequests" "$STATUS"; then
    echo "Installing $Packagerequests..."
    if [ "$OSTYPE" = "DreamOs" ]; then
        apt-get update && apt-get install -y "$Packagerequests"
    else
        opkg update && opkg --force-reinstall --force-overwrite install "$Packagerequests"
    fi || { echo "Failed to install $Packagerequests"; exit 1; }
fi

# Extra multimedia packages (only for non-DreamOs)
if [ "$OSTYPE" != "DreamOs" ]; then
    opkg update && opkg --force-reinstall --force-overwrite install ffmpeg gstplayer exteplayer3 enigma2-plugin-systemplugins-serviceapp python3-youtube-dl
fi
sleep 2

# Download and extract plugin
mkdir -p "$TMPPATH"
cd "$TMPPATH" || exit 1
wget --no-check-certificate 'https://github.com/Belfagor2005/AdvancedScreenshot/archive/refs/heads/main.tar.gz' -O "$FILEPATH" || { echo "Download failed"; exit 1; }
tar -xzf "$FILEPATH" -C /tmp/ || { echo "Extraction failed"; exit 1; }
cp -r /tmp/AdvancedScreenshot-main/usr/ / || { echo "Copy failed"; exit 1; }
set +e
cd
sleep 2

# Verify installation
if [ ! -d "$PLUGINPATH" ]; then
    echo "Installation failed: plugin directory missing"
    rm -rf "$TMPPATH" "$FILEPATH"
    exit 1
fi

# Cleanup
rm -rf "$TMPPATH" "$FILEPATH"
sync

# Show debug info
FILE="/etc/image-version"
box_type=$(head -n 1 /etc/hostname 2>/dev/null || echo "Unknown")
distro_value=$(grep '^distro=' "$FILE" 2>/dev/null | awk -F '=' '{print $2}')
distro_version=$(grep '^version=' "$FILE" 2>/dev/null | awk -F '=' '{print $2}')
python_vers=$(python --version 2>&1)

echo "#########################################################
#          	    INSTALLED SUCCESSFULLY                  #
#                developed by LULULLA                   #
#               https://corvoboys.org                   #
#########################################################
#           your Device will RESTART Now                #
#########################################################
^^^^^^^^^^Debug information:
BOX MODEL: $box_type
OO SYSTEM: $OSTYPE
PYTHON: $python_vers
IMAGE NAME: ${distro_value:-Unknown}
IMAGE VERSION: ${distro_version:-Unknown}
"

sleep 5
killall -9 enigma2
exit 0
