// 서익닷컴 AI 학습 도우미 프록시 (Cloudflare Workers 무료)
// 환경 변수(Secret) GEMINI_KEY 에 Google AI Studio에서 받은 무료 API 키를 넣는다. 키는 사이트 코드에 절대 넣지 않는다.
const ALLOW = ["https://goatseoik.github.io"];
const SYSTEM = "너는 고1 내신 대비 사이트 '서익닷컴'의 학습 도우미야. 한국어 반말로, 고등학생이 이해하기 쉽게 핵심부터 짧게 설명해. " +
  "아래 [사이트 자료]가 질문과 관련 있으면 그 내용을 우선 근거로 쓰고, 자료에 없는 내용은 일반 지식으로 보충하되 확실하지 않으면 모른다고 해. " +
  "수학은 풀이 과정을 단계별로 보여 줘. 시험 문제를 대신 풀어 주는 게 아니라 이해를 돕는 게 목적이야.";
export default {
  async fetch(req, env) {
    const origin = req.headers.get("Origin") || "";
    const cors = { "Access-Control-Allow-Origin": ALLOW.includes(origin) ? origin : ALLOW[0], "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Allow-Methods": "POST, OPTIONS" };
    if (req.method === "OPTIONS") return new Response(null, { headers: cors });
    if (req.method !== "POST" || !ALLOW.includes(origin)) return new Response("forbidden", { status: 403, headers: cors });
    let body; try { body = await req.json(); } catch (e) { return new Response("bad", { status: 400, headers: cors }); }
    const q = String(body.question || "").slice(0, 600), ctx = String(body.context || "").slice(0, 4000);
    const hist = (Array.isArray(body.history) ? body.history : []).slice(-6).flatMap(h => [
      { role: "user", parts: [{ text: String(h.q).slice(0, 400) }] }, { role: "model", parts: [{ text: String(h.a).slice(0, 1200) }] }]);
    const r = await fetch("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + env.GEMINI_KEY, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ systemInstruction: { parts: [{ text: SYSTEM }] },
        contents: hist.concat([{ role: "user", parts: [{ text: "[사이트 자료]\n" + ctx + "\n\n[질문]\n" + q }] }]),
        generationConfig: { maxOutputTokens: 800, temperature: 0.4 } })
    });
    const j = await r.json().catch(() => ({}));
    const answer = (((j.candidates || [])[0] || {}).content || {}).parts?.map(p => p.text).join("") || "";
    return new Response(JSON.stringify({ answer }), { headers: { ...cors, "Content-Type": "application/json" } });
  }
};
