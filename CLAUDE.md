# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run the app
streamlit run app.py
```

## Architecture

Single-file Streamlit app (`app.py`) with tool logic split into `tools/` modules.

```
app.py                  # Entry point: sidebar nav, tool dispatch, error handling
utils/gemini_client.py  # Gemini API wrapper (generate / generate_stream)
tools/
  blog_writer.py        # ブログ記事執筆
  email_replier.py      # メール返信文生成
  summarizer.py         # 文章要約
  proofreader.py        # 文章校正・改善
  title_generator.py    # タイトル・見出し生成
  sns_writer.py         # SNS投稿文生成
  translator.py         # 翻訳
```

**Adding a new tool:**
1. `tools/<name>.py` を作成し `render()` を実装する
2. `app.py` の import に追加する
3. `app.py` の `TOOLS` に `"表示名": ("key", module.render)` を追加する
4. `app.py` の `ICONS` に絵文字を追加する

## Tool module pattern

Every tool file follows this structure:

1. **Config dicts** — map user-facing labels to prompt strings (e.g. `TONE_MAP`, `LENGTH_MAP`)
2. **`_build_prompt()`** — assembles the full prompt string from UI inputs
3. **`render()`** — Streamlit UI; calls `generate_stream(prompt)` and pipes it to `st.write_stream()`; stores result in `st.session_state` for the download button

## Design decisions

- **認証・DBなし** — 個人用ツールとして意図的に省略している。追加しないこと
- **ツール間で状態を共有しない** — `st.session_state` のキーは各ツール固有のものを使う（例: `"blog_result"`, `"email_result"`）。共通キーを作るとツール切り替え時に競合する
- **`generate_stream()` を優先** — ユーザー向けの出力は常にストリーミングにする。`generate()` はストリーミングが使えない内部処理（バッチ処理など）に限定する
- **モデルは `gemini-2.5-flash` に固定** — コストと速度のバランスで選定。変更する場合は `utils/gemini_client.py` の `MODEL_NAME` のみ編集する

## Gemini client

`utils/gemini_client.py` uses the `google-genai` SDK (not the deprecated `google-generativeai`). Model is `gemini-2.5-flash`, configurable via `MODEL_NAME`. Always use `generate_stream()` for user-facing output (streaming UX); use `generate()` only for non-interactive calls.

## Do not

- `google-generativeai` パッケージを使わない — 非推奨。必ず `google-genai` を使う
- ツールモジュールに Streamlit 以外の状態管理（グローバル変数など）を持ち込まない — Streamlitはスクリプトを毎回再実行するため無意味になる
- `render()` を複数のファイルから呼び出さない — 各ツールの `render()` は `app.py` からのみ呼ばれる前提で設計されている

## API key

Set `GEMINI_API_KEY` in a `.env` file (loaded via `python-dotenv`). The sidebar also exposes a password input that writes to `os.environ` at runtime as a fallback.
