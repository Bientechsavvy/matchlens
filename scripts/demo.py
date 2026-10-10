"""Generate a match and print overlays + recap. Usage: python scripts/demo.py [seed]"""
import json
import sys

sys.path.insert(0, "src")
from matchlens.orchestration.pipeline import Pipeline  # noqa: E402
from matchlens.schemas.events import ViewerProfile  # noqa: E402
from matchlens.simulator.generator import MatchSimulator  # noqa: E402

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
m = MatchSimulator(seed).generate()
p = Pipeline()
a = p.analyse(m)
print(f"{m.home_name} {m.score['home']}-{m.score['away']} {m.away_name}  ({len(m.events)} events)\n")
for lang, mode in (("en", "analyst"), ("es", "casual")):
    prof = ViewerProfile(mode=mode, lang=lang)
    print(f"--- {mode}/{lang} ---")
    for o in p.overlays(a, prof)[:6]:
        print(json.dumps(o.model_dump(), ensure_ascii=False))
    print(p.recap(a, prof), "\n")
