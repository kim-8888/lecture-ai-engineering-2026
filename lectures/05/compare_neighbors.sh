#!/usr/bin/env bash
# 第5回 宿題（実装）: 前後ページ付与の「変更前（0）」と「変更後（1）」を、同じ質問・同じモデルで比べる。
# 使い方:  bash lectures/05/compare_neighbors.sh
# 結果は lectures/05/logs/ に保存する（APIキーは含まれない）。
set -u
cd "$(dirname "$0")/../.."
mkdir -p lectures/05/logs

Q1='第2回の説明では、LoRAは何を固定し何を学習しますか？ QLoRAは何を加えますか？'
Q2='第3回の例では、コンパクションとセッションをまたぐメモリはどう違いますか。日々のメモはすべて長期メモリに入りますか'

# 503（混雑）・429（レート制限）で落ちたら60秒待って最大5回やり直す
run() {  # run <ログ名> <AIE_RAG_NEIGHBORS> <質問>
  local log="lectures/05/logs/$1.txt"
  for i in 1 2 3 4 5; do
    if AIE_RAG_NEIGHBORS="$2" uv run python -m app.agent --trace "$3" > "$log" 2>&1; then
      echo "OK  $log"; return 0
    fi
    echo "失敗（$i 回目）: $(tail -1 "$log")  → 60秒待って再実行"; sleep 60
  done
  echo "NG  $log（5回失敗。ログを確認してください）"
}

# 検索だけ（APIは埋め込みのみ）：返るページの違いを見る
AIE_RAG_NEIGHBORS=0 uv run python -m app.retrieval "LoRA QLoRA 違い" > lectures/05/logs/retrieval_n0.txt 2>&1
AIE_RAG_NEIGHBORS=1 uv run python -m app.retrieval "LoRA QLoRA 違い" > lectures/05/logs/retrieval_n1.txt 2>&1

# 検索の段階だけをコードで採点（正解ページの recall、表をそのまま answer.md に貼れる）
uv run python lectures/05/check_recall.py > lectures/05/logs/recall.md 2>&1

run q1_before_n0 0 "$Q1"
run q1_after_n1  1 "$Q1"
run q2_before_n0 0 "$Q2"
run q2_after_n1  1 "$Q2"

echo
echo "=== 要約（answer.md の表に写す） ==="
for f in lectures/05/logs/q*_*.txt; do
  echo "--- $(basename "$f")"
  grep -E '^\[(model|tool call|time|usage|cost)\]' "$f"
done
echo
echo "=== 検索の採点（recall） ==="
cat lectures/05/logs/recall.md
echo
echo "=== 検索だけの結果（ページ番号） ==="
for f in lectures/05/logs/retrieval_n*.txt; do
  echo "--- $(basename "$f")"
  grep -E '^(検索結果 |講義: |ページ: )' "$f" | paste - - -
done
