# 単独実行サポート（python -m seleneko.tests.pytest_main）
import sys
import pytest

def main():
    sys.exit(pytest.main(["-q"]))

if __name__ == "__main__":
    main()
