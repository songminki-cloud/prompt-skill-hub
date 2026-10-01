# Prompt & Skill Hub

맥북의 기존 지식 노트와 공용 스킬을 읽어 정적 웹사이트로 보여주는 개인용 허브다.

## 원본

- Prompt Gallery: `workspace/knowledge/03-Resources/Prompt/**/*.md`
- Skill Hub: `workspace/skills/*/SKILL.md`

원본은 이 저장소로 옮기지 않는다. `build.py`가 읽어서 `data.json`과 썸네일 사본을 생성한다.

## 갱신

```bash
python3 build.py
python3 -m http.server 8765
```

브라우저에서 `http://localhost:8765`로 확인한다.

## 공개 전 주의

GitHub Pages에 공개하기 전에는 프롬프트와 스킬 본문에 개인정보, 회사 비공개 정보, 로컬 경로, 자격증명이 없는지 별도로 점검해야 한다.
