"""第5回 宿題（実装）: 検索結果に前後ページを付ける処理のテスト（APIキー不要）。"""

from app.retrieval import add_neighbor_pages, load_pages


def _hit(page_id: str, distance: float = 0.1) -> dict:
    page = next(p for p in load_pages() if p["page_id"] == page_id)
    return {**page, "distance": distance}


def test_window0_keeps_hits_only():
    hits = [_hit("lec02-main-p052")]
    results = add_neighbor_pages(hits, window=0)
    assert [r["page_id"] for r in results] == ["lec02-main-p052"]
    assert "retrieved_by" not in results[0]  # 変更前と同じ形


def test_adds_previous_and_next_page_of_same_document():
    results = add_neighbor_pages([_hit("lec02-main-p052")], window=1)
    assert [r["page_id"] for r in results] == ["lec02-main-p052", "lec02-main-p051", "lec02-main-p053"]
    assert results[0]["retrieved_by"] == "vector"
    assert results[1]["retrieved_by"] == "neighbor"
    assert results[1]["neighbor_of"] == "lec02-main-p052"
    assert "distance" not in results[1]
    # 引用情報（講義・ページ番号）も一緒に返す
    assert results[1]["lecture"] == 2 and results[1]["page"] == 51


def test_no_duplicates_when_hits_are_adjacent():
    hits = [_hit("lec02-main-p052", 0.1), _hit("lec02-main-p053", 0.2)]
    ids = [r["page_id"] for r in add_neighbor_pages(hits, window=1)]
    assert ids == ["lec02-main-p052", "lec02-main-p051", "lec02-main-p053", "lec02-main-p054"]
    assert len(ids) == len(set(ids))


def test_does_not_cross_document_boundary():
    results = add_neighbor_pages([_hit("lec02-main-p001")], window=1)
    assert [r["page_id"] for r in results] == ["lec02-main-p001", "lec02-main-p002"]
    assert all(r["document_id"] == "lec02-main" for r in results)
