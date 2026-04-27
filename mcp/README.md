# aip-mcp

Google [AIP](https://google.aip.dev) (API Improvement Proposals) コーパス全体を、LLM クライアントから直接参照できる **MCP (Model Context Protocol) サーバー** を Docker イメージとして提供します。

このリポジトリの全 AIP（general / cloud / auth / firebase / apps / aog / client-libraries の 7 スコープ・**117 本**）をイメージに同梱し、Markdown のままリソースとして、またメタフィルタや BM25 全文検索のツールとして公開します。

> **AIP コンテンツは Creative Commons Attribution 4.0、コードサンプルは Apache 2.0（リポジトリルートの `LICENSE.md` 参照）。本 MCP サーバーのコードは Apache 2.0 です。**

---

## 提供する Resources / Tools

### Resources（読み取り専用データ）

| URI | 中身 | MIME |
| --- | --- | --- |
| `aip://index` | 全 AIP のメタデータ JSON 配列 | `application/json` |
| `aip://scopes` | スコープ定義とカテゴリ一覧 | `application/json` |
| `aip://{scope}/{id}` | 指定 AIP の生 Markdown（フロントマター込） | `text/markdown` |

### Tools（呼び出し可能な関数）

| Tool | 引数 | 用途 |
| --- | --- | --- |
| `list_aips` | `scope?`, `category?`, `state?` | メタデータでフィルタした一覧（本文なし） |
| `get_aip` | `aip_id`, `scope?` | 単体取得（本文込み）。`scope` 省略時は一意なら自動解決 |
| `search_aips` | `query`, `scope?`, `top_k=10` | BM25 全文検索 |
| `get_related_aips` | `aip_id`, `scope?` | 当該 AIP の outgoing / incoming 参照 |
| `reload_corpus` | – | コーパスを再読み込み |

---

## クイックスタート

公開済みイメージ **[`tsubasatommy/aip-mcp`](https://hub.docker.com/r/tsubasatommy/aip-mcp)** を使えば、リポジトリの clone もビルドも不要です。ホストに Docker さえあれば動きます（multi-arch: `linux/amd64` / `linux/arm64`）。

### 1. イメージを取得（任意・初回起動時に自動 pull されます）

```bash
docker pull tsubasatommy/aip-mcp
```

### 2. 動作確認（任意）

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' | docker run --rm -i tsubasatommy/aip-mcp
```

`serverInfo.name = "aip"` を含む JSON が返れば成功。

### 3. Claude Desktop に登録

設定ファイルの場所:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "aip": {
      "command": "docker",
      "args": ["run", "--rm", "-i", "tsubasatommy/aip-mcp"]
    }
  }
}
```

Claude Desktop を再起動。ハンマー / プラグアイコンに `aip` が出れば成功です。

### 4. Claude Code に登録

```bash
claude mcp add aip -- docker run --rm -i tsubasatommy/aip-mcp
```

`/mcp` で `aip` が `connected` であることを確認します。

### バージョンを固定したい場合

`tsubasatommy/aip-mcp:latest` ではなく明示タグ（例: `tsubasatommy/aip-mcp:0.1.0`）を指定してください。

---

## 使い方の例

LLM への自然言語指示と、内部で呼ばれる Tool の対応例。

| プロンプト例 | 内部で呼ばれるもの |
| --- | --- |
| 「AIP-131 の要点を要約して」 | `aip://general/131` リソース or `get_aip(131)` |
| 「pagination について書かれた AIP を全部探して」 | `search_aips("pagination")` |
| 「AIP-160 が参照している AIP を一覧で」 | `get_related_aips(160)` |
| 「auth スコープに含まれる AIP のタイトル一覧」 | `list_aips(scope="auth")` |

---

## イメージを最新に保つ

公開イメージは上流の AIP 更新に追随して再 push されます。最新を引き直すには:

```bash
docker pull tsubasatommy/aip-mcp:latest
```

クライアント（Claude Desktop / Claude Code）はコンテナ起動時に最新層を使うので、`docker pull` 後に再起動すれば反映されます。

## 自分でビルドする（フォークを改造する場合）

このリポジトリを clone して `mcp/` や `aip/` を改造したい場合のみ、ローカルビルドが必要です。

```bash
git clone https://github.com/TsubasaTommy/google.aip.dev.git
cd google.aip.dev
docker build -f mcp/Dockerfile -t aip-mcp:dev .
```

ローカルビルドしたイメージを使うときは Claude Desktop の `args` を `["run", "--rm", "-i", "aip-mcp:dev"]` に差し替えてください。

---

## トラブルシューティング

| 症状 | 対処 |
| --- | --- |
| `docker: command not found` | Docker Desktop / Engine をインストール |
| `Cannot connect to the Docker daemon` | Docker を起動。macOS なら Docker Desktop アプリを開く |
| Claude Desktop に表示されない | `~/Library/Logs/Claude/mcp*.log` を確認。多くは `args` の typo |
| AIP が古いまま | `docker pull tsubasatommy/aip-mcp:latest` で取り直し、クライアントを再起動 |

---

## 開発者向け

### Python ローカルでテストを回したい

```bash
cd mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

ローダー / BM25 検索 / 参照グラフを 12 ケースで検証します。

### MCP Inspector で対話確認

```bash
cd mcp
source .venv/bin/activate
mcp dev src/aip_mcp/server.py
```

ブラウザで Inspector が開きます。

- **Resources** タブで `aip://index` → 117 件の JSON 配列
- **Tools** タブで `search_aips({"query": "standard get method"})` → AIP-131 が上位
- **Tools** タブで `get_related_aips({"aip_id": 131, "scope": "general"})` → outgoing に AIP-121

### その他

- AIP の一意キーは `(scope, id)` のタプル。番号空間が衝突する可能性があるため、`get_aip` / `get_related_aips` は scope 指定推奨
- 新スコープを追加するには `aip/{scope}/scope.yaml` を置けば自動認識（`mcp/` 側の変更不要）
- 環境変数 `AIP_REPO` でコーパスのルートを差し替え可能（Dockerfile では `/app` に固定）

---

## ライセンス

- MCP サーバーのコード（このディレクトリ配下）: **Apache 2.0**
- 配信される AIP コンテンツ: 上流 [`LICENSE.md`](../LICENSE.md) に従う（CC-BY 4.0 + Apache 2.0）
