"""Ca bổ sung trên dataset tạm, không thay đổi dữ liệu đề."""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from PIL import Image
from pipeline.common import Dataset, load_config
from pipeline.checks import label_format, second_opinion
from pipeline.steps import autofix

cfg = load_config()
with tempfile.TemporaryDirectory(prefix="autoqc_") as directory:
    root = Path(directory)
    (root / "images").mkdir()
    (root / "labels").mkdir()
    Image.new("RGB", (640, 480)).save(root / "images/a.JPG")
    ds = Dataset(root, cfg["classes"])
    path = ds.label_path("a")
    path.write_text("0 .95 .5 .2 .2\n\n0 .95 .5 .2 .2\ninf .5 .5 .2 .2\n", encoding="utf-8")
    issues = label_format.run(ds, cfg)
    assert {i.code for i in issues if i.line == 3} == {"DUP_BOX", "BOX_OUT_OF_IMAGE"}
    assert any(i.code == "BAD_FORMAT" and i.line == 4 for i in issues)
    fixes = autofix.fix(ds, issues, cfg)
    assert [(f["line"], f["action"]) for f in fixes] == [(1, "clip_box"), (3, "drop_line"), (4, "drop_line")]
    assert label_format.run(ds, cfg) == []
    assert autofix.fix(ds, label_format.run(ds, cfg), cfg) == []
    path.write_text("0 .5 .5 .2 .2\n\n1 .9 .9 .1 .1\n", encoding="utf-8")
    predictions = {"a": [[0, .9, .5, .5, .2, .2], [1, .9, .1, .1, .1, .1], [2, .9, .1, .8, .1, .1]]}
    flags = second_opinion.run(ds, cfg, predictions)
    assert [(i.code, i.line) for i in flags] == [("POSSIBLE_MISSING", None), ("POSSIBLE_MISSING", None), ("POSSIBLE_FALSE_POS", 3)]
result = {"passed": True, "cases": ["multi_error_drop_priority", "blank_line_numbers_and_nonfinite_class", "multiple_predictions_and_false_positive_line"], "assertions": 6}
(ROOT / "submission/evidence/edge_cases_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result))
