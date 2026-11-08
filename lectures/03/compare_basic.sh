#!/usr/bin/env bash
# 第3回 宿題（基礎）: search_glossary の docstring を1か所だけ変えて、--trace の結果を比べる。
#
# 変更点: 「query には調べたい用語を1つだけ入れる（例: "LoRA"）」
#      →「query には質問に出てくる用語をまとめて1回で入れる（例: "LoRA QLoRA"）」
#
# 使い方（リポジトリの直下で）:
#   bash lectures/03/compare_basic.sh
# 結果は lectures/03/trace_before.txt と lectures/03/trace_after.txt に保存される。
# 最後に docstring は元に戻す（変更したままにはしない）。
set -euo pipefail

QUESTION="${1:-LoRAとQLoRAの違いは？}"
OUT=lectures/03
BEFORE='query には調べたい用語を1つだけ入れる（例: "LoRA"）。'
AFTER='query には質問に出てくる用語をまとめて1回で入れる（例: "LoRA QLoRA"）。'

grep -qF "$BEFORE" app/tools.py || { echo "app/tools.py に元の文が見つかりません。すでに書き換えていないか確認してください。"; exit 1; }

restore() { uv run python - "$AFTER" "$BEFORE" <<'PY'
import sys, pathlib
p = pathlib.Path("app/tools.py")
p.write_text(p.read_text(encoding="utf-8").replace(sys.argv[1], sys.argv[2]), encoding="utf-8")
PY
}
trap restore EXIT

echo "=== 変更前 ==="
uv run python -m app.agent --trace "$QUESTION" | tee "$OUT/trace_before.txt"

uv run python - "$BEFORE" "$AFTER" <<'PY'
import sys, pathlib
p = pathlib.Path("app/tools.py")
p.write_text(p.read_text(encoding="utf-8").replace(sys.argv[1], sys.argv[2]), encoding="utf-8")
PY

echo
echo "=== 変更後（docstring を「まとめて入れる」に変更）==="
uv run python -m app.agent --list-tools | grep -A3 '\[search_glossary\]'
uv run python -m app.agent --trace "$QUESTION" | tee "$OUT/trace_after.txt"

echo
echo "=== 比較（tool call と usage の行だけ）==="
for f in before after; do
  echo "--- $f ---"
  grep -E '^\[tool call\]|^\[usage\]' "$OUT/trace_$f.txt"
done
echo
echo "docstring は元に戻しました。上の比較を lectures/03/answer.md の「宿題」欄に書き写してください。"
