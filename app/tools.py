"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
import random
import re
from datetime import datetime
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
# 第3回 宿題（実装）: 学習の記録の保存先。.gitignore 済みなので fork には上がらない
LOG_DIR = Path(__file__).resolve().parent.parent / "learning_log"
MAX_RESULTS = 3


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "").replace("　", "")


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
    """
    q = _normalize(query)
    if not q:
        return "検索語が空です。調べたい用語を1つ指定してください。"
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # 「r」のような短い別名が何にでも当たらないよう、名前側が短いものは除く
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"用語集に「{query}」は見つかりませんでした。"
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """指定した回（1始まりの整数）の講義の要点を返す。

    「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")


def make_quiz(lecture: int) -> str:
    """指定した回（1始まりの整数）の用語から確認問題を1問作り、問題と答えを返す。

    「第2回の確認問題を出して」「第3回の復習クイズを1問」のように、
    確認問題・クイズ・復習問題を求められたときに使う。
    lecture には問題を出したい回の番号を入れる（例: 2）。
    返り値は {"question": ..., "answer": ...} の JSON 文字列。
    """
    glossary = load_glossary()
    candidates = [e for e in glossary if e["lecture"] == lecture]
    if not candidates:
        available = sorted({e["lecture"] for e in glossary})
        return f"第{lecture}回の用語は用語集にありません。問題を出せる回: {available}"
    entry = random.choice(candidates)
    return json.dumps(
        {"question": f"「{entry['term']}」の意味は？", "answer": entry["definition"]},
        ensure_ascii=False,
    )


def save_learning_log(title: str, content: str) -> str:
    """学習の記録を learning_log/ フォルダに Markdown ファイルとして保存する。

    利用者が「今日の学習を記録して」「この内容をメモに残して」のように、
    学んだことの保存をはっきり頼んだときだけ使う。頼まれていないのに使わない。
    title には記録の短い題名（例: "LoRAとQLoRAの違い"）、
    content には保存する本文（学んだ要点を箇条書きなどで）を入れる。
    ファイルを書き込む操作なので、実行前に利用者の確認が入る。
    """
    title = title.strip()
    if not title or not content.strip():
        return "title と content の両方を指定してください。"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    # ファイル名に使えない文字は _ に置き換える（日本語はそのまま使う）
    safe_title = re.sub(r'[\\/:*?"<>|\s]+', "_", title)[:40].strip("_") or "log"
    path = LOG_DIR / f"{now:%Y%m%d-%H%M%S}_{safe_title}.md"
    path.write_text(
        f"# {title}\n\n- 保存日時: {now:%Y-%m-%d %H:%M}\n\n{content.strip()}\n",
        encoding="utf-8",
    )
    return f"保存しました: {path.relative_to(LOG_DIR.parent)}"
