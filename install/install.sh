#!/bin/bash

# Detect OS and architecture
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="MacOSX"
    if [[ $(uname -m) == "arm64" ]]; then
        ARCH="arm64"
    else
        ARCH="x86_64"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
    if [[ $(uname -m) == "aarch64" ]]; then
        ARCH="aarch64"
    else
        ARCH="x86_64"
    fi
else
    echo "Unsupported operating system"
    exit 1
fi

MINICONDA_URL="https://mirror.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py312_24.5.0-0-${OS}-${ARCH}.sh"
INSTALLER_PATH="/tmp/miniconda_installer.sh"

echo "Detected OS: $OS, Architecture: $ARCH"
echo "Downloading Miniconda from: $MINICONDA_URL"

# Download Miniconda
if command -v wget &> /dev/null; then
    wget -O "$INSTALLER_PATH" "$MINICONDA_URL"
elif command -v curl &> /dev/null; then
    curl -o "$INSTALLER_PATH" "$MINICONDA_URL"
else
    echo "Error: Neither wget nor curl is available. Please install one of them and try again."
    exit 1
fi

if [ $? -ne 0 ]; then
    echo "Failed to download Miniconda installer. Please check your internet connection and try again."
    exit 1
fi

echo "Installing Miniconda..."
bash "$INSTALLER_PATH" -b -p "./env"

if [ $? -ne 0 ]; then
    echo "Miniconda installation failed. Please check the error messages above."
    exit 1
fi

echo "Installing requirements..."
source ./env/bin/activate
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Failed to install requirements. Please check your requirements.txt file and try again."
    exit 1
fi

echo "Miniconda installation and setup complete."