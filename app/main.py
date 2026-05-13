from __future__ import annotations

import argparse

from app.reply_engine import ReplyEngine, Review, sample_reviews


PRODUCT_URL = "https://smartstore.naver.com/ppbb/products/3478201617"
STORE_NAME = "PPBB"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Naver SmartStore review reply bot prototype. Console output only."
    )
    parser.add_argument("--author", default="테스트고객", help="리뷰 작성자 표시명")
    parser.add_argument("--rating", type=int, choices=range(1, 6), help="1-5점 리뷰 평점")
    parser.add_argument("--review", help="응대 테스트에 사용할 리뷰 본문")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    engine = ReplyEngine(store_name=STORE_NAME, product_url=PRODUCT_URL)

    reviews = (
        [Review(author=args.author, rating=args.rating or 3, content=args.review)]
        if args.review
        else sample_reviews()
    )

    print(f"상품 URL: {PRODUCT_URL}")
    print("실제 스마트스토어에는 답변을 등록하지 않습니다.")
    print()

    for index, review in enumerate(reviews, start=1):
        reply = engine.generate(review)
        print(f"[{index}] 리뷰")
        print(f"- 작성자: {review.author}")
        print(f"- 평점: {review.rating}")
        print(f"- 내용: {review.content}")
        print(f"- 분류: {reply.sentiment.value}")
        print("[생성 답변]")
        print(reply.text)
        print()


if __name__ == "__main__":
    main()
