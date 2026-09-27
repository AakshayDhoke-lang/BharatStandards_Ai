from pathlib import Path
import json
p=Path(__file__).resolve().parents[1]/'training/gold_test_set.json'
tests=json.loads(p.read_text());assert len(tests)>=10;print('PASS',len(tests),'gold cases defined')
