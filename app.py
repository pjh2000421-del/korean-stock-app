"""
한국 주식 대시보드 - Flask 백엔드
Yahoo Finance (yfinance) 를 사용하여 주가 데이터를 제공합니다.
"""

from flask import Flask, render_template, jsonify, request
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# ──────────────────────────────────────────────
# 유틸리티 함수
# ──────────────────────────────────────────────

def format_number(value, suffix=""):
    """숫자를 읽기 쉬운 형식으로 변환 (예: 1,234,567 → 1.23M)"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "N/A"
    try:
        value = float(value)
        if abs(value) >= 1_000_000_000_000:
            return f"{value / 1_000_000_000_000:.2f}조{suffix}"
        elif abs(value) >= 100_000_000:
            return f"{value / 100_000_000:.2f}억{suffix}"
        elif abs(value) >= 10_000:
            return f"{value / 10_000:.2f}만{suffix}"
        else:
            return f"{value:,.0f}{suffix}"
    except (TypeError, ValueError):
        return "N/A"


def safe_get(info: dict, key: str, default=None):
    """딕셔너리에서 안전하게 값을 가져옵니다."""
    val = info.get(key, default)
    if isinstance(val, float) and pd.isna(val):
        return default
    return val


# ──────────────────────────────────────────────
# API 라우트
# ──────────────────────────────────────────────

@app.route("/")
def index():
    """메인 페이지를 렌더링합니다."""
    return render_template("index.html")


@app.route("/api/stock/<ticker>")
def get_stock_data(ticker: str):
    """
    주어진 티커의 주가 데이터와 재무지표를 반환합니다.

    Args:
        ticker: Yahoo Finance 형식의 티커 (예: 005930.KS)

    Returns:
        JSON: 주가 차트 데이터, 거래량 데이터, 재무지표
    """
    ticker = ticker.upper().strip()
    logger.info(f"데이터 요청: {ticker}")

    try:
        stock = yf.Ticker(ticker)

        # ── 1. 최근 1년 주가 데이터 가져오기 ──
        end_date = datetime.today()
        start_date = end_date - timedelta(days=365)
        hist = stock.history(start=start_date, end=end_date)

        # 데이터가 없으면 잘못된 티커로 판단
        if hist.empty:
            return jsonify({"error": f"'{ticker}' 에 해당하는 데이터를 찾을 수 없습니다. 티커를 확인해주세요."}), 404

        # 날짜를 문자열로 변환 (JSON 직렬화 가능하도록)
        hist.index = hist.index.strftime("%Y-%m-%d")

        # ── 2. 주가 차트 데이터 구성 ──
        price_data = {
            "dates":  hist.index.tolist(),
            "open":   [round(v, 2) for v in hist["Open"].tolist()],
            "close":  [round(v, 2) for v in hist["Close"].tolist()],
            "high":   [round(v, 2) for v in hist["High"].tolist()],
            "low":    [round(v, 2) for v in hist["Low"].tolist()],
        }

        # ── 3. 거래량 데이터 구성 ──
        volume_data = {
            "dates":   hist.index.tolist(),
            "volumes": hist["Volume"].tolist(),
        }

        # ── 4. 기업 정보 및 재무지표 가져오기 ──
        info = stock.info

        # 현재가 계산 (fast_info 우선, 없으면 history 마지막 값)
        try:
            current_price = stock.fast_info.last_price
        except Exception:
            current_price = hist["Close"].iloc[-1] if not hist.empty else None

        # 전일 종가 (52주 고가/저가 계산용)
        prev_close = safe_get(info, "previousClose") or (
            hist["Close"].iloc[-2] if len(hist) > 1 else None
        )

        # 가격 변동 계산
        price_change = None
        price_change_pct = None
        if current_price and prev_close:
            price_change = round(current_price - prev_close, 2)
            price_change_pct = round((price_change / prev_close) * 100, 2)

        # 재무지표 딕셔너리 구성
        financials = {
            "company_name":      safe_get(info, "longName") or safe_get(info, "shortName") or ticker,
            "current_price":     format_number(current_price, "원") if current_price else "N/A",
            "price_change":      f"{price_change:+,.0f}원" if price_change is not None else "N/A",
            "price_change_pct":  f"{price_change_pct:+.2f}%" if price_change_pct is not None else "N/A",
            "is_positive":       (price_change >= 0) if price_change is not None else None,
            "market_cap":        format_number(safe_get(info, "marketCap")),
            "per":               f"{safe_get(info, 'trailingPE'):.2f}" if safe_get(info, "trailingPE") else "N/A",
            "pbr":               f"{safe_get(info, 'priceToBook'):.2f}" if safe_get(info, "priceToBook") else "N/A",
            "eps":               format_number(safe_get(info, "trailingEps"), "원"),
            "dividend_yield":    f"{safe_get(info, 'dividendYield', 0) * 100:.2f}%" if safe_get(info, "dividendYield") else "N/A",
            "52w_high":          format_number(safe_get(info, "fiftyTwoWeekHigh"), "원"),
            "52w_low":           format_number(safe_get(info, "fiftyTwoWeekLow"), "원"),
            "avg_volume":        format_number(safe_get(info, "averageVolume")),
            "sector":            safe_get(info, "sector") or "N/A",
            "industry":          safe_get(info, "industry") or "N/A",
            "currency":          safe_get(info, "currency") or "KRW",
        }

        return jsonify({
            "ticker":     ticker,
            "price_data": price_data,
            "volume_data": volume_data,
            "financials": financials,
        })

    except Exception as e:
        logger.error(f"오류 발생 [{ticker}]: {e}", exc_info=True)
        return jsonify({"error": f"데이터를 불러오는 중 오류가 발생했습니다: {str(e)}"}), 500


@app.route("/api/search")
def search_ticker():
    """
    티커 자동완성을 위한 간단한 검색 엔드포인트.
    인기 한국 주식 티커 목록을 반환합니다.
    """
    popular_stocks = [
        {"ticker": "005930.KS", "name": "삼성전자"},
        {"ticker": "000660.KS", "name": "SK하이닉스"},
        {"ticker": "035420.KS", "name": "NAVER"},
        {"ticker": "035720.KS", "name": "카카오"},
        {"ticker": "005380.KS", "name": "현대차"},
        {"ticker": "051910.KS", "name": "LG화학"},
        {"ticker": "006400.KS", "name": "삼성SDI"},
        {"ticker": "207940.KS", "name": "삼성바이오로직스"},
        {"ticker": "068270.KS", "name": "셀트리온"},
        {"ticker": "000270.KS", "name": "기아"},
        {"ticker": "105560.KS", "name": "KB금융"},
        {"ticker": "055550.KS", "name": "신한지주"},
        {"ticker": "028260.KS", "name": "삼성물산"},
        {"ticker": "012330.KS", "name": "현대모비스"},
        {"ticker": "066570.KS", "name": "LG전자"},
    ]
    query = request.args.get("q", "").lower()
    if query:
        popular_stocks = [
            s for s in popular_stocks
            if query in s["ticker"].lower() or query in s["name"].lower()
        ]
    return jsonify(popular_stocks)


# ──────────────────────────────────────────────
# 앱 실행
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  한국 주식 대시보드 서버 시작")
    print("  http://127.0.0.1:5000 으로 접속하세요")
    print("=" * 50)
    app.run(debug=False, host="0.0.0.0", port=5000)
