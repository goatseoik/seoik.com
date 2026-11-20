# AI 학습 도우미 — 진짜 AI 답변 켜기

지금은 사이트 안 개념노트·문제 해설에서 찾아 답하는 모드다. 아래를 한 번 하면 그 자료를 근거로 생성형 AI가 문장으로 설명해 준다. (무료)

1. https://aistudio.google.com 에서 구글 계정으로 로그인 → **Get API key** → 키 복사
2. https://dash.cloudflare.com 가입 → **Workers & Pages → Create → Worker** → 이름 `seoik-ai` → Deploy
3. **Edit code**에서 내용을 모두 지우고 `ai/worker.js` 내용을 붙여 넣고 Deploy
4. Worker **Settings → Variables and Secrets → Add** → Type: Secret, 이름 `GEMINI_KEY`, 값: 1번 키 → Save
5. Worker 주소(예: `https://seoik-ai.아이디.workers.dev`)를 index.html의 `const AI_URL = "";` 따옴표 안에 넣는다

API 키는 Cloudflare에만 있고 GitHub(공개)에는 올라가지 않는다. 다른 사이트에서는 호출이 막혀 있다.
