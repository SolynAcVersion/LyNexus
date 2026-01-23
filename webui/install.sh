#!/bin/bash

# LyNexus WebUI Installation Script for Linux/macOS
# This script handles the installation with proper mirror configuration

set -e

echo "============================================"
echo "LyNexus WebUI - Installation Script"
echo "============================================"
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "ERROR: npm is not installed"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

echo "[1/4] Using China mirror for faster downloads..."
echo "Registry: https://registry.npmmirror.com"
echo ""

# Set npm configuration
npm config set registry https://registry.npmmirror.com
npm config set electron_mirror https://npmmirror.com/mirrors/electron/
npm config set electron_builder_binaries_mirror https://npmmirror.com/mirrors/electron-builder-binaries/

echo "[2/4] Cleaning previous installation..."
rm -rf node_modules package-lock.json dist dist-electron release
echo "Done."
echo ""

echo "[3/4] Installing dependencies..."
echo "This may take a few minutes, please wait..."
echo ""
npm install
echo ""
echo "[4/4] Installation completed successfully!"
echo ""

echo "============================================"
echo "Next Steps:"
echo "============================================"
echo ""
echo "To start development:"
echo "  npm run dev              (Web only)"
echo "  npm run electron:dev     (Electron app)"
echo ""
echo "To build for production:"
echo "  npm run build            (Build web)"
echo "  npm run electron:build   (Build Electron app)"
echo ""
echo "============================================"
