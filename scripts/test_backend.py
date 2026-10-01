import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.runtime'))
import pytest
if __name__=='__main__':raise SystemExit(pytest.main([str(ROOT/'backend/tests'),'-q']))
