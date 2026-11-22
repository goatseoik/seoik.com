// 서익닷컴 AI 학습 도우미 프록시 (Cloudflare Workers 무료)
// 환경 변수(Secret) GEMINI_KEY 에 Google AI Studio에서 받은 무료 API 키를 넣는다. 키는 사이트 코드에 절대 넣지 않는다.
const ALLOW = ["https://goatseoik.github.io"];
const SYSTEM = "너는 고1 학생을 돕는 똑똑한 AI 학습 도우미야. 한국어 반말로 친근하게, 핵심부터 쉽게 설명해. " +
  "질문에는 네가 아는 모든 지식으로 자유롭게 생각해서 답해. 학교 공부와 상관없는 질문(코딩, 진로, 상식, 고민 등)도 성실하게 답해 줘. " +
  "아래 [참고 자료]는 학생이 공부하는 사이트의 노트·문제 중 질문과 비슷해 보이는 것들이야. 질문과 실제로 관련 있을 때만 참고해서 '시험 범위에서는 이렇게 정리돼 있어'처럼 연결해 주고, 관련 없으면 완전히 무시해. 자료에 없다는 이유로 답을 거절하거나 줄이지 마. " +
  "수학·과학 계산은 풀이 과정을 단계별로 보여 줘. 확실하지 않은 사실은 확실하지 않다고 말해.";
export default {
  async fetch(req, env) {
    const origin = req.headers.get("Origin") || "";
    const cors = { "Access-Control-Allow-Origin": ALLOW.includes(origin) ? origin : ALLOW[0], "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Allow-Methods": "POST, OPTIONS" };
    if (req.method === "OPTIONS") return new Response(null, { headers: cors });
    if (req.method !== "POST") return new Response("seoik-ai OK (코드 배포됨) · 키 " + (env.GEMINI_KEY ? "있음" : "없음") + " · 모델 " + (env.MODEL || "gemini-3.5-flash-lite"), { headers: { ...cors, "Content-Type": "text/plain; charset=utf-8" } });
    if (!ALLOW.includes(origin)) return new Response("forbidden", { status: 403, headers: cors });
    let body; try { body = await req.json(); } catch (e) { return new Response("bad", { status: 400, headers: cors }); }
    const q = String(body.question || "").slice(0, 600), ctx = String(body.context || "").slice(0, 4000);
    const hist = (Array.isArray(body.history) ? body.history : []).slice(-6).flatMap(h => [
      { role: "user", parts: [{ text: String(h.q).slice(0, 400) }] }, { role: "model", parts: [{ text: String(h.a).slice(0, 1200) }] }]);
    const r = await fetch("https://generativelanguage.googleapis.com/v1beta/models/" + (env.MODEL || "gemini-3.5-flash-lite") + ":generateContent?key=" + env.GEMINI_KEY, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ systemInstruction: { parts: [{ text: SYSTEM }] },
        contents: hist.concat([{ role: "user", parts: [{ text: (ctx ? "[참고 자료 — 관련 있을 때만 사용]\n" + ctx + "\n\n" : "") + "[질문]\n" + q }] }]),
        generationConfig: { maxOutputTokens: 1500, temperature: 0.7 } })
    });
    const j = await r.json().catch(() => ({}));
    const answer = (((j.candidates || [])[0] || {}).content || {}).parts?.map(p => p.text).join("") || "";
    const error = answer ? "" : ((j.error && (j.error.status + " " + j.error.message)) || ("HTTP " + r.status));
    return new Response(JSON.stringify({ answer, error }), { headers: { ...cors, "Content-Type": "application/json" } });
  }
};
