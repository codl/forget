import sys
from pathlib import Path

PROJDIR = str(Path(__file__).parent.parent)
if PROJDIR not in sys.path:
    print(PROJDIR)
    sys.path.append(PROJDIR)

