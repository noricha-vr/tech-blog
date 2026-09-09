# Scripts

- `validate_site.py`: ビルドしたHTML/CSSの静的リソース参照から、旧kaisha3.comホストの混入を検出する。
- `test_validate_site.py`: `uv run python -m unittest discover -s scripts -p 'test_*.py'` で回帰検証する。

`build.sh` は日英ビルド後にvalidatorを実行する。通常の記事リンク・コード例・検索インデックスは許可する。動的JavaScript通信や外部配信設定は検査対象外で、この検査だけでは外部HTTP 500の解消を証明できない。
