"""
CREATIVE DEPOT - Backend API Server

起動方法:
  pip install -r requirements.txt
  python server.py

Gemini AI（無料枠）に切り替える場合:
  GEMINI_API_KEY=your_key python server.py
  ※ https://aistudio.google.com/app/apikey で無料取得可能
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import os, json, re
from pathlib import Path
from duckduckgo_search import DDGS

# ----------------------------------------------------------------
# 設定: GEMINI_API_KEY 環境変数を設定すると本物のAIに切り替わります
# ----------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
USE_GEMINI = bool(GEMINI_API_KEY)

BASE_DIR = Path(__file__).parent

app = FastAPI(title="CREATIVE DEPOT API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------
# Models
# ----------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    url: str
    category: str = ""

class SearchRequest(BaseModel):
    keywords: list[str]
    category: str = ""
    industry: str = ""

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
# モックAI（APIキーなしで動作）
# ----------------------------------------------------------------
def mock_analysis(title: str, description: str, body_text: str, category: str) -> dict:
    content = description or body_text[:250]
    brief = (
        f"{content[:220]}\n\n"
        "従来の手法では届けられなかったターゲット層への訴求を強化し、"
        "ブランドの存在意義を明確に伝えるアプローチが求められていた。"
        if content
        else f"「{title}」に関する課題を解決するため、新しいクリエイティブアプローチが必要とされていた。"
    )
    insight = INSIGHTS.get(category, "ターゲットの日常に潜む本音を掘り起こすことで、感情を動かす切り口が生まれる。")
    solution = f"「{title}」を軸に施策を展開。" + SOLUTIONS.get(category, "独自の視点でターゲットの心を動かすクリエイティブを実現した。")
    return {"brief": brief, "insight": insight, "solution": solution}

# ----------------------------------------------------------------
# Gemini AI（GEMINI_API_KEY 設定時に自動で使用）
# ----------------------------------------------------------------
def gemini_analysis(title: str, body_text: str, category: str) -> dict:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = (
        "あなたは広告・マーケティング戦略の専門家です。\n"
        "以下の記事を読み、Brief / Insight / Solution フレームワークで分析してください。\n\n"
        f"タイトル: {title}\n"
        f"カテゴリ: {category or 'その他'}\n"
        f"記事内容: {body_text[:1200]}\n\n"
        "必ず次のJSONのみを返してください（コードブロック・説明文は不要）:\n"
        '{"brief": "どんな課題に対して？（3文以内）", '
        '"insight": "どんな切り口で？（3文以内）", '
        '"solution": "どう解決したか？（3〜4文）"}'
    )
    response = model.generate_content(prompt)
    match = re.search(r'\{[^{}]+\}', response.text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return {"brief": "", "insight": "", "solution": ""}

# ----------------------------------------------------------------
# エンドポイント（static mount より先に定義すること）
# ----------------------------------------------------------------
@app.post("/api/analyze-url")
async def analyze_url(req: AnalyzeRequest):
    try:
        scraped = scrape_url(req.url)
        if USE_GEMINI:
            analysis = gemini_analysis(scraped["title"], scraped["body_text"], req.category)
        else:
            analysis = mock_analysis(
                scraped["title"], scraped["description"], scraped["body_text"], req.category
            )
        return {
            "success": True,
            "title": scraped["title"],
            "thumbnail": scraped["thumbnail"],
            **analysis,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/status")
async def status():
    return {"mode": "gemini" if USE_GEMINI else "mock", "ready": True}

# ----------------------------------------------------------------
# キーワード検索エンドポイント
# ----------------------------------------------------------------
def mock_analysis_from_search(keywords: list, combined_text: str, category: str) -> dict:
    keyword_str = "・".join(keywords)
    snippet = combined_text[:280] if combined_text else keyword_str
    brief = (
        f"「{keyword_str}」に関する最新動向として、{snippet[:250]}...\n\n"
        "この状況において、ターゲット層への効果的なアプローチが求められていた。"
    )
    insight = INSIGHTS.get(category, "ターゲットの日常に潜む本音を掘り起こすことで、感情を動かす切り口が生まれる。")
    solution = f"「{keyword_str}」を活用した施策を展開。" + SOLUTIONS.get(category, "独自の視点でターゲットの心を動かすクリエイティブを実現した。")
    return {"brief": brief, "insight": insight, "solution": solution}

def gemini_analysis_from_search(keywords: list, combined_text: str, category: str) -> dict:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    keyword_str = "、".join(keywords)
    prompt = (
        "あなたは広告・マーケティング戦略の専門家です。\n"
        "以下の検索結果をもとに、Brief / Insight / Solution で分析してください。\n\n"
        f"検索キーワード: {keyword_str}\n"
        f"カテゴリ: {category or 'その他'}\n"
        f"検索結果:\n{combined_text[:1500]}\n\n"
        "必ず次のJSONのみを返してください（コードブロック不要）:\n"
        '{"brief": "どんな課題に対して？（3文以内）", '
        '"insight": "どんな切り口で？（3文以内）", '
        '"solution": "どう解決したか？（3〜4文）"}'
    )
    response = model.generate_content(prompt)
    match = re.search(r'\{[^{}]+\}', response.text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return {"brief": "", "insight": "", "solution": ""}

@app.post("/api/search-keywords")
async def search_keywords(req: SearchRequest):
    try:
        query = " ".join(req.keywords)
        if req.industry:
            query += f" {req.industry} 広告 キャンペーン"

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=6, region="jp-jp"))

        articles = [
            {"title": r["title"], "url": r["href"], "snippet": r["body"]}
            for r in results if r.get("href")
        ]

        combined_text = "\n\n".join(
            [f"【{r['title']}】\n{r['body']}" for r in results[:4]]
        )

        if USE_GEMINI:
            analysis = gemini_analysis_from_search(req.keywords, combined_text, req.category)
        else:
            analysis = mock_analysis_from_search(req.keywords, combined_text, req.category)

        thumbnail = ""
        primary_url = articles[0]["url"] if articles else ""
        if primary_url:
            try:
                scraped = scrape_url(primary_url)
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

# static files はAPIルート定義後にマウント
app.mount("/", StaticFiles(directory=str(BASE_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
