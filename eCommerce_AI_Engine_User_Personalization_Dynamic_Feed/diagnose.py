import os
import sys

def run_diagnostics():
    print("========================================")
    print(" ENVIRONMENT DIAGNOSTIC REPORT ")
    print("========================================\n")
    
    # 1. Check Python executable context
    print("1. PYTHON EXECUTABLE:")
    print(f"   {sys.executable}\n")
    
    # 2. Check the absolute working directory
    current_dir = os.path.abspath(os.getcwd())
    print("2. CURRENT WORKING DIRECTORY:")
    print(f"   {current_dir}\n")
    
    # 3. List actual contents of the directory
    print("3. DIRECTORY CONTENTS (What Python actually sees here):")
    try:
        items = os.listdir(current_dir)
        dirs = [d for d in items if os.path.isdir(os.path.join(current_dir, d))]
        files = [f for f in items if os.path.isfile(os.path.join(current_dir, f))]
        
        for d in dirs:
            print(f"   [DIR]  {d}/")
        for f in files:
            print(f"   [FILE] {f}")
    except Exception as e:
        print(f"   Error reading directory: {e}")
    print()
    
    # 4. Check for the specific 'src' package
    print("4. 'src' PACKAGE CHECK:")
    src_path = os.path.join(current_dir, 'src')
    if os.path.exists(src_path):
        print(f"   [SUCCESS] 'src' directory found at: {src_path}")
        init_path = os.path.join(src_path, '__init__.py')
        if os.path.exists(init_path):
            print("   [SUCCESS] '__init__.py' found inside 'src'. It is a valid package.")
        else:
            print("   [WARNING] 'src' exists, but '__init__.py' is MISSING. Python will not recognize it as a package.")
    else:
        print("   [FATAL] The 'src' directory DOES NOT EXIST in the current working directory.")
    print("\n========================================")

if __name__ == "__main__":
    run_diagnostics()