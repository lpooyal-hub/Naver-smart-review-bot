from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from app.reply_engine import Review


DEFAULT_TIMEOUT_MS = 15_000
REVIEW_TAB_PATTERNS = ("리뷰", "구매평", "상품평")


def collect_visible_reviews(
    url: str,
    limit: int = 5,
    user_data_dir: str = ".playwright-profile",
    pause_for_login: bool = False,
) -> list[Review]:
    """Open a SmartStore product page and collect visible review text."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright가 설치되어 있지 않습니다. "
            "`pip install playwright` 후 `playwright install chromium`을 실행해 주세요."
        ) from exc

    with sync_playwright() as playwright:
        profile_dir = Path(user_data_dir)
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
            locale="ko-KR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 1000},
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
            page.wait_for_load_state("networkidle", timeout=DEFAULT_TIMEOUT_MS)

            if pause_for_login:
                input(
                    "브라우저에서 네이버 로그인을 완료한 뒤 Enter를 누르세요. "
                    "로그인 세션은 Playwright 프로필에 저장됩니다."
                )
                page.goto(url, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)
                page.wait_for_load_state("networkidle", timeout=DEFAULT_TIMEOUT_MS)

            _raise_if_unavailable(page)

            _open_review_area(page)
            page.wait_for_timeout(1500)

            return _extract_reviews_with_scroll(page, limit=limit)
        finally:
            context.close()


def _open_review_area(page: "Page") -> None:
    for label in REVIEW_TAB_PATTERNS:
        candidates = [
            page.get_by_role("tab", name=re.compile(label)),
            page.get_by_role("button", name=re.compile(label)),
            page.get_by_role("link", name=re.compile(label)),
            page.locator(f"text={label}"),
        ]

        for candidate in candidates:
            if _click_first_visible(candidate):
                return

    page.mouse.wheel(0, 900)


def _raise_if_unavailable(page: "Page") -> None:
    body_text = page.locator("body").inner_text(timeout=3000)
    if "현재 서비스 접속이 불가합니다" in body_text:
        raise RuntimeError(
            "네이버가 현재 서비스 접속 불가 페이지를 반환했습니다. "
            "잠시 후 다시 실행하거나 열린 브라우저에서 상품 페이지가 정상 표시되는지 확인해 주세요."
        )


def _click_first_visible(locator: "Locator") -> bool:
    try:
        count = min(locator.count(), 5)
    except Exception:
        return False

    for index in range(count):
        item = locator.nth(index)
        try:
            if not item.is_visible():
                continue

            item.click(timeout=3000)
            return True
        except Exception:
            continue

    return False


def _extract_reviews_with_scroll(page: "Page", limit: int) -> list[Review]:
    reviews: list[Review] = []
    seen: set[str] = set()

    for _ in range(8):
        _append_reviews(page, reviews=reviews, seen=seen, limit=limit)
        if len(reviews) >= limit:
            return reviews

        page.mouse.wheel(0, 850)
        page.wait_for_timeout(700)

    return reviews


def _append_reviews(
    page: "Page", reviews: list[Review], seen: set[str], limit: int
) -> None:
    review_blocks = _candidate_review_blocks(page)

    for block in review_blocks:
        for text in _visible_texts(block, limit=limit * 3):
            review = _parse_review(text)
            if review is None or review.content in seen:
                continue

            seen.add(review.content)
            reviews.append(review)
            if len(reviews) >= limit:
                return

    body_texts = page.locator("body").inner_text().splitlines()
    for text in body_texts:
        content = _clean_review_text(text)
        if _looks_like_review(content) and content not in seen:
            seen.add(content)
            reviews.append(Review(author="작성자확인필요", rating=3, content=content))
            if len(reviews) >= limit:
                return


def _candidate_review_blocks(page: "Page") -> Iterable["Locator"]:
    selectors = [
        "[data-shp-area*='review']",
        "[class*='review']",
        "[class*='Review']",
        "li",
        "article",
        "div",
    ]
    return (page.locator(selector) for selector in selectors)


def _visible_texts(locator: "Locator", limit: int) -> Iterable[str]:
    try:
        count = min(locator.count(), limit)
    except Exception:
        return

    for index in range(count):
        item = locator.nth(index)
        try:
            if item.is_visible():
                yield item.inner_text(timeout=1000)
        except Exception:
            continue


def _clean_review_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    blocked_prefixes = ("리뷰", "구매평", "평점", "신고", "도움돼요", "판매자", "옵션")
    content_lines = [
        line
        for line in lines
        if not any(line.startswith(prefix) for prefix in blocked_prefixes)
    ]
    return " ".join(content_lines)


def _parse_review(text: str) -> Review | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None

    author = _extract_author(lines)
    rating = _extract_rating(lines)
    content = _extract_content(lines)

    if not _looks_like_review(content):
        return None

    return Review(author=author, rating=rating, content=content)


def _extract_author(lines: list[str]) -> str:
    blocked = {
        "리뷰",
        "구매평",
        "상품평",
        "평점",
        "신고",
        "도움돼요",
        "판매자",
        "옵션",
        "한달사용기",
        "재구매",
    }
    masked_id_pattern = re.compile(r"^[\w가-힣]{1,12}\*{2,}[\w가-힣]*$")

    for line in lines[:8]:
        compact = line.replace(" ", "")
        if compact in blocked:
            continue
        if masked_id_pattern.match(compact):
            return compact
        if 2 <= len(compact) <= 12 and not any(char.isdigit() for char in compact):
            if not any(keyword in compact for keyword in ("평점", "옵션", "배송", "상품", "구매")):
                return compact

    return "작성자확인필요"


def _extract_rating(lines: list[str]) -> int:
    text = " ".join(lines)
    rating_patterns = [
        re.compile(r"(?:평점|별점)\s*([1-5])"),
        re.compile(r"([1-5])\s*점"),
    ]
    for pattern in rating_patterns:
        match = pattern.search(text)
        if match:
            return int(match.group(1))

    filled_star_count = text.count("★")
    if 1 <= filled_star_count <= 5:
        return filled_star_count

    return 3


def _extract_content(lines: list[str]) -> str:
    blocked_prefixes = (
        "리뷰",
        "구매평",
        "상품평",
        "평점",
        "별점",
        "신고",
        "도움돼요",
        "판매자",
        "옵션",
        "작성자",
    )
    metadata_patterns = [
        re.compile(r"^[\w가-힣]{1,12}\*{2,}[\w가-힣]*$"),
        re.compile(r"^\d{4}\.\d{1,2}\.\d{1,2}"),
        re.compile(r"^(?:평점|별점)\s*[1-5]"),
        re.compile(r"^[★☆]{1,5}$"),
    ]
    content_lines = []

    for line in lines:
        if any(line.startswith(prefix) for prefix in blocked_prefixes):
            continue
        if any(pattern.match(line.replace(" ", "")) for pattern in metadata_patterns):
            continue
        if len(line) <= 3:
            continue
        content_lines.append(line)

    return " ".join(content_lines)


def _looks_like_review(text: str) -> bool:
    if len(text) < 8 or len(text) > 500:
        return False
    if text.count(" ") < 1 and len(text) < 20:
        return False

    review_markers = ("좋", "만족", "배송", "구매", "상품", "사용", "아쉬", "빠르", "향", "피부")
    return any(marker in text for marker in review_markers)
