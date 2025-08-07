import os
import time
import argparse
import json
from bs4 import BeautifulSoup
import requests
from .data_for_spread import main as spread_main

os.environ['TZ'] = 'Asia/Tokyo'
time.tzset()

def extract_broad_rank_texts(soup):
    # "broad_rank"クラス内の"text_slide"クラスの要素1つの内部をspanで分割し、テキスト部分を「日時」「人名」「点数」に分解してJSON形式で返す
    import re
    results = []
    broad_rank = soup.find(class_="broad-rank")
    if broad_rank:
        slide = broad_rank.find(class_="text_slide")
        if slide:
            for node in slide.contents:
                # span要素以外のテキストノードのみ抽出
                if getattr(node, "name", None) == "span":
                    continue
                text = str(node).strip()
                if text:
                    # 例: "2025年08月06日 17:46 愛崎ユウナのアイテムが1点購入されました。"
                    m = re.match(r"^(\d{4}年\d{2}月\d{2}日 \d{2}:\d{2}) (.+?)のアイテムが(\d+)点購入されました。", text)
                    if m:
                        dt, name, count = m.groups()
                        results.append({
                            "datetime": dt,
                            "name": name,
                            "count": int(count)
                        })
                    else:
                        # パターンに合わない場合はrawで返す
                        results.append({
                            "raw": text
                        })
    return results

def extract_rank_table(soup):
    # "rank-table"クラス内"even"クラスの<tr>の内容（name, point）
    results = []
    rank_table = soup.find(class_="rank-table")
    if not rank_table:
        return results
    for tr in rank_table.find_all("tr"):
        name = None
        point = None
        name_tag = tr.find(class_="name-rank")
        if name_tag:
            name = name_tag.get_text(strip=True)
        box_text = tr.find(class_="box-text")
        if box_text:
            # "合計："などを除き数値部分のみ抽出
            import re
            m = re.search(r'(\d+)', box_text.get_text())
            if m:
                point = int(m.group(1))
        if name is not None and point is not None:
            results.append({"name": name, "point": point})
    return results

def run_once(html_path, output_path):
    # URLかローカルファイルか判定
    if html_path.startswith("http://") or html_path.startswith("https://"):
        try:
            resp = requests.get(html_path)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            print(f"Error fetching URL: {e}")
            return
    else:
        with open(html_path, encoding="utf-8") as f:
            html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    broad_rank_texts = extract_broad_rank_texts(soup)
    rank_table = extract_rank_table(soup)
    data = {
        "broad_rank_texts": broad_rank_texts,
        "rank_table": rank_table,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    }
    # 既存データに追記
    try:
        with open(output_path, encoding="utf-8") as f:
            all_data = json.load(f)
    except Exception:
        all_data = []
    all_data.append(data)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    # data_for_spread.pyのmain関数を呼び出し
    try:
        spread_main(data)
    except Exception as e:
        print(f"Error in data_for_spread: {e}")
    print(f"Scraped and saved at {data['timestamp']}")
    return data

def main(html_path, interval, output_path):
    import math
    if interval <= 0:
        # 1回だけ実行
        return run_once(html_path, output_path)

    # 毎時0分0秒を基準にinterval秒ごとに実行
    while True:
        start_time = time.time()
        data = run_once(html_path, output_path)
        # 次の実行時刻を計算
        now = time.time()
        # 現在時刻を「毎時0分0秒」基準のinterval倍数に切り上げ
        next_exec = math.ceil(now / interval) * interval
        sleep_time = next_exec - now
        if sleep_time > 0:
            time.sleep(sleep_time)
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="atjam2025情報収集")
    parser.add_argument("--html", default="https://up-t.jp/collabo/atjam2025", help="HTMLファイルパス")
    parser.add_argument("--interval", type=int, default=0, help="実行間隔（秒）。0以下で1回のみ")
    parser.add_argument("--output", default="atjam2025_data.json", help="出力jsonファイル")
    args = parser.parse_args()
    main(args.html, args.interval, args.output)
