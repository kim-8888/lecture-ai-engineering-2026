"""第5回 宿題（実装）: 検索の段階だけをコードで採点する（第4回「RAGは検索と生成を分けて測る」）。

質問ごとに「根拠になるページ」を正解として用意し、検索結果に正解のページが何件入ったか（recall）を、
前後ページ付与なし（0）とあり（1）で比べる。回答の生成（LLM）は呼ばず、質問の埋め込みだけAPIを使う。

使い方:  uv run python lectures/05/check_recall.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # リポジトリ直下の app を読み込む
from app.retrieval import add_neighbor_pages, search  # noqa: E402

CASES = [
    {"name": "Q1 LoRA（1ページで足りる）",
     "query": "第2回の説明では、LoRAは何を固定し何を学習しますか？ QLoRAは何を加えますか？",
     "gold": {"lec02-main-p052"}},
    {"name": "Q1' 検索だけ（STEP 2 の検索語）",
     "query": "LoRA QLoRA 違い",
     "gold": {"lec02-main-p052"}},
    {"name": "Q2 コンパクションとメモリ（複数ページ）",
     "query": "第3回の例では、コンパクションとセッションをまたぐメモリはどう違いますか。日々のメモはすべて長期メモリに入りますか",
     "gold": {"lec03-main-p013", "lec03-main-p039", "lec03-main-p040"}},
]


def main() -> None:
    print("| 質問 | 前後ページ | 返したページ数 | 正解の取得 | recall | 取得できなかった正解 |")
    print("|---|---|---|---|---|---|")
    for case in CASES:
        hits = search(case["query"])  # 埋め込みは1回だけ。0と1で同じ検索結果を使う
        for window in (0, 1):
            results = add_neighbor_pages(hits, window)
            got = {r["page_id"] for r in results} & case["gold"]
            missing = ", ".join(sorted(case["gold"] - got)) or "なし"
            print(f"| {case['name']} | {window} | {len(results)} | {len(got)}/{len(case['gold'])} "
                  f"| {len(got) / len(case['gold']):.2f} | {missing} |")
        print(f"<!-- {case['name']} の検索上位: "
              + ", ".join(f"{h['page_id']}({h['distance']:.3f})" for h in hits) + " -->")


if __name__ == "__main__":
    main()
