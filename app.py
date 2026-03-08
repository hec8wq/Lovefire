from flask import Flask, render_template, request, session
from functools import lru_cache  # キャッシュ用（オプション）
import random  # デバッグ用にランダムスコアも可

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # セッション用

# データ定義（変更なし）
zodiac_elements = {
    '牡羊座': '火', '牡牛座': '地', '双子座': '風', '蟹座': '水',
    '獅子座': '火', '乙女座': '地', '天秤座': '風', '蠍座': '水',
    '射手座': '火', '山羊座': '地', '水瓶座': '風', '魚座': '水'
}
zodiacs = list(zodiac_elements.keys())
blood_types = ['A', 'B', 'O', 'AB']
mbtis = ['INTJ','INTP','ENTJ','ENTP','INFJ','INFP','ENFJ','ENFP',
         'ISTJ','ISFJ','ESTJ','ESFJ','ISTP','ISFP','ESTP','ESFP']
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

    # 同じ属性が最強、その次に水×地・火×風
    if e1 == e2:
        return 95  # 同属性：魚×蟹、魚×蠍、牡牛×乙女 など

    pair = (e1, e2)

    # 良い組み合わせ（属性相性が高い）
    good_pairs = {
        ('水', '地'), ('地', '水'),   # 水が地に潤い、地が水を受け止める
        ('火', '風'), ('風', '火'),   # 火を風が煽る、風が火に刺激を与える
    }
    if pair in good_pairs:
        return 88

    # まあまあ（中立〜やや良い）
    neutral_pairs = {
        ('火', '地'), ('地', '火'),
        ('風', '水'), ('水', '風'),
    }
    if pair in neutral_pairs:
        return 75

    # それ以外はちょっと噛み合いにくい
    return 60

def blood_score(my_b, p_b):
    table = {
        ('A','A'): 80,   # 同型安定だがマンネリ気味
        ('A','O'): 95,   # 最強補完（Oの包容×Aの真面目）
        ('A','B'): 50,   # 衝突しやすい
        ('A','AB'): 70,
        ('O','A'): 95,
        ('O','O'): 85,
        ('O','B'): 80,
        ('O','AB'): 85,
        ('B','A'): 50,
        ('B','O'): 80,
        ('B','B'): 85,   # 自由同士でラク
        ('B','AB'): 75,
        ('AB','A'): 70,
        ('AB','O'): 85,
        ('AB','B'): 75,
        ('AB','AB'): 80,
    }
    return table.get((my_b, p_b), 65)

# MBTI相性テーブル（双方向意識・全16タイプ拡張版）
mbti_compat = {
    # INTJ (建築家) - 戦略的・論理的
    'INTJ': {
        'ENFP': 95,      # 最高のゴールデンペア（Ne-FiがNi-Teを刺激）
        'INFJ': 92,
        'ENTP': 90,
        'INTP': 88,
        'ESFJ': 85,
        'ENFJ': 82,
    },

    # INFJ (提唱者) - 洞察力・理想主義
    'INFJ': {
        'ENFP': 95,
        'ENTP': 92,
        'INTJ': 90,
        'INFP': 88,
        'ENFJ': 85,
    },

    # INTP (論理学者) - 分析的・好奇心旺盛
    'INTP': {
        'ENTJ': 95,      # 機能補完強い
        'ESTJ': 90,
        'INTJ': 88,
        'ENTP': 85,
        'INFJ': 82,
    },

    # INFP (仲介者) - 理想・共感力
    'INFP': {
        'ENFJ': 95,
        'ENTJ': 92,
        'ENFP': 90,
        'INFJ': 88,
        'ISFJ': 85,
    },

    # ENTJ (指揮官) - リーダー・決断力
    'ENTJ': {
        'INFP': 95,
        'INTP': 92,
        'INTJ': 90,
        'ENFJ': 88,
        'ESTJ': 85,
    },

    # ENTP (討論者) - 革新的・議論好き
    'ENTP': {
        'INFJ': 95,
        'INTJ': 92,
        'ENFP': 90,
        'INTP': 88,
        'ENTJ': 85,
    },

    # ENFP (運動家) - 情熱的・創造的
    'ENFP': {
        'INTJ': 95,      # 定番ゴールデンペア
        'INFJ': 92,
        'ENTP': 90,
        'INFP': 88,
        'ENFJ': 85,
    },

    # ENFJ (主人公) - 共感・リーダーシップ
    'ENFJ': {
        'INFP': 95,
        'ISFP': 92,
        'ENFP': 90,
        'ENTJ': 88,
        'INFJ': 85,
    },

    # ISTJ (管理者) - 責任感・現実的
    'ISTJ': {
        'ESFJ': 95,
        'ESTJ': 92,
        'ISFJ': 90,
        'INTJ': 85,
        'ESTP': 82,
    },

    # ISFJ (擁護者) - 献身的・思いやり
    'ISFJ': {
        'ESTJ': 95,
        'ESFJ': 92,
        'ISTJ': 90,
        'ISFP': 88,
        'ENFJ': 85,
    },

    # ESTJ (幹部) - 組織的・効率重視
    'ESTJ': {
        'ISFJ': 95,
        'ISTJ': 92,
        'ESFJ': 90,
        'INTP': 88,
        'ENTJ': 85,
    },

    # ESFJ (領事) - 社交的・調和重視
    'ESFJ': {
        'ISTJ': 95,
        'ISFJ': 92,
        'ESTJ': 90,
        'ENFP': 85,
        'INTJ': 82,
    },

    # ISTP (巨匠) - 実践的・独立
    'ISTP': {
        'ESFJ': 92,
        'ESTJ': 90,
        'ESTP': 88,
        'ISFP': 85,
        'ENTP': 82,
    },

    # ISFP (冒険家) - 芸術的・穏やか
    'ISFP': {
        'ENFJ': 95,
        'ESFJ': 92,
        'ISTP': 88,
        'INFP': 85,
    },

    # ESTP (起業家) - 行動的・冒険好き
    'ESTP': {
        'ISFJ': 92,
        'ISTJ': 90,
        'ESFP': 88,
        'ISTP': 85,
    },

    # ESFP (エンターテイナー) - 陽気・社交的
    'ESFP': {
        'ISFJ': 92,
        'ESTP': 90,
        'ENFP': 88,
        'ESFJ': 85,
    }
}

def mbti_score(my_m, p_m):
    if my_m == p_m:
        return 80
    return mbti_compat.get(my_m, {}).get(p_m, 60)

# 恋愛タイプ（双方向を意識して少し増やす）
# 恋愛タイプ相性テーブル（双方向意識・全16タイプ拡張版）
love_compat = {
    # LCRO: ボス猫
    'ボス猫': {
        '最後の恋人': 95,       # 最強補完（リード×サポート）
        '忠犬ハチ公': 92,
        'キャプテンライオン': 90,
        'カリスマバランサー': 88,
        'ちゃっかりうさぎ': 85,
    },

    # LCRE: 隠れベイビー
    '隠れベイビー': {
        '敏腕マネージャー': 95,   # 甘えを完璧に受け止める
        '憧れの先輩': 92,
        'ボス猫': 90,
        '忠犬ハチ公': 88,
        '最後の恋人': 85,
    },

    # LCPO: 主役体質
    '主役体質': {
        'デビル天使': 95,
        '恋愛モンスター': 92,
        'ボス猫': 90,
        'ツンデレヤンキー': 88,
        '敏腕マネージャー': 85,
    },

    # LCPE: ツンデレヤンキー
    'ツンデレヤンキー': {
        '恋愛モンスター': 95,
        '主役体質': 92,
        'キャプテンライオン': 90,
        'ボス猫': 85,
    },

    # LARO: 憧れの先輩
    '憧れの先輩': {
        '忠犬ハチ公': 95,
        '隠れベイビー': 92,
        'ちゃっかりうさぎ': 90,
        'カリスマバランサー': 88,
        'ロマンスマジシャン': 85,
    },

    # LARE: カリスマバランサー
    'カリスマバランサー': {
        'ちゃっかりうさぎ': 95,   # 現実派×甘えの神相性
        '憧れの先輩': 92,
        'パーフェクトカメレオン': 90,
        '恋愛モンスター': 88,
        'ボス猫': 85,
    },

    # LAPO: パーフェクトカメレオン
    'パーフェクトカメレオン': {
        'カリスマバランサー': 95,
        'デビル天使': 92,
        'ちゃっかりうさぎ': 90,
        '不思議生命体': 88,
    },

    # LAPE: キャプテンライオン
    'キャプテンライオン': {
        'ロマンスマジシャン': 95,
        '忠犬ハチ公': 92,
        'ボス猫': 90,
        'ツンデレヤンキー': 88,
    },

    # FCRO: ロマンスマジシャン
    'ロマンスマジシャン': {
        'キャプテンライオン': 95,
        '隠れベイビー': 92,
        '憧れの先輩': 90,
        '最後の恋人': 88,
    },

    # FCRE: ちゃっかりうさぎ
    'ちゃっかりうさぎ': {
        'カリスマバランサー': 95,
        '憧れの先輩': 93,
        'ボス猫': 90,
        '忠犬ハチ公': 88,
        '最後の恋人': 85,
        '主役体質': 82,       # 元コードにあったもの
    },

    # FCPO: 恋愛モンスター
    '恋愛モンスター': {
        '主役体質': 95,
        'ツンデレヤンキー': 92,
        'カリスマバランサー': 90,
        'デビル天使': 88,
        '最後の恋人': 85,
    },

    # FCPE: 忠犬ハチ公
    '忠犬ハチ公': {
        '憧れの先輩': 95,
        'キャプテンライオン': 92,
        '隠れベイビー': 90,
        'ボス猫': 88,
        'ちゃっかりうさぎ': 85,
    },

    # FARO: 不思議生命体
    '不思議生命体': {
        '主役体質': 92,
        'パーフェクトカメレオン': 90,
        'デビル天使': 88,
        'ボス猫': 85,
    },

    # FARE: 敏腕マネージャー
    '敏腕マネージャー': {
        '隠れベイビー': 95,
        '主役体質': 92,
        'ちゃっかりうさぎ': 88,
    },

    # FAPO: デビル天使
    'デビル天使': {
        '隠れベイビー': 95,
        '主役体質': 92,
        'パーフェクトカメレオン': 90,
        '恋愛モンスター': 88,
    },

    # FAPE: 最後の恋人
    '最後の恋人': {
        'ボス猫': 95,
        '恋愛モンスター': 92,
        'ロマンスマジシャン': 90,
        '忠犬ハチ公': 88,
        'ちゃっかりうさぎ': 85,
    }
}
def love_score(my_l, p_l):
    if my_l == p_l:
        return 78
    score = love_compat.get(my_l, {}).get(p_l, 0)
    if score > 0:
        return score
    # 逆方向もチェック（簡易双方向）
    score_rev = love_compat.get(p_l, {}).get(my_l, 0)
    return score_rev if score_rev > 0 else 65

# 総合スコア → ★（分布を占いサイト風に調整）
def get_stars(raw_total):
    # 220〜380くらいの範囲を想定 → ★5が上位5%くらいになるよう
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
    l_score = love_score(my_l, p_l)

    # ★ 星座×血液型の補正（安全にここで行う）
    water_signs = ['蟹座', '蠍座', '魚座']
    if my_z in water_signs and p_b in ['O', 'A']:
        z_score += 5
    if p_z in water_signs and my_b in ['O', 'A']:
        z_score += 5

    raw = z_score + b_score + m_score + l_score
    stars = get_stars(raw)
    percent = round((raw - 220) / (380 - 220) * 100, 1)

    return stars, raw, percent

# ------------------------- 
# メインルート
# -------------------------

@app.route('/', methods=['GET', 'POST'])
def home():
    best5 = []
    worst5 = []
    all_best = []  # 全組み合わせの降順リスト
    all_worst = []  # 全組み合わせの昇順リスト
    my_type = None

    if request.method == 'POST':
        my_z = request.form.get('my_zodiac')
        my_b = request.form.get('my_blood')
        my_m = request.form.get('my_mbti')
        my_l = request.form.get('my_love')

        if all([my_z, my_b, my_m, my_l]):
            my_type = (my_z, my_b, my_m, my_l)
            session['my_type'] = my_type

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
                                'zodiac': z,
                                'blood': b,
                                'mbti': m,
                                'love': l,
                                'stars': stars,
                                'raw': raw,
                                'percent': percent
                            })

            # 降順ソート（高い順）
            candidates_sorted_desc = sorted(
                candidates,
                key=lambda x: (x['stars'], x['raw'], x['percent']),
                reverse=True
            )

            # 昇順ソート（低い順）
            candidates_sorted_asc = sorted(
                candidates,
                key=lambda x: (x['stars'], x['raw'], x['percent']),
                reverse=False
            )

            best5 = candidates_sorted_desc[:5]
            worst5 = candidates_sorted_asc[:5]  # 低い順のトップ5がワースト5

            all_best = candidates_sorted_desc  # 全リスト（高い順）
            all_worst = candidates_sorted_asc  # 全リスト（低い順）

    elif 'my_type' in session:
        my_type = session['my_type']

    return render_template(
        'index.html',
        best5=best5,
        worst5=worst5,
        all_best=all_best,     # BESTの下に表示する全リスト（降順）
        all_worst=all_worst,   # WORSTの下に表示する全リスト（昇順）
        my_type=my_type
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)