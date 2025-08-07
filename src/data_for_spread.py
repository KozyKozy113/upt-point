import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- 設定 ---
SERVICE_ACCOUNT_FILE = 'google_service_account.json'  # ダウンロードしたサービスアカウント JSON
SPREADSHEET_ID      = '1-xZeooGI0_s7PCmIL_7LNBMeTaZ9_PzoX9lyOOF1WX0'    # スプレッドシート ID
# ----------------

def auth_gspread():
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds  = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
    return gspread.authorize(creds)

gc = auth_gspread()


def get_worksheet(name: str):
    """名前でワークシートを開く"""
    sh = gc.open_by_key(SPREADSHEET_ID)
    return sh.worksheet(name)


def append_purchase_records(records: list[dict], update_ts: str):
    """
    「直近の購入実績」シートへ追加。
     - 過去に同じ(datetime, name, count)が登録済みならスキップ
     - 同一更新内の重複は許容
     - 追加後に「購入日時」で降順ソート
    """
    ws = get_worksheet("直近の購入実績")
    all_rows = ws.get_all_values()[1:]  # ヘッダ行を除くすべての既存行
    existing = {(r[0], r[1], r[2]) for r in all_rows}

    to_append = []
    for rec in records:
        key = (rec["datetime"], rec["name"], str(rec["count"]))
        if key not in existing:
            to_append.append([rec["datetime"], rec["name"], rec["count"], update_ts])

    if to_append:
        ws.append_rows(to_append, value_input_option='USER_ENTERED')

    # 購入日時（1列目）で降順ソート
    # sort((col_index, 'desc'))
    ws.sort((1, 'des'))


def update_overall_ranking_points(ranking: list[dict], update_ts: str):
    """
    「全体ランキング(ポイント)」シートへ、
     - 1行目に名前一覧を揃え（初回は新規入力）
     - 新しい行（先頭=2行目, ヘッダ=update_ts）を上に追加
     - 各列に該当ユーザーのポイントを入力
    """
    ws = get_worksheet("全体ランキング(ポイント)")

    # 1行目: 名前一覧
    header = ws.row_values(1)
    new_names = [item["name"] for item in ranking]
    if not header:
        header = [""] + new_names
        ws.append_row(header)
    else:
        # 追記が必要な名前を追加
        missing = [n for n in new_names if n not in header[1:]]
        if missing:
            header += missing
            ws.update('1:1', [header])

    # 既存の全データ取得
    all_values = ws.get_all_values()
    # 既に同じ更新があれば何もしない
    for row in all_values[1:]:
        if row and row[0] == update_ts:
            return

    # 名前→列番号マップ
    header = ws.row_values(1)
    name_to_col = {header[i]: i+1 for i in range(1, len(header))}

    # 新しい行データ（1列目はupdate_ts, 2列目以降はポイント）
    row_data = [update_ts]
    for name in header[1:]:
        val = next((item["point"] for item in ranking if item["name"] == name), "")
        row_data.append(val)

    # 既存データを下にずらして新しい行を2行目に挿入
    if len(all_values) > 1:
        ws.insert_row(row_data, 2)
    else:
        ws.append_row(row_data)


def update_overall_ranking_positions(ranking: list[dict], update_ts: str):
    """
    「全体ランキング(順位)」シートへ、
     - 1行目に名前一覧を揃え（ポイントシートと同様）
     - 新しい行（先頭=2行目, ヘッダ=update_ts）を上に追加
     - rankingリストの順序をそのまま順位（1,2,3…）として入力
    """
    ws = get_worksheet("全体ランキング(順位)")

    # 1行目: 名前一覧
    header = ws.row_values(1)
    new_names = [item["name"] for item in ranking]
    if not header:
        header = [""] + new_names
        ws.append_row(header)
    else:
        missing = [n for n in new_names if n not in header[1:]]
        if missing:
            header += missing
            ws.update('1:1', [header])

    # 既存の全データ取得
    all_values = ws.get_all_values()
    for row in all_values[1:]:
        if row and row[0] == update_ts:
            return

    # 新しい行データ（1列目はupdate_ts, 2列目以降は順位）
    row_data = [update_ts]
    for name in header[1:]:
        idx = next((i+1 for i, item in enumerate(ranking) if item["name"] == name), "")
        row_data.append(idx)

    # 既存データを下にずらして新しい行を2行目に挿入
    if len(all_values) > 1:
        ws.insert_row(row_data, 2)
    else:
        ws.append_row(row_data)


def main(data: dict):
    """
    data = {
      "broad_rank_texts": [ { "datetime": "...", "name": "...", "count": ... }, … ],
      "rank_table":        [ { "name": "...", "point": … }, … ],
      "timestamp":         "YYYY-MM-DD HH:mm:ss"
    }
    """
    ts = data["timestamp"]
    append_purchase_records(data["broad_rank_texts"], ts)
    update_overall_ranking_points(data["rank_table"], ts)
    update_overall_ranking_positions(data["rank_table"], ts)


if __name__ == "__main__":
    import json
    # stdin などから読み込む例
    payload = json.load(open("input.json", encoding="utf-8"))
    main(payload)
