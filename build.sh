#!/bin/bash
set -e

# Cleanup previous builds
rm -rf build dist *.spec

# Build with PyInstaller
# --onefile: Create a single executable
# --name: Name of the output binary
# --add-data: Include non-python files if needed (e.g., templates, config) - currently none critical for pure RAG?
#             Actually, we might need to verify if modules need data. 
#             But the code seems to rely on relative paths for 'target', which is fine.

eval "$(conda shell.bash hook)"
conda activate openui-env

echo "Building OpenUI Binary..."
pyinstaller --onedir \
            --name openui \
            --clean \
            --exclude-module=nvidia \
            --exclude-module=tensorboard \
            --exclude-module=triton \
            --hidden-import=sklearn.utils._cython_blas \
            --hidden-import=sklearn.neighbors.typedefs \
            --hidden-import=sklearn.neighbors.quad_tree \
            --hidden-import=sklearn.tree \
            --hidden-import=sklearn.tree._utils \
            openui_gen.py

echo "Build Complete. Executable is at dist/openui/openui"
