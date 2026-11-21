#!/usr/bin/env bash
# 第5回: まだログがない実行だけをまとめて行う（全文投入・Tree・Graph・宿題Q2の前後）。
# 使い方:  bash lectures/05/run_rest.sh     （止めたいときは Ctrl+C。Ctrl+Z は使わない）
# すでにログが正常に取れている実行は飛ばすので、途中で止まっても同じコマンドで再開できる。
set -u
cd "$(dirname "$0")/../.."
mkdir -p lectures/05/logs

Q1='第2回の説明では、LoRAは何を固定し何を学習しますか？ QLoRAは何を加えますか？'
Q2='第3回の例では、コンパクションとセッションをまたぐメモリはどう違いますか。日々のメモはすべて長期メモリに入りますか'

run() {  # run <ログ名> <AIE_RAG_NEIGHBORS> <質問> [モードの引数]
  local log="lectures/05/logs/$1.txt" n="$2" q="$3"; shift 3
  if grep -q '^\[usage\]' "$log" 2>/dev/null; then echo "済  $log"; return 0; fi
  for i in 1 2 3 4 5 6 7 8; do
    if AIE_RAG_NEIGHBORS="$n" uv run python -m app.agent "$@" --trace "$q" > "$log" 2>&1 \
       && grep -q '^\[usage\]' "$log"; then
      echo "OK  $log"; return 0
    fi
    echo "失敗（$i 回目）: $(tail -1 "$log")  → 60秒待って再実行"; sleep 60
  done
  echo "NG  $log（8回失敗。時間をおいて同じコマンドで再開してください）"
}

run step1_full    0 "$Q1" --full-context
run step4_tree    0 "$Q1" --tree
run step4_graph   0 "$Q1" --graph
run q2_before_n0  0 "$Q2"
run q2_after_n1   1 "$Q2"

echo
echo "=== 終わったら次を実行して push ==="
echo "git add lectures/05/logs/ && git commit -m '第5回 残りの実行ログ' && git push"
