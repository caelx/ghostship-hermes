from __future__ import annotations

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
contract_src = root / 'ghostship-cli-contract' / 'src'
sys.path.insert(0, str(contract_src))
