# Naver Review Reply Bot Prototype

네이버 스마트스토어 상품 리뷰 답변 봇의 테스트용 프로토타입입니다.

대상 상품:

https://smartstore.naver.com/ppbb/products/3478201617

현재 버전은 실제 스마트스토어 리뷰를 읽고, 답변은 등록하지 않은 채 콘솔에만 출력합니다.

## Docker 실행

Docker는 브라우저 로그인 세션을 보기 어렵기 때문에 현재는 로컬 Playwright 실행을 권장합니다.

직접 리뷰를 넣어 테스트:

```bash
docker compose run --rm review-reply-bot python -m app.main \
  --author "테스트고객" \
  --rating 5 \
  --review "배송 빠르고 상품도 만족합니다."
```

## 로컬 Playwright 수집 실행

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
python -m app.main
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python -m app.main
```

처음 실행하거나 로그인이 풀렸다면 브라우저에서 직접 로그인한 뒤 계속 진행합니다.

```bash
python -m app.main --pause-for-login
```

로그인 쿠키는 기본적으로 `.playwright-profile`에 저장됩니다. 다음 실행부터는 같은 프로필을 재사용합니다.

다른 상품 URL을 열려면:

```bash
python -m app.main --url "https://smartstore.naver.com/ppbb/products/3478201617" --limit 5
```

샘플 리뷰로 답변 생성만 테스트하려면:

```bash
python -m app.main --sample
```

## 다음 단계

- 스마트스토어 DOM 구조에 맞춘 리뷰 selector 보강
- 리뷰 작성자, 평점, 옵션 정보 분리 수집
- OpenAI 등 LLM 기반 답변 생성기 연결
- 관리자 검토 후 답변 등록하는 승인 플로우 추가
