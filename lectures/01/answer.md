# 第1回 解答

## 演習

- 講座に固有の質問（宿題の3レベル）へのモデルの回答（要約でよい）：
*わからないときは？**
   * レベル1でつまずいた場合は、授業のアーカイブや教材に戻って復習しましょう。
   * レベル2や3で難しすぎる場合は、一人で抱え込まずに質問チャンネル等でメンターに相談することをお勧めします。

※もし、お手元の教材に「3レベル」についての具体的な定義（例：「レベル1：〇〇、レベル2：〇〇…」）が書かれているページがありましたら、その内容を教えていただければ、より正確にお答えできます！
- 用語集の正しい意味と比べて気づいたこと：要約されていた
- 表示できたトークン数（入力 / 出力）：入力トークン数は21、出力トークン数は406でした。

## 宿題

- 取り組んだレベル： / 実装 / 
- やったこと：連続質問
- 結果："""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 既定の質問から会話を始める

回答後に質問を入力すると、同じ会話履歴を使って続けて質問できる。
空の入力で終了する。ツールは使わない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai.chats import Chat
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def create_chat() -> Chat:
    client = genai.Client(api_key=get_api_key())
    return client.chats.create(model=MODEL)


def ask(question: str, chat: Chat | None = None) -> str:
    if chat is None:
        chat = create_chat()
    response = chat.send_message(question)

    usage = response.usage_metadata
    if usage is not None:
        print(
            f"[usage] input_tokens={usage.prompt_token_count} "
            f"output_tokens={usage.candidates_token_count}"
        )

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        chat = create_chat()
        question = args.question
        while True:
            print(f"[質問] {question}\n")
            print(ask(question, chat))
            try:
                question = input("\n次の質問（終了するには空行）: ")
            except EOFError:
                break
            if not question.strip():
                break
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()

- 気づき・疑問：
