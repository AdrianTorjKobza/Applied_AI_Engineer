import sys
import os
import uvicorn

# 1. Calculate the absolute path of the directory containing this script (the project root)
project_root = os.path.dirname(os.path.abspath(__file__))

# 2. Forcefully inject the project root into Python's module search path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 3. Now that the path is guaranteed, we can safely import from the 'src' package
from src.main import app

if __name__ == "__main__":
    print(f"Bootstrapping API from root: {project_root}")
    # Run the application directly
    uvicorn.run(app, host="0.0.0.0", port=8000)