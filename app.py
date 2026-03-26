from flask import Flask, render_template, request, session
from functools import lru_cache  # キャッシュ用（オプション）
import random  # デバッグ用にランダムスコアも可

app = Flask(__name__)
# セッション用のキーも新しく「love-file-key-2026」に変更
app.secret_key = 'love-file-key-2026'

# データ定義
zodiac_elements = {
    '牡羊座': '火', '牡牛座': '地', '双子座': '風', '蟹座': '水',
    '獅子座': '火', '乙女座': '地', '天秤座': '風', '蠍座': '水',
    '射手座': '火', '山羊座': '地', '水瓶座': '風', '魚座': '水'
}
zodiacs = list(zodiac_elements.keys())
blood_types = ['A', 'B', 'O', 'AB']
mbtis = [
    # NT（分析・戦略タイプ）
    'INTJ','INTP','ENTJ','ENTP',

    # NF（共感・理想タイプ）
    'INFJ','INFP','ENFJ','ENFP',

    # SJ（安定・実務タイプ）
    'ISTJ','ISFJ','ESTJ','ESFJ',

    # SP（行動・柔軟タイプ）
    'ISTP','ISFP','ESTP','ESFP'
]

# 変数名を love_types から変更なし（内部ロジック用）
love_types = [
    'ボス猫','隠れベイビー','主役体質','ツンデレヤンキー',
    '憧れの先輩','カリスマバランサー','パーフェクトカメレオン','キャプテンライオン',
    'ロマンスマジシャン','ちゃっかりうさぎ','恋愛モンスター','忠犬ハチ公',
    '不思議生命体','敏腕マネージャー','デビル天使','最後の恋人'
]

# -------------------------
# スコア関数
# -------------------------

def zodiac_score(my_z, p_z):
    e1 = zodiac_elements[my_z]
    e2 = zodiac_elements[p_z]

    if e1 == e2:
        return 95

    pair = (e1, e2)
    good_pairs = {
        ('水', '地'), ('地', '水'),
        ('火', '風'), ('風', '火'),
    }
    if pair in good_pairs:
        return 88

    neutral_pairs = {
        ('火', '地'), ('地', '火'),
        ('風', '水'), ('水', '風'),
    }
    if pair in neutral_pairs:
        return 75

    return 60

def blood_score(my_b, p_b):
    # あなたが提示した「公式」に基づくランキング設定
    table = {
        # --- 1位：最強の相性 (100点) ---
        ('A', 'O'): 100,
        ('B', 'O'): 100,
        ('O', 'B'): 100,
        ('AB', 'AB'): 100,

        # --- 2位：かなり良い相性 (85点) ---
        ('A', 'AB'): 85,
        ('B', 'AB'): 85,
        ('O', 'A'): 85,
        ('AB', 'A'): 85,

        # --- 3位：普通の相性 (70点) ---
        ('A', 'A'): 70,
        ('B', 'B'): 70,
        ('O', 'O'): 70,
        ('AB', 'B'): 70,

        # --- 4位：努力が必要な相性 (50点) ---
        ('A', 'B'): 50,
        ('B', 'A'): 50,
        ('O', 'AB'): 50,
        ('AB', 'O'): 50,
    }
    # 万が一データがない場合は平均的な 70点を返す設定
    return table.get((my_b, p_b), 70)

# MBTI相性テーブル
mbti_compat = {
    'INTJ': {'ENFP': 95, 'INFJ': 92, 'ENTP': 90, 'INTP': 88, 'ESFJ': 85, 'ENFJ': 82},
    'INFJ': {'ENFP': 95, 'ENTP': 92, 'INTJ': 90, 'INFP': 88, 'ENFJ': 85},
    'INTP': {'ENTJ': 95, 'ESTJ': 90, 'INTJ': 88, 'ENTP': 85, 'INFJ': 82},
    'INFP': {'ENFJ': 95, 'ENTJ': 92, 'ENFP': 90, 'INFJ': 88, 'ISFJ': 85},
    'ENTJ': {'INFP': 95, 'INTP': 92, 'INTJ': 90, 'ENFJ': 88, 'ESTJ': 85},
    'ENTP': {'INFJ': 95, 'INTJ': 92, 'ENFP': 90, 'INTP': 88, 'ENTJ': 85},
    'ENFP': {'INTJ': 95, 'INFJ': 92, 'ENTP': 90, 'INFP': 88, 'ENFJ': 85},
    'ENFJ': {'INFP': 95, 'ISFP': 92, 'ENFP': 90, 'ENTJ': 88, 'INFJ': 85},
    'ISTJ': {'ESFJ': 95, 'ESTJ': 92, 'ISFJ': 90, 'INTJ': 85, 'ESTP': 82},
    'ISFJ': {'ESTJ': 95, 'ESFJ': 92, 'ISTJ': 90, 'ISFP': 88, 'ENFJ': 85},
    'ESTJ': {'ISFJ': 95, 'ISTJ': 92, 'ESFJ': 90, 'INTP': 88, 'ENTJ': 85},
    'ESFJ': {'ISTJ': 95, 'ISFJ': 92, 'ESTJ': 90, 'ENFP': 85, 'INTJ': 82},
    'ISTP': {'ESFJ': 92, 'ESTJ': 90, 'ESTP': 88, 'ISFP': 85, 'ENTP': 82},
    'ISFP': {'ENFJ': 95, 'ESFJ': 92, 'ISTP': 88, 'INFP': 85},
    'ESTP': {'ISFJ': 92, 'ISTJ': 90, 'ESFP': 88, 'ISTP': 85},
    'ESFP': {'ISFJ': 92, 'ESTP': 90, 'ENFP': 88, 'ESFJ': 85}
}

def mbti_score(my_m, p_m):
    if my_m == p_m:
        return 80
    return mbti_compat.get(my_m, {}).get(p_m, 60)

# 恋愛タイプ相性テーブル
love_file_compat = {
    'ボス猫': {'最後の恋人': 95, '忠犬ハチ公': 92, 'キャプテンライオン': 90, 'カリスマバランサー': 88, 'ちゃっかりうさぎ': 85},
    '隠れベイビー': {'敏腕マネージャー': 95, '憧れの先輩': 92, 'ボス猫': 90, '忠犬ハチ公': 88, '最後の恋人': 85},
    '主役体質': {'デビル天使': 95, '恋愛モンスター': 92, 'ボス猫': 90, 'ツンデレヤンキー': 88, '敏腕マネージャー': 85},
    'ツンデレヤンキー': {'恋愛モンスター': 95, '主役体質': 92, 'キャプテンライオン': 90, 'ボス猫': 85},
    '憧れの先輩': {'忠犬ハチ公': 95, '隠れベイビー': 92, 'ちゃっかりうさぎ': 90, 'カリスマバランサー': 88, 'ロマンスマジシャン': 85},
    'カリスマバランサー': {'ちゃっかりうさぎ': 95, '憧れの先輩': 92, 'パーフェクトカメレオン': 90, '恋愛モンスター': 88, 'ボス猫': 85},
    'パーフェクトカメレオン': {'カリスマバランサー': 95, 'デビル天使': 92, 'ちゃっかりうさぎ': 90, '不思議生命体': 88},
    'キャプテンライオン': {'ロマンスマジシャン': 95, '忠犬ハチ公': 92, 'ボス猫': 90, 'ツンデレヤンキー': 88},
    'ロマンスマジシャン': {'キャプテンライオン': 95, '隠れベイビー': 92, '憧れの先輩': 90, '最後の恋人': 88},
    'ちゃっかりうさぎ': {'カリスマバランサー': 95, '憧れの先輩': 93, 'ボス猫': 90, '忠犬ハチ公': 88, '最後の恋人': 85, '主役体質': 82},
    '恋愛モンスター': {'主役体質': 95, 'ツンデレヤンキー': 92, 'カリスマバランサー': 90, 'デビル天使': 88, '最後の恋人': 85},
    '忠犬ハチ公': {'憧れの先輩': 95, 'キャプテンライオン': 92, '隠れベイビー': 90, 'ボス猫': 88, 'ちゃっかりうさぎ': 85},
    '不思議生命体': {'主役体質': 92, 'パーフェクトカメレオン': 90, 'デビル天使': 88, 'ボス猫': 85},
    '敏腕マネージャー': {'隠れベイビー': 95, '主役体質': 92, 'ちゃっかりうさぎ': 88},
    'デビル天使': {'隠れベイビー': 95, '主役体質': 92, 'パーフェクトカメレオン': 90, '恋愛モンスター': 88},
    '最後の恋人': {'ボス猫': 95, '恋愛モンスター': 92, 'ロマンスマジシャン': 90, '忠犬ハチ公': 88, 'ちゃっかりうさぎ': 85}
}

def love_file_score(my_l, p_l):
    if my_l == p_l:
        return 78
    score = love_file_compat.get(my_l, {}).get(p_l, 0)
    if score > 0:
        return score
    score_rev = love_file_compat.get(p_l, {}).get(my_l, 0)
    return score_rev if score_rev > 0 else 65

# 総合スコア計算
def get_stars(raw_total):
    if raw_total >= 360: return 5.0
    if raw_total >= 345: return 4.5
    if raw_total >= 330: return 4.0
    if raw_total >= 315: return 3.5
    if raw_total >= 300: return 3.0
    if raw_total >= 280: return 2.5
    if raw_total >= 260: return 2.0
    if raw_total >= 240: return 1.5
    if raw_total >= 225: return 1.0
    return 0.5

def total_compatibility(my_type, partner_type):
    my_z, my_b, my_m, my_l = my_type
    p_z, p_b, p_m, p_l = partner_type

    z_score = zodiac_score(my_z, p_z)
    b_score = blood_score(my_b, p_b)
    m_score = mbti_score(my_m, p_m)
    l_score = love_file_score(my_l, p_l)

    raw = z_score + b_score + m_score + l_score

    # 統計的正規化
    PRACTICAL_MIN = 210
    MAX_TOTAL = 400
    raw_clipped = max(PRACTICAL_MIN, raw)

    percent = (raw_clipped - PRACTICAL_MIN) / (MAX_TOTAL - PRACTICAL_MIN) * 100
    percent = max(0.4, percent)
    percent = min(100.0, percent)
    percent = round(percent, 1)

    stars = get_stars(raw)
    return stars, raw, percent

# ------------------------- 
# メインルート (LoveFile)
# -------------------------

# 1. 【ホームページ】 
@app.route('/')
def home_html():
    return render_template('home.html')

# 2. 【診断ページ】
@app.route('/diagnose', methods=['GET', 'POST'])
def diagnose():
    best5, worst5, all_best, all_worst = [], [], [], []
    search_result = None
    p_type = None

    # セッションから前回の入力を取得（表示用）
    my_type = session.get('my_type')
    
    # どのボタンが押されたか確認
    action = request.form.get('action') if request.method == 'POST' else None

    # 「診断する」ボタンが押された場合のみ、自分のタイプを更新
    if action == 'diagnose':
        my_z = request.form.get('my_zodiac')
        my_b = request.form.get('my_blood')
        my_m = request.form.get('my_mbti')
        my_l = request.form.get('my_love')
        if all([my_z, my_b, my_m, my_l]):
            my_type = (my_z, my_b, my_m, my_l)
            session['my_type'] = my_type

    # 👈【ここが重要！】action（ボタン押下）がある時だけ、1万件の計算を実行する
    if my_type and action: 
        candidates = []
        for z in zodiacs:
            for b in blood_types:
                for m in mbtis:
                    for l in love_types:
                        partner = (z, b, m, l)
                        if partner == my_type:
                            continue
                        stars, raw, percent = total_compatibility(my_type, partner)
                        candidates.append({
                            'zodiac': z, 'blood': b, 'mbti': m, 'love': l,
                            'stars': stars, 'raw': raw, 'percent': percent
                        })

        candidates_desc = sorted(candidates, key=lambda x: (x['stars'], x['raw'], x['percent']), reverse=True)
        candidates_asc = sorted(candidates, key=lambda x: (x['stars'], x['raw'], x['percent']), reverse=False)

        best5 = candidates_desc[:5]
        worst5 = candidates_asc[:5]
        all_best = candidates_desc[:100]
        all_worst = candidates_asc[:100]

        # 相手の順位検索
        if action == 'search_rank':
            p_z = request.form.get('p_zodiac')
            p_b = request.form.get('p_blood')
            p_m = request.form.get('p_mbti')
            p_l = request.form.get('p_love')
            p_type = (p_z, p_b, p_m, p_l)
            
            if my_type == p_type:
                search_result = {"error": "自分と全く同じ組み合わせです（診断対象外です）"}
            else:
                for idx, item in enumerate(candidates_desc, start=1):
                    if (item['zodiac'] == p_z and item['blood'] == p_b and
                        item['mbti'] == p_m and item['love'] == p_l):
                        search_result = {
                            'rank': idx,
                            'total_count': len(candidates_desc),
                            'zodiac': p_z, 'blood': p_b, 'mbti': p_m, 'love': p_l,
                            'percent': item['percent'], 'stars': item['stars']
                        }
                        break

    return render_template(
        'index.html',
        best5=best5, worst5=worst5,
        all_best=all_best, all_worst=all_worst,
        my_type=my_type, p_type=p_type, search_result=search_result
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)