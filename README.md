# Naver Review Reply Bot Prototype

네이버 스마트스토어 상품 리뷰 응대 봇의 테스트용 프로토타입입니다.

대상 상품:

https://smartstore.naver.com/ppbb/products/3478201617

현재 버전은 안전하게 콘솔 출력만 합니다. 실제 상품 페이지에 답변을 등록하지 않습니다.

## 실행

```bash
docker compose run --rm review-reply-bot
```

직접 리뷰를 넣어 테스트:

```bash
docker compose run --rm review-reply-bot python -m app.main \
  --author "테스트고객" \
  --rating 5 \
  --review "배송 빠르고 상품도 만족합니다"
```

로컬 Python 실행:

```bash
python -m app.main
```

## 다음 단계

- 실제 리뷰 수집 모듈 추가
- OpenAI 등 LLM 기반 답변 생성기 연결
- 답변 금칙어, 톤앤매너, CS 에스컬레이션 규칙 추가
- 관리자 검수 후 등록하는 승인 플로우 추가
