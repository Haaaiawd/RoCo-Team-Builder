"""
pytest 顶层 conftest — 确保 src/ 可被测试代码以包路径导入。
"""

import sys
from pathlib import Path

_src_root = Path(__file__).resolve().parent.parent / "src"
if str(_src_root) not in sys.path:
    sys.path.insert(0, str(_src_root))
