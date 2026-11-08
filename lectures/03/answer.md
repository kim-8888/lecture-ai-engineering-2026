# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
  - 第1回の `app.ask` は用語集を見ずに答えるので、講座固有の言葉は一般論や推測で答えていた。
  - 第3回のエージェントは、まず `search_glossary` で用語集を検索し、その定義に沿って答え、回答の最後に関係する回（第N回）を示した。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
  - 「LoRAとQLoRAの違いは？」で `search_glossary({'query': 'LoRA'})` が1回呼ばれた（`lectures/03/trace_before.txt`）。
  - 用語を2つ聞いたのに検索は1回だった。`search_glossary` は部分一致も拾うため、`'LoRA'` だけで「LoRA」「ランク（LoRAのr）」「QLoRA」の3件が返り、モデルはそれで足りると判断したと考えられる。
- 1つの質問での LLM 呼び出し回数（`requests`）：
  - `requests=2`、`tool_calls=1`。1回目でモデルがツール呼び出しを返し、ツールの結果を渡した2回目で回答を作っている（エージェントループ）。
- 追加したツールと、docstring に書いた説明：
  - `make_quiz(lecture: int) -> str`。用語集から指定した回の用語を1つ `random.choice` で選び、`{"question": "「○○」の意味は？", "answer": 定義}` を JSON 文字列で返す。用語が無い回（第0回など）は「問題を出せる回: [1, 2, 3, 5]」と案内し、エラーにしない。
  - docstring：「指定した回の用語から確認問題を1問作り、問題と答えを返す。『第2回の確認問題を出して』のように、確認問題・クイズ・復習問題を求められたときに使う。」
  - `app/agent.py` の TODO の場所で `agent.tool_plain(tools.make_quiz)` と登録した。

## 宿題

- 取り組んだレベル：基礎、実装

### 基礎

- やったこと：
  - `app/tools.py` の `search_glossary` の docstring を1か所だけ変えた。
    - 変更前：「query には調べたい用語を1つだけ入れる（例: "LoRA"）」
    - 変更後：「query には質問に出てくる用語をまとめて1回で入れる（例: "LoRA QLoRA"）」
  - 同じ質問「LoRAとQLoRAの違いは？」を `--trace` 付きで実行し、`lectures/03/compare_basic.sh` で変更前後を比べた（比べたあと docstring は元に戻した）。結果は `trace_before.txt` / `trace_after.txt`。
- 結果：

  | | 変更前（1つだけ） | 変更後（まとめて） |
  |---|---|---|
  | ツール呼び出し | `search_glossary({'query': 'LoRA'})` | `search_glossary({'query': 'LoRA QLoRA'})` |
  | 返った用語 | LoRA, ランク（LoRAのr）, QLoRA | LoRA, QLoRA |
  | requests / tool_calls | 2 / 1 | 2 / 1 |
  | 入力 / 出力トークン | 1591 / 185 | 1543 / 204 |

  - 回答の違い：変更前は「16ビットなどの高精度で固定」など、用語集に無い説明が混ざっていた。変更後は「用語集によると」で始まり、PEFT であることやファイルサイズの削減など、用語集の定義に近い内容になった。
- 気づき・疑問：
  - docstring の書き換えで、モデルが渡す引数（`'LoRA'` → `'LoRA QLoRA'`）ははっきり変わった。docstring はコメントではなく、モデルへの「使い方の指示」として効いている。
  - 一方、検索回数は変わらなかった。「1つだけ」でも部分一致で QLoRA が一緒に返るため、もともと1回で済んでいた。ツールの実装（検索の仕方）次第で、docstring の指示の効き方も変わる。
  - 変更後は関係の薄い「ランク（LoRAのr）」が返らず、入力トークンが少し減った。ただ、用語が多い質問では `MAX_RESULTS=3` で切られて取りこぼしが起きないかが気になった。

### 実装

- やったこと：
  - `app/tools.py` に `save_learning_log(title, content)` を追加。`learning_log/日時_題名.md` に Markdown で保存する（`learning_log/` は `.gitignore` 済み）。ファイル名に使えない文字は `_` に置き換え、別フォルダに書かないようにした。
  - `app/agent.py` で `agent.tool_plain(tools.save_learning_log, requires_approval=True)` と登録し、`output_type=[str, DeferredToolRequests]` にした。
  - CLI に `resolve_approvals()` を追加。`result.output` が `DeferredToolRequests` の間、`approvals` の1件ずつに題名と本文を表示して `y/N` を聞き、許可なら `True`、拒否なら `ToolDenied("利用者が保存を許可しませんでした。")` を `DeferredToolResults` に入れ、`message_history=result.all_messages()` と一緒に `run_sync` をやり直す。
  - `tests/test_learning_log.py` に TestModel を使ったテストを6つ書いた（保存の中身、ファイル名の安全化、空入力、承認前は保存されない、承認すると保存される、拒否すると保存されない）。保存先は `tmp_path` に差し替え、本物の `learning_log/` には書かない。
- 結果：
  - `uv run pytest -q` で、既存のテストも含めて全て通った。
  - `uv run python -m app.agent --trace "LoRAとQLoRAの違いを調べて、学習の記録に保存して"` で `[approval] save_learning_log を実行しようとしています` と題名・本文が表示され、`y` で `learning_log/` に保存された。
- 気づき・疑問：
  - 承認待ちのツールは実行されずに一度 run が終わり、承認結果を渡してもう一度 run する、という2段階になっている。
  - 取り消しにくい操作（書き込み）だけ承認を挟み、検索のような読むだけのツールには挟まない、と分けるのが使いやすい。
