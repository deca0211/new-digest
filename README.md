# 뉴스 다이제스트

RSS로 글을 모아 AI가 2문장으로 요약하고, 웹페이지로 보여주는 프로젝트입니다.
GitHub Actions가 매일 자동으로 수집·요약하고, GitHub Pages가 결과를 공개합니다.

## 구조
```
RSS 수집(fetch_news.py) -> AI 요약 -> data/articles.json -> index.html
        ^ GitHub Actions(cron, 매일 07:00 KST)가 자동 실행
```

## 설정 방법
1. 이 폴더를 GitHub 저장소로 올리기
2. Settings > Secrets and variables > Actions > `ANTHROPIC_API_KEY` 등록
3. Settings > Pages > Branch를 `main` / root로 설정
4. Actions 탭 > update-news > Run workflow로 첫 실행

## 설계 포인트
- URL 기준 중복 제거, 소스 하나가 실패해도 계속 진행
- 하루 요약 호출 상한(`MAX_SUMMARIES_PER_RUN`)으로 비용 제한
- 제목·링크·짧은 요약만 저장하고 원문 전문은 저장하지 않음(저작권)
- API 키는 Secrets로만 관리

## 로컬 실행 (설치가 가능한 환경에서)
```
pip install -r requirements.txt
python fetch_news.py
python -m http.server   # http://localhost:8000
```

## 배운 점 / 트러블슈팅
(직접 채워 넣으세요)
