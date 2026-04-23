# 📈 한국 주식 대시보드

Yahoo Finance 데이터를 사용하는 Flask 기반 한국 주식 조회 웹앱입니다.

## 📁 프로젝트 구조

```
korean-stock-app/
├── app.py                  # Flask 백엔드 (API + 라우트)
├── requirements.txt        # Python 패키지 목록
├── README.md               # 이 파일
└── templates/
    └── index.html          # 프론트엔드 (HTML + CSS + JS)
```

## 🚀 실행 방법

### 1단계: Python 설치 확인 (3.9 이상 권장)
```bash
python --version
```

### 2단계: 가상환경 생성 및 활성화 (권장)
```bash
# 가상환경 생성
python -m venv venv

# 활성화 (Mac/Linux)
source venv/bin/activate

# 활성화 (Windows)
venv\Scripts\activate
```

### 3단계: 패키지 설치
```bash
pip install -r requirements.txt
```

### 4단계: 서버 실행
```bash
python app.py
```

### 5단계: 브라우저에서 접속
```
http://127.0.0.1:5000
```

## 🔍 사용법

- 입력창에 티커 코드 입력 후 **조회** 버튼 클릭
- 한국 주식: `005930.KS` 형식 (종목코드 + `.KS`)
- 상단 태그를 클릭하면 인기 종목 빠른 조회 가능

| 기업명      | 티커        |
|-------------|-------------|
| 삼성전자    | 005930.KS   |
| SK하이닉스  | 000660.KS   |
| NAVER       | 035420.KS   |
| 카카오      | 035720.KS   |
| 현대차      | 005380.KS   |

## 📊 표시 정보

- **주가 차트**: 최근 1년 시가 / 종가
- **거래량 차트**: 전일 대비 색상 구분 (초록/빨강)
- **재무지표**: 시가총액, PER, PBR, EPS, 배당수익률, 52주 고/저가

## 🔧 확장 아이디어

- 여러 종목 비교 기능 → `/api/compare?tickers=005930.KS,000660.KS`
- 기간 선택 (1개월 / 3개월 / 1년)
- 이동평균선 (MA5, MA20) 오버레이
- 관심 종목 북마크 (localStorage)
