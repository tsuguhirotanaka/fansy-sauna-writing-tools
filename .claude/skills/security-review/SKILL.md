---
name: security-review
description: >
  Streamlit + LLM API アプリのセキュリティ診断を実行するスキル。
  「セキュリティチェック」「脆弱性チェック」「セキュリティレビュー」「security check」「security review」「脆弱性を調べて」などと言われたら必ずこのスキルを使うこと。
  コード全体を静的解析し、APIキー漏洩・SSRF・プロンプトインジェクション・XSS・依存パッケージの脆弱性を診断してMarkdownレポートを出力する。
  Streamlit・LLM API（Gemini / OpenAI / Anthropic 等）・外部URL取得を使うアプリなら何でも対象になる。
---

# Streamlit + LLM API セキュリティ診断スキル

## 事前調査

診断を始める前に、以下でプロジェクト構造とスタックを把握する。

```bash
# ファイル構造の把握
find . -name "*.py" | grep -v __pycache__ | sort
cat requirements.txt 2>/dev/null || cat pyproject.toml 2>/dev/null

# LLM API の種類を特定（Gemini / OpenAI / Anthropic / 他）
grep -rn "openai\|anthropic\|google.genai\|google-generativeai\|cohere\|mistral" --include="*.py" . | head -20

# 外部通信の特定
grep -rn "requests\.\|httpx\.\|aiohttp\.\|urllib" --include="*.py" . | grep -v "^Binary\|#\|import "
```

---

## 診断チェックリスト

### 1. APIキー管理

**何を調べるか：** APIキーがコードや設定ファイルに直接書かれていないか、Gitに乗っていないかを確認する。

```bash
# .gitignore に .env が含まれるか
cat .gitignore 2>/dev/null | grep -E "\.env|secret|credential|key"

# .env がコミット済みか（あれば Critical）
git ls-files .env .env.local .env.production 2>/dev/null

# コード内のハードコード疑惑
grep -rn "sk-\|AIza\|api_key\s*=\s*['\"]" --include="*.py" . | grep -v "os.getenv\|os.environ\|placeholder\|#"

# 環境変数の読み取り方が安全か
grep -rn "os.environ\|os.getenv\|load_dotenv" --include="*.py" .

# Streamlit サイドバーでのAPIキー入力 → os.environ への書き込み箇所
grep -rn "os.environ\[" --include="*.py" .
```

**リスク判定：**
- APIキーのハードコード、または `.env` がコミット済み → **Critical**
- `.gitignore` に `.env` なし → **High**
- Streamlit の `st.text_input(type="password")` でAPIキーを受け取り `os.environ` に書き込む → **Low**（個人用では許容範囲だが、セッション間でキーが共有される点に注意）

---

### 2. SSRF（Server-Side Request Forgery）

**何を調べるか：** ユーザーが入力したURLをサーバーサイドでフェッチする箇所でSSRFが可能かを確認する。

```bash
# 外部フェッチの箇所を全て列挙
grep -rn "requests.get\|requests.post\|httpx.get\|urllib.request" --include="*.py" . 

# URLをユーザー入力から受け取る箇所
grep -rn "st.text_input\|url\s*=" --include="*.py" . | grep -i url | head -20

# URLバリデーション・フィルタリングの有無
grep -rn "urlparse\|startswith.*http\|localhost\|127\.0\|private\|internal" --include="*.py" .
```

**確認ポイント：**
- `requests.get(user_url)` のような直接フェッチがあるか
- スキームを `http://` / `https://` のみに制限しているか
- プライベートIPレンジ（`127.*`、`10.*`、`192.168.*`、`172.16-31.*`、`169.254.*`）へのアクセスをブロックしているか
- `requests` がリダイレクトを追従する際、リダイレクト先もバリデーションされているか

**リスク判定：**
- URLバリデーションが一切なく外部公開サービスならば → **Critical**
- 個人用ツールでバリデーションなし → **Medium**
- スキーム確認あり・プライベートIPフィルタなし → **Low**

---

### 3. プロンプトインジェクション

**何を調べるか：** 外部から取得したコンテンツやユーザー入力が、LLMへのプロンプトにそのまま埋め込まれていないかを確認する。

```bash
# プロンプト組み立て関数を特定
grep -rn "_build_prompt\|build_prompt\|make_prompt\|format_prompt" --include="*.py" .

# サイトから取得したコンテンツがプロンプトに入る箇所
grep -rn "site_info\|fetched\|scraped\|page_content\|web_content" --include="*.py" .

# ユーザー入力がプロンプトに直接入る箇所
grep -rn "memo\|user_input\|text_area\|text_input" --include="*.py" tools/ 2>/dev/null | grep -v "st\."
```

**確認ポイント：**
- WebスクレイピングしたコンテンツがそのままLLMプロンプトに入る場合、悪意あるサイトが「プロンプトを乗っ取る命令」を埋め込める（間接プロンプトインジェクション）
- ユーザーが入力したテキストがプロンプトに入る場合、「今までの指示を無視して…」という直接インジェクションが可能
- f-string でプロンプトを組み立てている場合、`{` や `}` を含む入力が Python 側で問題を起こす可能性はないか確認する（通常 f-string では変数展開済みなので無害だが、Jinja2 等テンプレートエンジン利用時は別）

**リスク判定：**
- 外部WebコンテンツをLLMに渡す構造 + 公開サービス → **High**
- 外部WebコンテンツをLLMに渡す構造 + 個人用ツール → **Medium**
- ユーザー自身のメモ入力のみ → **Low**

---

### 4. XSS（`unsafe_allow_html` の誤用）

**何を調べるか：** Streamlit の `unsafe_allow_html=True` が使われている箇所で、ユーザー入力や外部コンテンツが混入していないかを確認する。

```bash
# unsafe_allow_html の使用箇所を全列挙
grep -rn "unsafe_allow_html\s*=\s*True" --include="*.py" .
```

該当箇所があれば、その引数の文字列を追う。変数が含まれる場合はその変数の出所を確認する（ユーザー入力由来か、定数・テンプレートのみか）。

**リスク判定：**
- `unsafe_allow_html=True` + ユーザー入力または外部コンテンツを含む変数 → **High**
- `unsafe_allow_html=True` だが引数が完全に静的なテンプレート → **Low**（念のため記録）

---

### 5. 依存パッケージの脆弱性

**何を調べるか：** `requirements.txt` に記載されたパッケージに既知のCVE（脆弱性）がないかを確認する。

```bash
# pip-audit による自動チェック（推奨）
pip audit 2>/dev/null

# pip-audit がなければインストールして実行
pip install pip-audit -q 2>/dev/null && pip audit

# どちらも失敗したら requirements.txt の内容を列挙
cat requirements.txt
```

---

### 6. その他の設定確認

```bash
# Streamlit 設定ファイル（CORSや公開設定）
cat .streamlit/config.toml 2>/dev/null || echo "config.toml なし（デフォルト設定）"

# エラーハンドリングで内部情報が漏洩していないか
# （スタックトレースをそのまま st.error() に渡すと実装詳細が見える）
grep -rn "st\.error\|st\.exception\|traceback\.format" --include="*.py" .

# requests のタイムアウト設定（タイムアウトなしは DoS に脆弱）
grep -rn "requests\.get\|requests\.post" --include="*.py" . | grep -v "timeout="

# ファイルアップロード機能がある場合：ファイルタイプ検証の有無
grep -rn "file_uploader\|uploaded_file" --include="*.py" . | head -10
```

---

## レポート出力フォーマット

全チェック完了後、以下のフォーマットでMarkdownレポートを出力する。

```markdown
# セキュリティ診断レポート — [アプリ名]
診断日時: YYYY-MM-DD  
対象スタック: [例: Streamlit + Gemini API + requests]

## サマリー

| リスクレベル | 件数 |
|---|---|
| 🔴 Critical | N |
| 🟠 High | N |
| 🟡 Medium | N |
| 🟢 Low | N |

## 詳細所見

### 🟠 [High] 所見タイトル

- **ファイル**: `path/to/file.py:行番号`
- **内容**: 何が問題か（コードの該当箇所を引用）
- **リスク**: どんな攻撃が可能か、実際の影響範囲（このアプリの用途・公開範囲を考慮）
- **推奨対応**: 具体的な修正方法。可能であれば修正前後のコード例を示す

---

（所見ごとに繰り返す）

## 許容・対応不要事項

意図的な設計（認証なし、DB なしなど）や、用途・公開範囲を考慮して許容できるリスクをここに記載する。  
ただし「個人用なので問題ない」で済ませず、将来の公開可能性や想定リスクを簡潔に述べること。

## 結論と優先対応

全体評価と、対応するなら何から着手すべきかを箇条書きで示す。
```

---

## 注意事項

- **静的解析のみ**を行う。実際にSSRFを試みるなど動的テストは行わない
- リスク評価は**アプリの公開範囲**（個人用・社内用・公開サービス）を考慮して行うこと。個人用ツールと公開サービスでは同じ脆弱性でもリスクレベルが異なる
- CLAUDE.md や README に「個人用ツール」「認証なし」などの設計方針が明記されている場合は、その前提でリスクを評価する
