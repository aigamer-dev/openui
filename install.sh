#!/bin/bash
set -e

echo "========================================"
echo "   OpenUI Auto-Generator Installer"
echo "========================================"

# 1. Check for Conda
if ! command -v conda &> /dev/null; then
    echo "Error: Conda is not installed or not in PATH."
    exit 1
fi

ENV_NAME="openui-env"

# 2. Create/Update Environment
echo "[1/3] Setting up Conda Environment '$ENV_NAME'..."
if conda info --envs | grep -q "$ENV_NAME"; then
    echo "Environment exists. Updating..."
    eval "$(conda shell.bash hook)"
    conda activate $ENV_NAME
else
    echo "Creating new environment..."
    conda create -n $ENV_NAME python=3.10 -y
    eval "$(conda shell.bash hook)"
    conda activate $ENV_NAME
fi

# 3. Install Dependencies
echo "[2/3] Installing Dependencies via Poetry..."
if ! command -v poetry &> /dev/null; then
    pip install poetry
fi
poetry install

# 4. Verify Installation
echo "[3/3] Verifying 'openui' CLI..."
if poetry run openui --help > /dev/null; then
    echo "Success! The 'openui' command is ready."
    echo ""
    echo "Usage:"
    echo "  1. Activate Env: conda activate $ENV_NAME"
    echo "  2. Run Tool:     poetry run openui --target <path> --rag"
    echo ""
    echo "Example:"
    echo "  poetry run openui --target ../external-react-cart --rag"
else
    echo "Error: CLI installation failed."
    exit 1
fi
