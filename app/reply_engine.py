from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReviewSentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass(frozen=True)
class Review:
    author: str
    rating: int
    content: str
    review_id: str = ""


@dataclass(frozen=True)
class Reply:
    review: Review
    sentiment: ReviewSentiment
    text: str


class ReplyEngine:
    """Offline-safe reply generator for console-only testing."""

    def __init__(self, store_name: str, product_url: str) -> None:
        self.store_name = store_name
        self.product_url = product_url

    def generate(self, review: Review) -> Reply:
        sentiment = self._classify(review)
        salutation = _salutation(review.author)

        if sentiment == ReviewSentiment.POSITIVE:
            text = (
                f"{salutation}, 소중한 후기 감사합니다. "
                "상품을 만족스럽게 사용해 주신다니 정말 기쁩니다. "
                "앞으로도 좋은 품질과 빠른 응대로 보답하겠습니다."
            )
        elif sentiment == ReviewSentiment.NEGATIVE:
            text = (
                f"{salutation}, 이용에 불편을 드려 죄송합니다. "
                "남겨주신 내용은 확인 후 개선에 반영하겠습니다. "
                "문제가 계속된다면 주문 정보와 함께 고객센터로 문의 부탁드립니다."
            )
        else:
            text = (
                f"{salutation}, 후기 남겨주셔서 감사합니다. "
                "말씀해주신 의견을 꼼꼼히 확인하고 더 만족스러운 상품과 서비스로 보답하겠습니다."
            )

        return Reply(review=review, sentiment=sentiment, text=text)

    def _classify(self, review: Review) -> ReviewSentiment:
        content = review.content.lower()
        negative_keywords = [
            "별로",
            "아쉬",
            "불편",
            "안 좋아",
            "파손",
            "환불",
            "교환",
            "문제",
            "bad",
            "disappointed",
        ]
        positive_keywords = [
            "좋",
            "만족",
            "빠르",
            "추천",
            "깔끔",
            "재구매",
            "최고",
            "good",
            "great",
        ]

        if review.rating <= 2 or any(keyword in content for keyword in negative_keywords):
            return ReviewSentiment.NEGATIVE
        if review.rating >= 4 or any(keyword in content for keyword in positive_keywords):
            return ReviewSentiment.POSITIVE
        return ReviewSentiment.NEUTRAL


def sample_reviews() -> list[Review]:
    return [
        Review(
            author="테스트고객",
            rating=5,
            content="배송 빠르고 상품도 마음에 들어요. 재구매할게요.",
            review_id="sample-1",
        ),
        Review(
            author="테스트고객",
            rating=3,
            content="무난합니다. 아직 오래 써보지는 않았어요.",
            review_id="sample-2",
        ),
        Review(
            author="테스트고객",
            rating=1,
            content="배송이 늦고 포장이 조금 파손되어 왔습니다.",
            review_id="sample-3",
        ),
    ]


def _salutation(author: str) -> str:
    if not author or author == "고객님":
        return "고객님"
    return f"{author} 고객님"
