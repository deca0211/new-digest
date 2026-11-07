"""RSS 수집 -> AI 요약 -> data/articles.json 저장.

- 새 글만 요약합니다(URL 기준 중복 제거).
- 요약은 RSS가 주는 제목+발췌만 사용하고 원문 전문은 저장하지 않습니다.
- ANTHROPIC_API_KEY가 없으면 요약 없이 수집만 합니다(테스트용).
"""
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import feedparser

# ★ 여기를 수정해서 소스를 바꾸세요. 학교 학과 공지 RSS 주소도 추가해 보세요.
SOURCES = [
    {"name": "GeekNews", "url": "https://news.hada.io/rss/news"},
    {"name": "Hacker News", "url": "https://hnrss.org/frontpage"},
]

DATA_FILE = Path("data/articles.json")
MAX_PER_FEED = 15        # 소스당 한 번에 가져올 최대 글 수
MAX_SUMMARIES_PER_RUN = 20  # 하루 요약 호출 상한 (비용 보호)
MAX_STORED = 300         # 저장할 최대 글 수
MODEL = "claude-haiku-5-5"

PROMPT = """아래 글의 제목과 발췌를 보고 JSON으로만 답하세요.
{{"summary": "한국어 2문장 요약", "keywords": ["키워드1", "키워드2", "키워드3"]}}

제목: {title}
발췌: {excerpt}"""


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def load() -> list:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []


def collect(known: set) -> list:
    new = []
    for src in SOURCES:
        try:
            feed = feedparser.parse(src["url"])
        except Exception as e:  # 한 소스가 실패해도 계속 진행
            print(f"[skip] {src['name']}: {e}")
            continue
        for e in feed.entries[:MAX_PER_FEED]:
            link = e.get("link")
            if not link or link in known:
                continue
            known.add(link)
            new.append({
                "title": clean(e.get("title")),
                "url": link,
                "source": src["name"],
                "published": e.get("published", ""),
                "excerpt": clean(e.get("summary"))[:500],
                "summary": "",
                "keywords": [],
                "collected_at": datetime.now(timezone.utc).isoformat(),
            })
        time.sleep(1)  # 서버에 부담을 주지 않도록 간격 두기
    return new


def summarize(items: list) -> None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("ANTHROPIC_API_KEY 없음 -> 요약 생략")
        return
    import anthropic
    client = anthropic.Anthropic(api_key=key)
    for item in items[:MAX_SUMMARIES_PER_RUN]:
        try:
            msg = client.messages.create(
                model=MODEL,
                max_tokens=300,
                messages=[{"role": "user", "content": PROMPT.format(
                    title=item["title"], excerpt=item["excerpt"])}],
            )
            raw = msg.content[0].text.strip()
            raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
            data = json.loads(raw)
            item["summary"] = data.get("summary", "")
            item["keywords"] = data.get("keywords", [])[:5]
        except Exception as e:
            print(f"[요약 실패] {item['title'][:30]}: {e}")


def main() -> None:
    DATA_FILE.parent.mkdir(exist_ok=True)
    articles = load()
    new = collect({a["url"] for a in articles})
    print(f"새 글 {len(new)}개")
    summarize(new)
    articles = (new + articles)[:MAX_STORED]
    DATA_FILE.write_text(
        json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
