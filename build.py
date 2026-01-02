import os
import sys
import shutil
import subprocess
import platform

def clean_build():
    """Removes previous build artifacts."""
    dirs_to_clean = ["build", "dist"]
    files_to_clean = ["openui.spec"]
    
    print("Cleaning build directories...")
    for d in dirs_to_clean:
        if os.path.exists(d):
            shutil.rmtree(d)
    
    for f in files_to_clean:
        if os.path.exists(f):
            os.remove(f)

def build():
    """Run PyInstaller with platform-specific configurations."""
    
    # Detect OS
    current_os = platform.system()
    print(f"Detected Platform: {current_os}")
    
    # Common PyInstaller arguments
    # Using --onedir to avoid size limits (4GB+ uncompressed)
    # Use sys.executable to ensure we use the PyInstaller from the current env
    args = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--name", "openui",
        "--clean",
        "--noconfirm", # Do not ask for confirmation to overwrite
        
        # Exclude massive unused libraries to prevent OOM and reduce size
        "--exclude-module=nvidia",
        "--exclude-module=tensorboard",
        "--exclude-module=triton",
        # Custom: Keep torch.distributed/testing as they are needed for runtime imports
        # "--exclude-module=torch.distributed", 
        # "--exclude-module=torch.testing",
        "--exclude-module=torch.tests", # We found torch.testing is needed, tests might not be
        
        # Handle hidden imports for Scikit-Learn (used heavily in RAG)
        "--hidden-import=sklearn.utils._cython_blas",
        "--hidden-import=sklearn.neighbors.typedefs",
        "--hidden-import=sklearn.neighbors.quad_tree",
        "--hidden-import=sklearn.tree",
        "--hidden-import=sklearn.tree._utils",
        
        # Entry point
        "openui_gen.py"
    ]
    
    # Platform-specific adjustments (if any future needs arise)
    if current_os == "Windows":
        # Windows might need specific icon or separator handling, 
        # but PyInstaller handles mostly everything.
        pass
    
    print(f"Running command: {' '.join(args)}")
    
    try:
        subprocess.run(args, check=True)
        print("\n------------------------------------------------")
        print("Build Complete!")
        
        # executable path
        ext = ".exe" if current_os == "Windows" else ""
        dist_path = os.path.join("dist", "openui", f"openui{ext}")
        
        if os.path.exists(dist_path):
            print(f"Executable located at: {os.path.abspath(dist_path)}")
        else:
            print("Warning: Executable not found in expected location.")
            
    except subprocess.CalledProcessError as e:
        print(f"Build Failed with error code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    clean_build()
    build()
