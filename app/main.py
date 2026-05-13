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
    parser.add_argument("--review", help="답변 테스트에 사용할 리뷰 본문")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="실제 수집 대신 샘플 리뷰로 답변 생성만 테스트합니다.",
    )
    parser.add_argument(
        "--collect",
        action="store_true",
        help="Playwright headed 모드로 상품 페이지를 열고 실제 리뷰를 수집합니다.",
    )
    parser.add_argument("--url", default=PRODUCT_URL, help="수집할 스마트스토어 상품 URL")
    parser.add_argument("--limit", type=int, default=5, help="수집할 리뷰 최대 개수")
    parser.add_argument(
        "--user-data-dir",
        default=".playwright-profile",
        help="네이버 로그인 세션을 저장할 Playwright 프로필 경로",
    )
    parser.add_argument(
        "--pause-for-login",
        action="store_true",
        help="브라우저에서 직접 로그인한 뒤 Enter를 누르면 수집을 계속합니다.",
    )
    return parser.parse_args()


def build_reviews(args: argparse.Namespace) -> list[Review]:
    if args.review:
        return [Review(author=args.author, rating=args.rating or 3, content=args.review)]

    if args.sample:
        return sample_reviews()

    if args.collect or not args.review:
        from app.review_collector import collect_visible_reviews

        try:
            return collect_visible_reviews(
                url=args.url,
                limit=args.limit,
                user_data_dir=args.user_data_dir,
                pause_for_login=args.pause_for_login,
            )
        except RuntimeError as exc:
            print(f"리뷰 수집 실패: {exc}")
            return []

    return []


def main() -> None:
    args = parse_args()
    engine = ReplyEngine(store_name=STORE_NAME, product_url=args.url)
    reviews = build_reviews(args)

    print(f"상품 URL: {args.url}")
    if args.review or args.sample:
        print("실제 스마트스토어에는 답변을 등록하지 않습니다.")
    else:
        print("Playwright headed 모드로 화면에 보이는 실제 리뷰를 수집했습니다.")
    print()

    if not reviews:
        print("수집된 리뷰가 없습니다. 브라우저에서 리뷰 영역이 보이는지 확인해 주세요.")
        return

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
