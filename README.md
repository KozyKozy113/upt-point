# プロダクト要件
- 特定のHPのサイトから必要な情報を定期的に取得し、データを蓄積
    - 実行頻度はパラメータで指定可能
- プログラムはPythonを利用

# 対象サイト
https://up-t.jp/collabo/atjam2025

# 取得する情報
- "broad_rank"クラス内の"text_slide"クラスに表示されているテキスト（文字列の配列形式）
- "rank-table"クラス内の"even"クラスの<tr>属性の内容（オブジェクトの配列形式）
    - name属性："name-rank"クラス内のテキスト
    - point属性："box-text"クラス内のテキストから、数値部分を抽出し整数型に変換

# 実行例
- サンプルHTMLで1回だけ実行:\
  python -m src.scrape_atjam2025 --html samplehtml.txt --interval 0 --output data/atjam2025_data.json

- 実サイトから取得:\
  python -m src.scrape_atjam2025 --html https://up-t.jp/collabo/atjam2025 --interval 0 --output data/atjam2025_data.json
