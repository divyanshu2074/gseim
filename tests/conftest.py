import sys
from pathlib import Path

# Add project root and parent to sys.path
root_dir = Path(__file__).resolve().parent.parent
parent_dir = root_dir.parent

if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
