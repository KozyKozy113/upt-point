# ベースイメージ
FROM python:3.11-slim

# コンテナ内作業ディレクトリ
WORKDIR /workspaces/愛ちゃんポイント収集

# ホストの requirements.txt をコピー＆インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードをコピー
COPY . .

# デフォルトのコマンド
ENTRYPOINT ["python", "-m", "src.scrape_atjam2025"]

CMD ["--interval", "60"]
