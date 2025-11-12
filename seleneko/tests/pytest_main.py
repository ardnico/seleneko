import pytest
import sys
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    sys.exit(pytest.main(["-v", "tests"]))
