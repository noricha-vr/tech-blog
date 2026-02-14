# Tech Blog

AI エージェント開発の知見を公開する技術ブログ。Material for MkDocs + Cloudflare Pages。

## Quick Reference

| 項目 | 値 |
|------|---|
| URL (本番) | https://blog.kojin.works |
| URL (英語) | https://blog.kojin.works/en/ |
| フレームワーク | Material for MkDocs 9.x |
| ホスティング | Cloudflare Pages |
| リポジトリ | noricha-vr/tech-blog |

## 技術スタック

- Material for MkDocs 9.x (blog plugin, tags plugin)
- 2-config ビルド方式 (mkdocs.yml + mkdocs.en.yml)
- Cloudflare Pages (Git 連携デプロイ)

## ディレクトリ構成

| ディレクトリ | 役割 |
|-------------|------|
| `docs/` | 日本語コンテンツ |
| `docs-en/` | 英語コンテンツ（翻訳） |
| `overrides/` | テーマカスタマイズ |
| `site/` | ビルド出力（Git 管理外） |

## コマンド

```bash
# ローカルサーバー（日本語）
uv run mkdocs serve

# ローカルサーバー（英語）
uv run mkdocs serve -f mkdocs.en.yml

# 両言語ビルド
bash build.sh
```

## 記事作成

- `/blog-publish` スキルで記事を作成・翻訳・PR 作成
- 記事ファイル名: `YYYY-MM-DD-slug.md`
- frontmatter: date, authors, tags, categories 必須

## i18n 方式

blog プラグインと mkdocs-static-i18n は非互換のため、2-config ビルド方式を採用。
`mkdocs.en.yml` は `INHERIT: mkdocs.yml` で共通設定を継承し、docs_dir と site_dir を上書き。
