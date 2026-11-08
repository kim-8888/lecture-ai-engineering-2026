# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
  - 第1回の `app.ask` は用語集を見ずに答えるので、講座固有の言葉（「lecNN-start タグ」など）は一般論や推測になっていた（← 自分の第1回の結果に合わせて1行で）。
  - 第3回のエージェントは、まず `search_glossary` で用語集を検索し、その定義に沿って答えた。回答の最後に関係する回（第N回）も示された。
- `--trace` で見えたツール呼び出し（ツール名と引数）：
  - 「LoRAとQLoRAの違いは？」で `search_glossary({'query': 'LoRA'})` と `search_glossary({'query': 'QLoRA'})`（← 実際の出力に合わせて）。docstring の「1つだけ入れる」に従い、用語を1つずつ検索していた。
- 1つの質問での LLM 呼び出し回数（`requests`）：
  - `requests=○`（← `[usage]` の数字）。ツールを呼ぶ → 結果を見て次を決める、を繰り返すので、1つの質問でも LLM を複数回呼ぶ。
- 追加したツールと、docstring に書いた説明：
  - `make_quiz(lecture: int) -> str`。用語集から指定した回の用語を1つ `random.choice` で選び、`{"question": "「○○」の意味は？", "answer": 定義}` を JSON 文字列で返す。用語が無い回（第0回など）は「問題を出せる回: [1, 2, 3, 5]」と案内する。
  - docstring：「指定した回の用語から確認問題を1問作り、問題と答えを返す。『第2回の確認問題を出して』のように、確認問題・クイズ・復習問題を求められたときに使う。」
  - `--trace "第2回の内容から確認問題を1問出して"` で `[tool call] make_quiz({'lecture': 2})` が出た（← 確認して書く）。

## 宿題

- 取り組んだレベル：基礎、実装

### 基礎

- やったこと：
  - `app/tools.py` の `search_glossary` の docstring を1か所だけ変えた。
    - 変更前：「query には調べたい用語を1つだけ入れる（例: "LoRA"）」
    - 変更後：「query には質問に出てくる用語をまとめて1回で入れる（例: "LoRA QLoRA"）」
  - 同じ質問「LoRAとQLoRAの違いは？」を `--trace` 付きで実行し、`lectures/03/compare_basic.sh` で変更前後の `[tool call]` と `[usage]` を比べた（比べたあと docstring は元に戻した）。
- 結果：（← `trace_before.txt` / `trace_after.txt` を見て書き換える）
  - 変更前：`search_glossary` が ○回、引数は `'LoRA'`, `'QLoRA'`、`requests=○`
  - 変更後：`search_glossary` が ○回、引数は `'○○'`、`requests=○`
  - 回答の違い：
- 気づき・疑問：
  - docstring はコードのコメントではなく、モデルへの「使い方の指示」として効いている。
  - まとめて検索すると LLM の呼び出し回数は減りうるが、検索は部分一致なので、用語が増えると取りこぼし（`MAX_RESULTS=3` で切られる）が起きないか気になった。

### 実装

- やったこと：
  - `app/tools.py` に `save_learning_log(title, content)` を追加。`learning_log/日時_題名.md` に Markdown で保存する（`learning_log/` は `.gitignore` 済み）。
  - `app/agent.py` で `agent.tool_plain(tools.save_learning_log, requires_approval=True)` と登録し、`output_type=[str, DeferredToolRequests]` にした。
  - CLI に `resolve_approvals()` を追加。`result.output` が `DeferredToolRequests` の間、`approvals` の1件ずつに題名と本文を表示して `y/N` を聞き、許可なら `True`、拒否なら `ToolDenied(...)` を `DeferredToolResults` に入れて、`message_history=result.all_messages()` と一緒に `run_sync` をやり直す。
  - `tests/test_learning_log.py` に TestModel を使ったテストを6つ書いた（保存の中身、ファイル名の安全化、空入力、承認前は保存されない、承認すると保存される、拒否すると保存されない）。保存先は `tmp_path` に差し替え。
- 結果：
  - `uv run pytest -q` が全て成功（← 件数を書く）。
  - `uv run python -m app.agent --trace "LoRAとQLoRAの違いを調べて、学習の記録に保存して"` で `[approval] save_learning_log` と確認が出て、`y` で `learning_log/` に保存された／`n` で保存されなかった（← 確認して書く）。
- 気づき・疑問：
  - 承認待ちのツールは実行されずに一度 run が終わり、承認結果を渡してもう一度 run する、という2段階になっている。
  - 取り消しにくい操作（書き込み）だけ承認を挟み、検索のような読むだけのツールは挟まない、と分けるのが使いやすい。
