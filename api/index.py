import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Vercel環境フラグを立てる（静的ファイルマウントをスキップ）
os.environ["VERCEL"] = "1"

from mangum import Mangum
from server import app  # noqa: E402

handler = Mangum(app, lifespan="off")
