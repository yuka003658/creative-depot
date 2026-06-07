"""
CREATIVE DEPOT - Backend API Server

起動方法:
  pip install -r requirements.txt
  python server.py

Gemini AI（無料枠）に切り替える場合:
  GEMINI_API_KEY=your_key python server.py
  ※ https://aistudio.google.com/app/apikey で無料取得可能
"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import requests
from bs4 import BeautifulSoup
import os, json, base64, io
from pathlib import Path
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

# .env ファイルがあれば自動読み込み
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# ----------------------------------------------------------------
# 設定: ANTHROPIC_API_KEY > GROQ_API_KEY > GEMINI_API_KEY の優先順
# ----------------------------------------------------------------
GEMINI_API_KEY    = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
USE_ANTHROPIC = bool(ANTHROPIC_API_KEY)
USE_GEMINI    = bool(GEMINI_API_KEY) and not USE_ANTHROPIC
USE_GROQ      = bool(GROQ_API_KEY) and not USE_ANTHROPIC and not USE_GEMINI
USE_AI        = USE_ANTHROPIC or USE_GEMINI or USE_GROQ

BASE_DIR = Path(__file__).parent

app = FastAPI(title="CREATIVE DEPOT API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------
# マスターリスト（フロントの選択肢と一致させること）
# ----------------------------------------------------------------
CATEGORIES = [
    "ブランディング", "マス＆ビジュアル表現", "テレビCM・WEB動画",
    "パッケージデザイン・装丁", "SNS施策・キャンペーン", "WEBサイト・UI/UX",
    "イベント・ポップアップストア", "インストア・販促プロモーション",
    "空間デザイン・環境演出", "PR・ソーシャルグッド（SDGs）",
    "ゲリラマーケティング", "AI・最新テック活用", "メタバース・ゲーム内施策",
]

INDUSTRIES = [
    "食品・飲料", "ファッション・アパレル", "ビューティ・コスメ", "テクノロジー・IT",
    "自動車・モビリティ", "金融・保険", "小売・EC", "エンタメ・メディア",
    "スポーツ・アウトドア", "医療・ヘルスケア", "教育", "不動産・建設",
    "旅行・ホスピタリティ", "NPO・社会貢献", "その他",
]

# キーワードベースの簡易検出テーブル（モックAI用）
CATEGORY_HINTS = [
    ("SNS施策・キャンペーン",       ["sns", "twitter", "instagram", "tiktok", "viral", "キャンペーン", "ハッシュタグ", "拡散", "投稿"]),
    ("テレビCM・WEB動画",           ["cm", "動画", "video", "youtube", "commercial", "映像", "広告動画", "spot"]),
    ("AI・最新テック活用",           ["ai", "人工知能", "artificial intelligence", "chatgpt", "ar ", "vr ", "ジェネレーティブ", "生成ai"]),
    ("WEBサイト・UI/UX",            ["web", "ウェブ", " ui ", " ux ", "サイト", "アプリ", "app", "ランディング"]),
    ("イベント・ポップアップストア", ["イベント", "ポップアップ", "event", "展示", "体験型", "期間限定", "リアル体験"]),
    ("パッケージデザイン・装丁",     ["パッケージ", "package", "装丁", "容器", "缶", "ボトル"]),
    ("PR・ソーシャルグッド（SDGs）", ["sdg", " pr ", "社会課題", "環境", "サステナ", "寄付", "社会貢献"]),
    ("ゲリラマーケティング",         ["ゲリラ", "屋外", "街頭", "ooh", "out of home", "サプライズ"]),
    ("ブランディング",               ["ブランド", "brand", "リブランディング", "identity", "vi ", "ci "]),
]

INDUSTRY_HINTS = [
    ("食品・飲料",         ["food", "飲料", "食品", "レストラン", "カフェ", "ビール", "コーヒー", "飲み物", "お菓子"]),
    ("ファッション・アパレル", ["fashion", "ファッション", "アパレル", "clothing", "服", "ウェア", "wear"]),
    ("ビューティ・コスメ", ["beauty", "コスメ", "化粧品", "skincare", "makeup", "美容", "ヘアケア"]),
    ("テクノロジー・IT",   ["tech", "テック", "software", "スタートアップ", "サービス", "saas", "it企業"]),
    ("エンタメ・メディア", ["entertainment", "music", "film", "映画", "音楽", "spotify", "netflix", "メディア"]),
    ("スポーツ・アウトドア", ["sport", "スポーツ", "nike", "adidas", "outdoor", "アスリート", "運動"]),
    ("自動車・モビリティ", ["car", "車", "自動車", "モビリティ", "ev", "バイク", "乗り物"]),
    ("旅行・ホスピタリティ", ["旅行", "ホテル", "travel", "hotel", "観光", "宿泊", "airline", "航空"]),
    ("医療・ヘルスケア",   ["医療", "ヘルス", "health", "病院", "薬", "wellness", "フィットネス"]),
    ("金融・保険",         ["金融", "保険", "finance", "bank", "銀行", "investment", "投資"]),
]

def extract_json(text: str) -> dict:
    """レスポンステキストから最初の有効なJSONオブジェクトを抽出する。"""
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i, ch in enumerate(text[start:], start):
        if escape:
            escape = False
            continue
        if ch == '\\' and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except Exception:
                    return None
    return None

def detect_category(text: str) -> str:
    t = text.lower()
    for cat, hints in CATEGORY_HINTS:
        if any(h in t for h in hints):
            return cat
    return "ブランディング"

def detect_industry(text: str) -> str:
    t = text.lower()
    for ind, hints in INDUSTRY_HINTS:
        if any(h in t for h in hints):
            return ind
    return "その他"

# ----------------------------------------------------------------
# カテゴリ別テンプレート（モックAI用）
# ----------------------------------------------------------------
INSIGHTS = {
    "ブランディング": "消費者は製品の機能よりも、ブランドが体現する「価値観・世界観」に自分を重ねて購買を決断する。",
    "マス＆ビジュアル表現": "圧倒的なビジュアルは、スマートフォンの画面を超えた「強烈な現実体験」として拡散される。",
    "テレビCM・WEB動画": "誰もが共感できる「人間の本質」を描いたドラマには感情移入し、スキップされずに見てしまう。",
    "パッケージデザイン・装丁": "現代の消費者はパッケージの「手触り感・開封体験」という情緒的価値にお金を払う。",
    "SNS施策・キャンペーン": "「自分のセンスをフォロワーにアピールできる大義名分」があれば、ユーザーは喜んでコンテンツを拡散する。",
    "WEBサイト・UI/UX": "小気味よいインタラクションで心地よい反応が返ってくると、ゲーム感覚で滞在時間が伸びる。",
    "イベント・ポップアップストア": "「その場所でしかできない五感体験」と希少性がプレミアム感を生み出す。",
    "インストア・販促プロモーション": "「宝探し体験」があると衝動買いへのハードルが下がる。",
    "空間デザイン・環境演出": "物理空間の体験は視覚情報より脳に直接作用し、記憶を感情に長期間結びつける。",
    "PR・ソーシャルグッド（SDGs）": "社会課題をエンターテインメントに昇華させると、自発的な協力エコシステムが生まれる。",
    "ゲリラマーケティング": "日常に「小さな異物」が混入すると、強烈な違和感からSNS投稿欲求が生まれる。",
    "AI・最新テック活用": "完璧なパーソナライズ情報は、驚きとともに特別な体験として自然に受け入れられる。",
    "メタバース・ゲーム内施策": "ゲーム体験の一部としてブランドが溶け込めば、広告と感じさせずに受容される。",
}

SOLUTIONS = {
    "ブランディング": "一貫したメッセージングで情緒的コミュニケーションを設計し、強固なブランドポジションを確立した。",
    "マス＆ビジュアル表現": "デジタルでは再現できないスケールのビジュアルを展開し、話題化と認知拡大を達成した。",
    "テレビCM・WEB動画": "感情豊かなストーリー仕立てのムービーでSNS拡散されるブランディング動画を構築した。",
    "パッケージデザイン・装丁": "素材感から開封体験まで設計し、誰かに自慢したくなるデザインを実現した。",
    "SNS施策・キャンペーン": "参加・投稿したくなる「お題」を設計し、トレンド入りさせる拡散の輪を生み出した。",
    "WEBサイト・UI/UX": "3D演出とインタラクションで、ブランド世界観をシームレスに体験できるサイトを構築した。",
    "イベント・ポップアップストア": "写真映えする体験型空間で、来場者が自発的に拡散する仕掛けを設計した。",
    "インストア・販促プロモーション": "目を引く什器と明快なインセンティブで、購買を後押しする体験を設計した。",
    "空間デザイン・環境演出": "テクノロジーとアートを融合させ、歩くたびにブランド理念を体感できる空間を構築した。",
    "PR・ソーシャルグッド（SDGs）": "参加自体が社会貢献になるエコシステムを設計し、大きなパブリシティを獲得した。",
    "ゲリラマーケティング": "日常インフラをハックするゲリラ施策で、SNSとメディアの自然拡散を最大化した。",
    "AI・最新テック活用": "リアルタイムデータでAIがパーソナライズ表現を生成し、双方向の新体験を提供した。",
    "メタバース・ゲーム内施策": "独自ゲームとアバターアイテムで、ゲーム体験を通じたブランドエンゲージメントを実現した。",
}

APPROACHES = {
    "ブランディング": "ブランドの「信念・パーパス」を前面に打ち出し、製品の機能訴求を脇に置く逆転の発想。消費者が「このブランドを使うこと＝自分の価値観の表明」と感じられるよう、一貫したナラティブで感情的つながりを設計する。",
    "マス＆ビジュアル表現": "「デジタルでは再現不可能な体験」を逆手に取り、オフラインのスケールそのものをコンテンツ化。来街者が自発的に撮影・シェアする口コミの起点として設計する。",
    "テレビCM・WEB動画": "製品を「主役」から「脇役」に降格させ、普遍的な人間ドラマを前面に。視聴者が「自分のことだ」と感じる瞬間にブランドがそっと寄り添う構造で、説得ではなく共鳴によって好意を醸成する。",
    "パッケージデザイン・装丁": "パッケージ自体を「広告媒体かつSNSコンテンツ」として設計。棚で目を奪うだけでなく、開封・使用のすべてのシーンで写真に撮りたくなる仕掛けを仕込み、製品が自ら拡散する構造を作る。",
    "SNS施策・キャンペーン": "ブランドが「舞台装置」を用意し、主役はユーザー自身に委ねる参加型フォーマットを設計。企業メッセージを伝えるのではなく、ユーザーが自己表現したくなる「お題」を作ることで自走拡散を生む。",
    "WEBサイト・UI/UX": "情報設計ではなく「体験設計」を起点に据える。ユーザーのスクロールやクリックに世界観で応答するインタラクションを軸に、ブランドの世界に没入させながら自然にCTAへ誘導する動線を設計する。",
    "イベント・ポップアップストア": "「今ここにしかない体験」を設計し、ブランドとの記憶を身体に刻む。来場者が写真を撮らずにはいられない仕掛けを随所に配置し、会場の外へ口コミが広がるメディア化した空間を作る。",
    "インストア・販促プロモーション": "購買の「最後の1メートル」を制する什器・POPを起点に、店頭体験そのものをプロモーションメディア化。「なぜ今買うべきか」が一瞬で伝わる訴求と希少性演出で、迷いを決断に変換する。",
    "空間デザイン・環境演出": "空間を「ブランドの思想を歩いて体験できる物語」として再設計。入口から出口まで動線をナラティブで貫き、歩を進めるごとにブランドの世界観への没入が深まる体験設計を行う。",
    "PR・ソーシャルグッド（SDGs）": "社会課題解決をエンターテインメントとして設計し、参加すること自体を報酬にする。ユーザーの行動変容を「お願い」ではなく「楽しい選択肢」として提示し、善意をムーブメントに変える。",
    "ゲリラマーケティング": "広告費ゼロで「ニュース」を作る。街や公共空間を文脈ごとハックし、「なぜここに？」という違和感と驚きでメディアとSNSが自発的に拡散する事件を起こす。",
    "AI・最新テック活用": "テクノロジーを「精度向上ツール」ではなく「体験創造エンジン」として活用。ユーザーのリアルタイムな文脈をAIが解釈し、その瞬間にしか存在しないパーソナライズされた表現を生成する体験設計を行う。",
    "メタバース・ゲーム内施策": "広告枠を買うのではなく、ゲームの「コンテンツそのもの」になる。ブランド世界観をゲームの語法で翻訳し、ユーザーが遊ぶ中で自然にブランドへの親密度が高まる体験を設計する。",
}

# ----------------------------------------------------------------
# Models
# ----------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    url: str
    category: str = ""
    title: str = ""      # 同一URL内の複数コンテンツを絞り込む際のヒント
    keywords: list = []  # 関連キーワード（検索クエリ強化用）
    user_memo: str = ""  # ユーザーが記述した着眼点メモ（AI解析の最優先インプット）

class SearchRequest(BaseModel):
    keywords: list
    category: str = ""
    industry: str = ""
    user_memo: str = ""  # ユーザーが記述した着眼点メモ

class BatchAnalyzeItem(BaseModel):
    submitter: str = ""
    title: str = ""      # ページ内の絞り込みヒント
    url: str
    keywords: list = []  # 関連キーワード
    user_memo: str = ""  # ユーザーが記述した着眼点メモ

class BatchAnalyzeRequest(BaseModel):
    items: list[BatchAnalyzeItem]

# ----------------------------------------------------------------
# スクレイピング
# ----------------------------------------------------------------
def scrape_url(url: str) -> dict:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=12)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    def meta(prop, attr="property"):
        tag = soup.find("meta", {attr: prop})
        return (tag.get("content", "") if tag else "").strip()

    title = (
        meta("og:title")
        or (soup.find("h1").get_text(strip=True) if soup.find("h1") else "")
        or (soup.find("title").get_text(strip=True) if soup.find("title") else "")
    )
    description = meta("og:description") or meta("description", "name")
    thumbnail = meta("og:image")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    body_text = " ".join(soup.get_text(" ", strip=True).split())[:2000]

    return {
        "title": title,
        "description": description,
        "thumbnail": thumbnail,
        "body_text": body_text,
    }

# ----------------------------------------------------------------
# テキストユーティリティ
# ----------------------------------------------------------------
import re as _re

_NOISE_PAT = _re.compile(
    r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\s*[··]?\s*',
    _re.IGNORECASE,
)
_NOISE_KEYWORDS = (
    "ご確認", "クリック", "cookie", "javascript",
    "copyright", "all rights reserved", "privacy policy",
    "会員登録", "ログイン", "メールアドレス",
)

def _clean_text(text: str) -> str:
    """DDGスニペットから日付プレフィックスや中点記号などのノイズを除去する。"""
    text = _NOISE_PAT.sub("", text)
    text = text.replace("·", " ").replace("·", " ")
    # 連続スペースを1つに
    text = " ".join(text.split())
    return text

def _pick_sentences(text: str, max_chars: int = 280) -> str:
    """テキストから情報量の多い文を優先して抽出し、max_chars 以内で返す。"""
    text = _clean_text(text)
    # 【...】ブロックヘッダーを取り除く
    lines = [l for l in text.splitlines() if not (l.startswith("【") and l.endswith("】"))]
    text = "\n".join(lines)

    parts = []
    for sep in ("。", ". ", "！", "? ", "\n"):
        candidate = [s.strip() for s in text.split(sep) if s.strip()]
        if len(candidate) > 2:
            parts = candidate
            break
    if not parts:
        parts = [s.strip() for s in text.split() if len(s.strip()) > 20]

    # 日本語文字の割合（ひらがな・カタカナ・漢字）
    def _jp_ratio(t):
        jp = sum(1 for c in t if '぀' <= c <= '鿿')
        return jp / max(len(t), 1)

    scored = []
    for s in parts:
        if len(s) < 20 or len(s) > 200:
            continue
        s_lower = s.lower()
        if any(kw in s_lower for kw in _NOISE_KEYWORDS):
            continue
        # Wikipedia / 辞書系のコンテンツを除外
        if "wikipedia" in s_lower or "wikimedia" in s_lower:
            continue
        jp = _jp_ratio(s)
        score = sum([
            any(c.isdigit() for c in s) * 1,
            len([c for c in s if c.isupper()]) * 1,       # 固有名詞
            min(len(s) // 30, 4),
            jp * 6,                                        # 日本語コンテンツを強く優先
            ("施策" in s or "ブランド" in s or "戦略" in s) * 5,
            ("広告" in s or "マーケティング" in s or "キャンペーン" in s) * 4,
            ("SNS" in s or "動画" in s or "コンテンツ" in s) * 3,
        ])
        scored.append((score, s))
    scored.sort(reverse=True)
    result, total = [], 0
    for _, s in scored:
        if total + len(s) + 1 > max_chars:
            break
        result.append(s)
        total += len(s) + 1
    return "。".join(result) if result else ""

# ----------------------------------------------------------------
# モックAI（APIキーなしで動作）
# カテゴリ・業界を自動検出し、実際のコンテンツ・Web検索結果を活用
# ----------------------------------------------------------------
def mock_analysis(
    title: str, description: str, body_text: str,
    category: str = "", industry: str = "", focus_title: str = "",
    extra_context: str = "", user_memo: str = ""
) -> dict:
    effective_title = focus_title or title
    # user_memo を最優先素材として先頭に置く
    combined = f"{user_memo} {description} {body_text} {extra_context}"
    search_text = f"{effective_title} {combined[:600]}"

    detected_category = category or detect_category(search_text)
    detected_industry = industry or detect_industry(search_text)

    # ── Brief ────────────────────────────────────────────────────────
    # user_memo があれば最優先で使い、なければ description/body_text から抽出
    if user_memo and len(user_memo) > 30:
        raw_brief = user_memo[:300]
        brief = (
            f"「{effective_title}」について、着眼点として次の点が挙げられた：{raw_brief}。\n\n"
            "この視点を起点に、ターゲット層への新しいアプローチとブランド独自のポジションを確立することが求められていた。"
        )
    else:
        raw_brief = description or _pick_sentences(body_text, 300) or _pick_sentences(extra_context, 300)
        if focus_title and focus_title.lower() not in title.lower():
            brief = (
                f"「{focus_title}」は、{raw_brief[:260]}という背景から生まれた施策。"
                "ターゲット層への新たなリーチと、ブランド独自のポジションを確立することが求められていた。"
            )
        elif raw_brief:
            brief = (
                f"{raw_brief[:280]}\n\n"
                "従来の手法では届けにくかったターゲット層へのアプローチと、"
                "ブランドの存在意義を明確に伝えるコミュニケーション設計が必要とされていた。"
            )
        else:
            brief = f"「{effective_title}」に関する課題を解決するため、新しいクリエイティブアプローチが求められていた。"

    # ── Insight ───────────────────────────────────────────────────────
    base_insight = INSIGHTS.get(
        detected_category,
        "ターゲットの日常に潜む本音を掘り起こすことで、感情を動かす切り口が生まれる。"
    )
    # user_memo > extra_context > body_text の優先順位
    context_for_insight = _pick_sentences(user_memo or extra_context or body_text, 150)
    if context_for_insight and len(context_for_insight) > 20:
        insight = f"{context_for_insight}。そこから導き出されたインサイトは、{base_insight}"
    else:
        insight = base_insight

    # ── Approach ──────────────────────────────────────────────────────
    approach = APPROACHES.get(
        detected_category,
        "ターゲットの本音を起点に、カテゴリの常識を逆手に取ったクリエイティブな切り口を設計する。"
    )

    # ── Solution ──────────────────────────────────────────────────────
    base_solution = SOLUTIONS.get(
        detected_category,
        "独自の視点でターゲットの心を動かすクリエイティブを実現した。"
    )
    execution_detail = _pick_sentences(user_memo or extra_context or body_text, 200)
    if execution_detail and len(execution_detail) > 40:
        solution = f"「{effective_title}」として展開。{execution_detail}"
    else:
        solution = f"「{effective_title}」を軸に施策を展開。{base_solution}"

    return {
        "category": detected_category,
        "industry": detected_industry,
        "brief": brief,
        "insight": insight,
        "approach": approach,
        "solution": solution,
    }

# ----------------------------------------------------------------
# Gemini AI（GEMINI_API_KEY 設定時に自動で使用）
# カテゴリ・業界も含めてJSONで返す
# ----------------------------------------------------------------
def gemini_analysis(
    title: str, body_text: str,
    category: str = "", industry: str = "", focus_title: str = "",
    extra_context: str = "", user_memo: str = ""
) -> dict:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    cats = "、".join(CATEGORIES)
    inds = "、".join(INDUSTRIES)

    hints = []
    if focus_title and focus_title.lower() not in title.lower():
        hints.append(
            f"【重要】このページには複数のコンテンツが含まれる可能性があります。"
            f"「{focus_title}」に関する情報のみを対象に分析してください。"
        )
    if category:
        hints.append(f"施策タイプは「{category}」を優先してください。")
    if industry:
        hints.append(f"業界は「{industry}」を優先してください。")
    hint_block = ("\n" + "\n".join(hints)) if hints else ""

    extra_block = f"\n\n【Web検索で収集した関連情報】\n{extra_context[:800]}" if extra_context else ""

    # user_memo がある場合は最優先インプットとして冒頭に置く
    memo_block = (
        f"\n\n【★最優先インプット：ユーザーの着眼点メモ★】\n{user_memo}\n"
        "↑ このメモはユーザーが「ここが凄い」と感じた核心です。"
        "このメモに書かれた観察・違和感・評価を起点に深掘りしてください。"
    ) if user_memo else ""

    prompt = (
        "あなたは電通・博報堂のトッププランナーです。広告・マーケティング施策を分析し、"
        "消費者インサイトからクリエイティブな切り口を導き出すのが専門です。\n\n"
        "URLから取得した情報と、ユーザーが記述した『ユーザーメモ（着眼点）』をガッチャンコして分析してください。\n"
        "ユーザーが『ここが良い』と感じたクリエイティブの裏側にある"
        "【真の課題】【ターゲットの未充足インサイト】【固定観念を覆す切り口】【具体的な解決策】を、"
        "プロの広告プランナーの視点で150文字以上でロジカルに深掘り・言語化してください。"
        "一般的な要約や薄い一般論で片付ける記述は厳禁とします。\n\n"
        f"ページタイトル: {title}\n"
        f"分析対象: {focus_title or title}\n"
        f"ページ内容: {body_text[:1000]}"
        f"{memo_block}"
        f"{extra_block}"
        f"{hint_block}\n\n"
        f"施策タイプの選択肢: {cats}\n"
        f"業界の選択肢: {inds}\n\n"
        "必ず次のJSONのみを返してください（コードブロック・説明文は不要）:\n"
        '{"category": "施策タイプ（選択肢から1つ）", '
        '"industry": "業界（選択肢から1つ）", '
        '"brief": "どんな市場・競合・顧客課題があったか？（150字以上・施策固有の背景。なぜその課題が重要だったかを含める）", '
        '"insight": "ターゲットのどんな本音・行動心理を発見したか？（150字以上・表面的なニーズではなく、潜在的な欲求や矛盾・固定観念を掘り下げる）", '
        '"approach": "そのインサイトをどんな切り口・コアアイデアで解決に導いたか？（100字以上・カテゴリーの常識を逆手に取る発想や逆説的アングルを必ず含める）", '
        '"solution": "具体的に何を作り、どう届けたか？（150字以上・媒体・フォーマット・体験設計の具体的な実行内容）", '
        '"user_memo": "広告プランナー視点での「ここが凄い！」ポイント（この施策の独自性・発想の転換・意外な切り口を中心に2〜3文で。一般論ではなくこの事例固有の面白さを具体的に）"}'
    )
    response = model.generate_content(prompt)
    result = extract_json(response.text)
    if result:
        return result
    return {"category": "", "industry": "", "brief": "", "insight": "", "approach": "", "solution": ""}

# ----------------------------------------------------------------
# システムプロンプト（マーケティングプランナー役割 + Few-Shot）
# ----------------------------------------------------------------
_ANALYSIS_SYSTEM_PROMPT = """\
# 役割
あなたは一流のマーケティングプランナー、およびUXリサーチャーです。
提出された記事（テキストや画像）を深く分析し、単なる表面的な事実の要約ではなく、その裏にある「消費者の心理変容」や「ビジネス・UX設計における革新性（構造）」を抽出してください。

# 出力フォーマットと抽出ルール

## Brief（課題設定）
単に「情報が多い」だけでなく、それが消費者にどんなストレス（心理的負荷、真贋判定の疲弊）を与えているか、時代のパラダイムシフト（例：コスパ→タイパ→メンパへの進化）を踏まえて構造的に記述してください。

## Insight（発見・消費者の本音）
消費者が自覚している表面的なニーズではなく、深層心理（本音）を言語化してください。
（例：自分で選ぶ自由よりも、考えなくていい安心の方が価値が高いなど、一見矛盾するようなインサイト）

## Approach（切り口・コアアイデア）
従来の常識（UXの通説など）をどう近現代の視点で逆転・再定義したかを記述してください。
単なる「サービス提供」ではなく、「●●から▲▲への価値訴求軸のシフト」という抽象度で捉えてください。

## Solution（解決策・アイデア）
事例の具体的な仕組み（機能、実績数値など）を記述し、それがどのように上記のアプローチを具現化しているかを紐付けて説明してください。

# 思考のガイドライン（重要）
- 「事実の箇条書き」は禁止します。
- 文脈同士をロジカルに繋ぎ、「つまりどういうことか？」を1段上の視点（抽象化）で言語化してください。
- 記事内で語られている具体的な数値（例：累計300万食、26年1月など）はSolutionやBriefの文脈を補強するエビデンスとして適切に配置してください。

# 出力例（Few-Shot）
以下は理想的な出力の質と抽象度です。この水準を維持してください。

【Brief例】
AI（人工知能）の普及により情報量が爆増し、真偽不明の情報も増えた結果、生活者は常に「選択の負荷（最適解を選ばなければならないプレッシャー）」と「真贋判定の負荷」にさらされるようになった。さらにSNS上でちょっとした感想を漏らすだけで周囲から〝正しさ〟の指摘が来る環境が、心をじわじわと疲弊させている。コスパ（コストパフォーマンス）→タイパ（タイムパフォーマンス）と続いてきた消費最適化の流れは2026年、「自分の意思決定コストそのものを削減したい」という第3ステージ＝メンタルパフォーマンス（メンパ）へと進化。各企業は「ユーザーが選ばなくて済む」体験設計への刷新を迫られている。

【Insight例】
デリOisixのβ版開始から約1年・累計300万食突破という数字が象徴するのは、消費者がもはや「何を食べるか」を自分で決めること自体に疲弊しているという事実だ。「自分で選ぶ自由」より「考えなくていい安心」の方が価値が高い時代に突入した。ぐるなびがAIに店選びを委ねるUMAMEを作り、Voicetepが顔写真・テキストプロフィールなしで音声通話からマッチングを始めたのも同じ構造——判断材料が増えれば増えるほど「失敗したくない・正解がわからない」不安が高まるというパラドックスを突いた設計だ。

【Approach例】
「選択肢を減らす＝ユーザーの自由を奪う」という従来のUX常識を根底から逆転させ、「選ばせないこと＝最高の体験」として再定義する。AIを「答えを探す補助ツール」ではなく「意思決定を丸ごと代行する代理人」として位置付けることで、サービスの価値訴求軸を「便利さ」から「メンタルの解放」へシフトさせる戦略。

【Solution例】
【デリOisix】顧客が注文品目と配送頻度を登録するとAIが自動でカートに商品を入れる「ゼロ選択」モデルを構築。電子レンジで温めるだけの調理済み2〜3人分主菜＋副菜を冷蔵配送し、β版開始から約1年で累計300万食超を達成。【UMAME（ぐるなび）】希望を一文で入力するだけでAIが最適な店を絞り込み、2026年1月20日に正式版リリース。【Voicetep】顔写真・テキストプロフィール不要でまず音声通話からマッチングを開始するUI設計で「断られる恐怖」を設計から排除。
"""

_JSON_SPEC = (
    '{"category":"施策タイプ（選択肢から1つ）","industry":"業界（選択肢から1つ）","title":"施策タイトル",'
    '"brief":"課題設定（200字以上・パラダイムシフトを含む構造的記述）",'
    '"insight":"消費者の本音（200字以上・深層心理・矛盾するインサイト）",'
    '"approach":"切り口（150字以上・価値訴求軸のシフトを●●から▲▲へという形で）",'
    '"solution":"解決策（200字以上・具体的仕組みと数値をApproachと紐付けて）",'
    '"user_memo":"広告プランナー視点での「ここが凄い！」ポイント（この事例固有の発想転換を2〜3文で）"}'
)

# ----------------------------------------------------------------
# AI バックエンド（Anthropic Claude / Groq Llama）
# ----------------------------------------------------------------
def _claude_request(prompt: str, system: str, images: list = None) -> dict:
    """Anthropic Claude API（ANTHROPIC_API_KEY設定時）"""
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    content = []
    if images:
        for img_bytes, mime_type in images:
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            content.append({"type": "image", "source": {"type": "base64", "media_type": mime_type, "data": b64}})
    content.append({"type": "text", "text": prompt})
    kwargs = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 2048,
        "temperature": 0.55,
        "messages": [{"role": "user", "content": content}],
    }
    if system:
        kwargs["system"] = system
    r = client.messages.create(**kwargs)
    return extract_json(r.content[0].text) or {}

def _groq_request(prompt: str, system: str, images: list = None) -> dict:
    """Groq API（GROQ_API_KEY設定時）"""
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    if images:
        content = []
        for img_bytes, mime_type in images:
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            content.append({"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64}"}})
        content.append({"type": "text", "text": prompt})
        model = "meta-llama/llama-4-scout-17b-16e-instruct"
    else:
        content = prompt
        model = "llama-3.3-70b-versatile"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": content})
    r = client.chat.completions.create(model=model, messages=messages, temperature=0.55)
    return extract_json(r.choices[0].message.content) or {}

def _ai_request(prompt: str, system: str = "", images: list = None) -> dict:
    """アクティブなAIバックエンドへのルーター"""
    if USE_ANTHROPIC:
        return _claude_request(prompt, system, images)
    elif USE_GROQ:
        return _groq_request(prompt, system, images)
    return {}

# ----------------------------------------------------------------
# 分析関数（URL / 検索 / ファイル）
# ----------------------------------------------------------------
def _build_analysis_user_prompt(
    title: str, body_text: str,
    category: str = "", industry: str = "", focus_title: str = "",
    extra_context: str = "", user_memo: str = ""
) -> str:
    cats = "、".join(CATEGORIES)
    inds = "、".join(INDUSTRIES)
    hints = []
    if focus_title and focus_title.lower() not in title.lower():
        hints.append(f"【重要】「{focus_title}」に関する情報のみを対象に分析してください。")
    if category:
        hints.append(f"施策タイプは「{category}」を優先してください。")
    if industry:
        hints.append(f"業界は「{industry}」を優先してください。")
    hint_block = ("\n" + "\n".join(hints)) if hints else ""
    extra_block = f"\n\n【Web検索で収集した関連情報】\n{extra_context[:800]}" if extra_context else ""
    memo_block = (
        f"\n\n【★最優先インプット：ユーザーの着眼点メモ★】\n{user_memo}\n"
        "↑ このメモはユーザーが「ここが凄い」と感じた核心です。このメモを起点に深掘りしてください。"
    ) if user_memo else ""
    return (
        f"ページタイトル: {title}\n分析対象: {focus_title or title}\n"
        f"ページ内容:\n{body_text[:1200]}"
        f"{memo_block}{extra_block}{hint_block}\n\n"
        f"施策タイプの選択肢: {cats}\n業界の選択肢: {inds}\n\n"
        f"必ず次のJSONのみを返してください（コードブロック・説明文は不要）:\n{_JSON_SPEC}"
    )

def groq_analysis(title, body_text, category="", industry="", focus_title="", extra_context="", user_memo="") -> dict:
    prompt = _build_analysis_user_prompt(title, body_text, category, industry, focus_title, extra_context, user_memo)
    return _ai_request(prompt, _ANALYSIS_SYSTEM_PROMPT)

def groq_analysis_from_search(keywords: list, combined_text: str, category: str, user_memo: str = "") -> dict:
    cats = "、".join(CATEGORIES)
    inds = "、".join(INDUSTRIES)
    cat_hint = f"\n施策タイプは「{category}」を優先してください。" if category else ""
    memo_block = (
        f"\n\n【★最優先インプット：ユーザーの着眼点メモ★】\n{user_memo}\n"
        "↑ このメモを起点に深掘りしてください。"
    ) if user_memo else ""
    prompt = (
        f"検索キーワード: {'、'.join(keywords)}\n\n検索結果:\n{combined_text[:1400]}"
        f"{memo_block}{cat_hint}\n\n"
        f"施策タイプの選択肢: {cats}\n業界の選択肢: {inds}\n\n"
        f"必ず次のJSONのみを返してください（コードブロック不要）:\n{_JSON_SPEC}"
    )
    return _ai_request(prompt, _ANALYSIS_SYSTEM_PROMPT)

def groq_analysis_from_files(file_data: list, category="", title="", user_memo="", keywords_str="") -> dict:
    cats = "、".join(CATEGORIES)
    inds = "、".join(INDUSTRIES)
    cat_hint = f"\n施策タイプは「{category}」を優先してください。" if category else ""
    kw_hint = f"\n関連キーワード: {keywords_str}" if keywords_str else ""
    memo_block = (
        f"\n\n【★最優先インプット：ユーザーの着眼点メモ★】\n{user_memo}\n"
        "↑ このメモを起点に深掘りしてください。"
    ) if user_memo else ""
    title_hint = title or "（ファイルから読み取ってください）"
    prompt = (
        f"添付の{len(file_data)}点のファイルを読み込み、マーケティング施策・広告事例を分析してください。\n"
        f"分析対象タイトル: {title_hint}{kw_hint}{memo_block}{cat_hint}\n\n"
        f"施策タイプの選択肢: {cats}\n業界の選択肢: {inds}\n\n"
        f"必ず次のJSONのみを返してください（コードブロック不要）:\n{_JSON_SPEC}"
    )
    images = [(b, m) for b, m, _ in file_data if m.startswith("image/")]
    if images:
        return _ai_request(prompt, _ANALYSIS_SYSTEM_PROMPT, images)
    body_text = ""
    for b, m, _ in file_data:
        if m == "application/pdf":
            body_text = extract_pdf_text(b)
            break
    return _ai_request(prompt + f"\n\nPDFテキスト:\n{body_text[:2000]}", _ANALYSIS_SYSTEM_PROMPT)

# ----------------------------------------------------------------
# エンドポイント（static mount より先に定義すること）
# ----------------------------------------------------------------
async def _web_context(query: str, max_results: int = 6, keywords: list = None) -> tuple:
    """DDGでqueryを検索し、(スニペットテキスト, 参照URLリスト) を返す。
    keywords が指定された場合はクエリに追加して精度を上げる。"""
    if not query:
        return "", []
    kw_suffix = (" " + " ".join(keywords)) if keywords else ""
    try:
        def _search():
            with DDGS() as ddgs:
                return list(ddgs.text(
                    query + kw_suffix + " マーケティング 施策 ブランド",
                    max_results=max_results,
                ))
        results = await asyncio.to_thread(_search)
        snippets = []
        refs = []
        for r in results:
            body = (r.get("body") or "").strip()
            if not body or len(body) < 30:
                continue
            snippets.append(f"【{r['title']}】\n{body}")
            refs.append({"title": r["title"], "url": r.get("href", ""), "snippet": body[:120]})
        return "\n\n".join(snippets[:4]), refs[:4]
    except Exception:
        return "", []

@app.post("/api/analyze-url")
async def analyze_url(req: AnalyzeRequest):
    try:
        scraped = await asyncio.to_thread(scrape_url, req.url)
        focus = req.title or scraped["title"]

        # 施策タイトルでWeb検索して追加コンテキストを取得（常に実行）
        extra_context, references = await _web_context(
            f"{focus} 広告 マーケティング 施策 事例", max_results=5,
            keywords=req.keywords or [],
        )

        if USE_GEMINI:
            analysis = await asyncio.to_thread(
                gemini_analysis,
                scraped["title"], scraped["body_text"],
                req.category, "", req.title, extra_context, req.user_memo,
            )
        elif USE_AI:
            analysis = await asyncio.to_thread(
                groq_analysis,
                scraped["title"], scraped["body_text"],
                req.category, "", req.title, extra_context, req.user_memo,
            )
        else:
            analysis = mock_analysis(
                scraped["title"], scraped["description"], scraped["body_text"],
                category=req.category, focus_title=req.title,
                extra_context=extra_context, user_memo=req.user_memo,
            )
        return {
            "success": True,
            "title": scraped["title"],
            "thumbnail": scraped["thumbnail"],
            "references": references,
            **analysis,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

async def _analyze_one_item(item: BatchAnalyzeItem) -> dict:
    """1件のバッチアイテムを処理する（scrape → DDG補填 → AI分析）。"""
    try:
        # ── Step 1: URLスクレイピング（スレッドで実行してイベントループをブロックしない）
        scraped = {
            "title": item.title or "",
            "description": "",
            "thumbnail": "",
            "body_text": "",
        }
        try:
            scraped = await asyncio.to_thread(scrape_url, item.url)
        except Exception:
            pass  # 失敗してもStep2で補填

        # ── Step 2: DDG検索で補填 or 追加コンテキスト取得 ──────────────
        query = item.title or scraped.get("title", "")
        body_ok = len(scraped.get("body_text", "")) > 150
        desc_ok = len(scraped.get("description", "")) > 50
        extra_context = ""
        kw_suffix = (" " + " ".join(item.keywords)) if item.keywords else ""
        if query:
            try:
                def _ddg_search():
                    with DDGS() as ddgs:
                        return list(ddgs.text(
                            f"{query}{kw_suffix} マーケティング 施策 ブランド",
                            max_results=5,
                        ))
                sr = await asyncio.to_thread(_ddg_search)
                extra_context = "\n\n".join(
                    f"【{r['title']}】\n{r['body']}" for r in sr[:4] if r.get("body")
                )
                # コンテンツが薄い場合はスクレイプ本文も補填
                if not (body_ok or desc_ok):
                    supplement = "\n\n".join(
                        f"【{r['title']}】\n{r['body']}" for r in sr[:4]
                    )
                    scraped["body_text"] = (scraped["body_text"] + "\n\n" + supplement).strip()
                    if not scraped["description"] and sr:
                        scraped["description"] = sr[0]["body"]
                    if not scraped["thumbnail"]:
                        for r in sr[:3]:
                            try:
                                s2 = await asyncio.to_thread(scrape_url, r["href"])
                                if s2.get("thumbnail"):
                                    scraped["thumbnail"] = s2["thumbnail"]
                                    break
                            except Exception:
                                pass
            except Exception:
                pass  # DDGも失敗した場合はタイトルだけで分析

        # ── Step 3: AI分析 ──────────────────────────────────────────────
        if USE_GEMINI:
            analysis = await asyncio.to_thread(
                gemini_analysis,
                scraped.get("title") or item.title,
                scraped["body_text"],
                "", "", item.title, extra_context, item.user_memo,
            )
        elif USE_AI:
            analysis = await asyncio.to_thread(
                groq_analysis,
                scraped.get("title") or item.title,
                scraped["body_text"],
                "", "", item.title, extra_context, item.user_memo,
            )
        else:
            analysis = mock_analysis(
                scraped.get("title") or item.title,
                scraped.get("description", ""),
                scraped["body_text"],
                focus_title=item.title,
                extra_context=extra_context,
                user_memo=item.user_memo,
            )

        return {
            "success": True,
            "submitter": item.submitter,
            "title": item.title or scraped.get("title", ""),
            "url": item.url,
            "thumbnail": scraped.get("thumbnail", ""),
            **analysis,
        }

    except Exception as e:
        try:
            fallback = mock_analysis(item.title, "", "", focus_title=item.title)
            return {
                "success": True,
                "submitter": item.submitter,
                "title": item.title,
                "url": item.url,
                "thumbnail": "",
                **fallback,
            }
        except Exception:
            return {
                "success": False,
                "submitter": item.submitter,
                "title": item.title,
                "url": item.url,
                "error": str(e),
                "category": "", "industry": "",
                "brief": "", "insight": "", "approach": "", "solution": "",
                "userMemo": item.user_memo,
                "thumbnail": "",
            }

@app.post("/api/batch-analyze")
async def batch_analyze(req: BatchAnalyzeRequest):
    """
    スプレッドシートからのバッチインポート用。
    1. URLスクレイピング → 2. 内容不足時はDDG検索で補填 → 3. AI分析
    同一URLに複数コンテンツがある場合は title をヒントに抽出。
    全アイテムを並行処理する。
    """
    results = await asyncio.gather(*[_analyze_one_item(item) for item in req.items])
    return {"results": list(results)}

@app.get("/api/status")
async def status():
    mode = "claude" if USE_ANTHROPIC else ("gemini" if USE_GEMINI else ("groq" if USE_GROQ else "mock"))
    return {"mode": mode, "ready": True}

# ----------------------------------------------------------------
# キーワード検索エンドポイント
# ----------------------------------------------------------------
def mock_analysis_from_search(keywords: list, combined_text: str, category: str, user_memo: str = "") -> dict:
    keyword_str = "・".join(keywords)
    clean_ctx = _clean_text(combined_text) if combined_text else ""
    # user_memo を最優先素材として先頭に結合
    primary_text = f"{user_memo} {clean_ctx}" if user_memo else clean_ctx
    search_text = f"{keyword_str} {primary_text[:600]}"
    detected_category = category or detect_category(search_text)
    detected_industry = detect_industry(search_text)

    # Brief: user_memo 優先、なければ検索結果から抽出
    if user_memo and len(user_memo) > 30:
        brief = (
            f"「{keyword_str}」について、着眼点として次の点が挙げられた：{user_memo[:280]}。\n\n"
            "この視点を起点に、ターゲット層への効果的なアプローチが求められていた。"
        )
    else:
        rich_snippet = _pick_sentences(clean_ctx, 280) if clean_ctx else ""
        if rich_snippet:
            brief = (
                f"「{keyword_str}」に関する背景として、{rich_snippet}。\n\n"
                "この状況において、ターゲット層への効果的なアプローチが求められていた。"
            )
        else:
            brief = f"「{keyword_str}」に関するマーケティング課題に対して、新しいクリエイティブアプローチが求められていた。"

    # Insight: user_memo > 検索結果の優先順位
    base_insight = INSIGHTS.get(detected_category, "ターゲットの日常に潜む本音を掘り起こすことで、感情を動かす切り口が生まれる。")
    insight_hint = _pick_sentences(user_memo or clean_ctx, 150) if (user_memo or clean_ctx) else ""
    if insight_hint and len(insight_hint) > 30:
        insight = f"{insight_hint}。\n\n{base_insight}"
    else:
        insight = base_insight

    # Approach
    approach = APPROACHES.get(
        detected_category,
        "ターゲットの本音を起点に、カテゴリの常識を逆手に取ったクリエイティブな切り口を設計する。"
    )

    # Solution: user_memo > 検索結果
    base_solution = SOLUTIONS.get(detected_category, "独自の視点でターゲットの心を動かすクリエイティブを実現した。")
    exec_detail = _pick_sentences(user_memo or clean_ctx, 200) if (user_memo or clean_ctx) else ""
    if exec_detail and len(exec_detail) > 40:
        solution = f"「{keyword_str}」として展開。{exec_detail}"
    else:
        solution = f"「{keyword_str}」を活用した施策を展開。{base_solution}"

    return {"category": detected_category, "industry": detected_industry, "brief": brief, "insight": insight, "approach": approach, "solution": solution}

def gemini_analysis_from_search(keywords: list, combined_text: str, category: str, user_memo: str = "") -> dict:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    keyword_str = "、".join(keywords)
    cats = "、".join(CATEGORIES)
    inds = "、".join(INDUSTRIES)
    category_hint = f"\n施策タイプは「{category}」を優先してください。" if category else ""

    memo_block = (
        f"\n\n【★最優先インプット：ユーザーの着眼点メモ★】\n{user_memo}\n"
        "↑ このメモはユーザーが「ここが凄い」と感じた核心です。このメモを起点に深掘りしてください。"
    ) if user_memo else ""

    prompt = (
        "あなたは電通・博報堂のトッププランナーです。広告・マーケティング施策を分析し、"
        "消費者インサイトからクリエイティブな切り口を導き出すのが専門です。\n\n"
        "Web検索結果と、ユーザーが記述した『ユーザーメモ（着眼点）』をガッチャンコして分析してください。\n"
        "ユーザーが『ここが良い』と感じたクリエイティブの裏側にある"
        "【真の課題】【ターゲットの未充足インサイト】【固定観念を覆す切り口】【具体的な解決策】を、"
        "プロの広告プランナーの視点で150文字以上でロジカルに深掘り・言語化してください。"
        "一般的な要約や薄い一般論で片付ける記述は厳禁とします。\n\n"
        f"検索キーワード: {keyword_str}\n"
        f"検索結果:\n{combined_text[:1200]}"
        f"{memo_block}"
        f"{category_hint}\n\n"
        f"施策タイプの選択肢: {cats}\n"
        f"業界の選択肢: {inds}\n\n"
        "必ず次のJSONのみを返してください（コードブロック不要）:\n"
        '{"category": "施策タイプ（選択肢から1つ）", '
        '"industry": "業界（選択肢から1つ）", '
        '"brief": "どんな市場・競合・顧客課題があったか？（150字以上・なぜその課題が重要だったかを含める）", '
        '"insight": "ターゲットのどんな本音・行動心理を発見したか？（150字以上・潜在的な欲求や矛盾・固定観念を掘り下げる）", '
        '"approach": "そのインサイトをどんな切り口・コアアイデアで解決に導いたか？（100字以上・カテゴリーの常識を逆手に取る発想を必ず含める）", '
        '"solution": "具体的に何を作り、どう届けたか？（150字以上・媒体・フォーマット・体験設計の具体的な実行内容）", '
        '"user_memo": "広告プランナー視点での「ここが凄い！」ポイント（この施策の独自性・発想の転換・意外な切り口を中心に2〜3文で。一般論ではなくこの事例固有の面白さを具体的に）"}'
    )
    response = model.generate_content(prompt)
    result = extract_json(response.text)
    if result:
        return result
    return {"category": "", "industry": "", "brief": "", "insight": "", "approach": "", "solution": ""}

@app.post("/api/search-keywords")
async def search_keywords(req: SearchRequest):
    try:
        query = " ".join(req.keywords)
        if req.industry:
            query += f" {req.industry} 広告 キャンペーン"

        def _search():
            with DDGS() as ddgs:
                return list(ddgs.text(
                    query + " マーケティング 広告 施策",
                    max_results=6,
                ))
        results = await asyncio.to_thread(_search)

        articles = [
            {"title": r["title"], "url": r["href"], "snippet": r["body"]}
            for r in results if r.get("href")
        ]

        combined_text = "\n\n".join(
            [f"【{r['title']}】\n{r['body']}" for r in results[:4]]
        )

        if USE_GEMINI:
            analysis = await asyncio.to_thread(
                gemini_analysis_from_search, req.keywords, combined_text, req.category, req.user_memo
            )
        elif USE_AI:
            analysis = await asyncio.to_thread(
                groq_analysis_from_search, req.keywords, combined_text, req.category, req.user_memo
            )
        else:
            analysis = mock_analysis_from_search(req.keywords, combined_text, req.category, req.user_memo)

        thumbnail = ""
        primary_url = articles[0]["url"] if articles else ""
        if primary_url:
            try:
                scraped = await asyncio.to_thread(scrape_url, primary_url)
                thumbnail = scraped.get("thumbnail", "")
            except Exception:
                pass

        title = articles[0]["title"] if articles else " ".join(req.keywords)

        return {
            "success": True,
            "articles": articles[:5],
            "title": title,
            "url": primary_url,
            "thumbnail": thumbnail,
            **analysis,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ----------------------------------------------------------------
# ファイル解析（PDF / JPG / PNG）
# ----------------------------------------------------------------
def _get_file_mime(filename: str, content_type: str = "") -> str:
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    return {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
        'png': 'image/png',
        'webp': 'image/webp',
        'gif': 'image/gif',
    }.get(ext) or (content_type if content_type not in ('', 'application/octet-stream') else 'application/pdf')

def extract_pdf_text(pdf_bytes: bytes) -> str:
    """pypdfでテキストPDFから文字列を抽出（スキャン系は空になる）。"""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                pages.append(t.strip())
        return "\n\n".join(pages)[:4000]
    except Exception:
        return ""

def gemini_analysis_from_files(
    file_data: list,  # list of (bytes, mime_type, filename)
    category: str = "", title: str = "",
    user_memo: str = "", keywords_str: str = "",
) -> dict:
    """GeminiにPDF/画像を1枚以上渡してスキャン含め4項目を抽出する。"""
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    cats = "、".join(CATEGORIES)
    inds = "、".join(INDUSTRIES)
    cat_hint = f"\n施策タイプは「{category}」を優先してください。" if category else ""
    kw_hint  = f"\n関連キーワード: {keywords_str}" if keywords_str else ""
    memo_block = (
        f"\n\n【★最優先インプット：ユーザーの着眼点メモ★】\n{user_memo}\n"
        "↑ このメモを起点に深掘りしてください。"
    ) if user_memo else ""

    n = len(file_data)
    all_images = all(m.startswith("image/") for _, m, _ in file_data)
    if n == 1:
        _, mime_type, _ = file_data[0]
        file_desc = "画像（写真・スキャン等）" if mime_type.startswith("image/") else "PDF（雑誌スキャン等）"
    else:
        file_desc = f"{n}枚の画像" if all_images else f"{n}点のファイル（PDF/画像）"
    title_hint = title or f"（{file_desc}から読み取ってください）"

    prompt = (
        "あなたは電通・博報堂のトッププランナーです。\n"
        f"添付の{file_desc}を読み込み、掲載されているマーケティング施策・広告事例を分析してください。\n"
        "ユーザーが記述した着眼点メモをガッチャンコして、"
        "【真の課題】【ターゲットの未充足インサイト】【固定観念を覆す切り口】【具体的な解決策】を"
        "150文字以上でロジカルに深掘り・言語化してください。一般論は厳禁。\n"
        f"分析対象タイトル: {title_hint}"
        f"{kw_hint}{memo_block}{cat_hint}\n\n"
        f"施策タイプの選択肢: {cats}\n"
        f"業界の選択肢: {inds}\n\n"
        "必ず次のJSONのみを返してください（コードブロック不要）:\n"
        '{"category":"施策タイプ","industry":"業界","title":"施策タイトル（ファイル内から読み取る）",'
        '"brief":"真の課題（150字以上）","insight":"ターゲットの未充足インサイト（150字以上）",'
        '"approach":"固定観念を覆す切り口（100字以上）","solution":"具体的な解決策（150字以上）",'
        '"user_memo":"広告プランナー視点での「ここが凄い！」ポイント（この事例固有の独自性・発想の転換を2〜3文で）"}'
    )

    parts = [
        {"inline_data": {"mime_type": m, "data": base64.b64encode(b).decode("utf-8")}}
        for b, m, _ in file_data
    ]
    parts.append(prompt)

    response = model.generate_content(parts)
    result = extract_json(response.text)
    if result:
        return result
    return {"category": "", "industry": "", "title": "", "brief": "", "insight": "", "approach": "", "solution": ""}

@app.post("/api/analyze-pdf")
async def analyze_pdf_endpoint(
    files: list[UploadFile] = File(...),
    category: str = Form(""),
    title: str = Form(""),
    keywords: str = Form(""),
    user_memo: str = Form(""),
):
    try:
        file_data = []
        for f in files:
            content = await f.read()
            mime_type = _get_file_mime(f.filename or "", f.content_type or "")
            file_data.append((content, mime_type, f.filename or "uploaded"))

        if not file_data:
            return {"success": False, "error": "ファイルが選択されていません"}

        first_filename = file_data[0][2]

        if USE_GEMINI:
            analysis = await asyncio.to_thread(
                gemini_analysis_from_files, file_data, category, title, user_memo, keywords
            )
        elif USE_AI:
            analysis = await asyncio.to_thread(
                groq_analysis_from_files, file_data, category, title, user_memo, keywords
            )
        else:
            # モックモード: 最初のPDFからテキスト抽出（画像は空テキスト）
            body_text = ""
            for content, mime_type, _ in file_data:
                if mime_type == "application/pdf":
                    body_text = await asyncio.to_thread(extract_pdf_text, content)
                    break
            analysis = mock_analysis(
                title or first_filename, "", body_text,
                category=category, focus_title=title,
                user_memo=user_memo,
            )

        extracted_title = analysis.pop("title", "") or title or first_filename

        return {
            "success": True,
            "title": extracted_title,
            "filename": first_filename,
            "thumbnail": "",
            **analysis,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# static files はローカル開発時のみマウント（Vercel では静的配信をVercel側が担当）
if not os.environ.get("VERCEL"):
    app.mount("/", StaticFiles(directory=str(BASE_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
