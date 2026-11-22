"""공통영어2 교과서 Lesson 3·4 본문 → 시험형 문항 + 문장·해석 빈칸 (english/textbook-2026.js)

원문·해석·출제 포인트는 english/textbook-2026-source.json 에 있다. 수정 후:
    python3 tools/build_english_textbook.py
"""
import html
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = json.loads((ROOT / 'english/textbook-2026-source.json').read_text())
CIRC = ['①', '②', '③', '④', '⑤']
esc = html.escape
sets, titles, topics = [], [], {}


def box(label, body_html):
    return '<div class="mat-wrap"><div class="mat-label">' + esc(label) + '</div><div class="mat-box">' + body_html + '</div></div>'


def short(p):
    return p['lesson'].split(' · ')[0] + ' ' + p['title'].split(' – ')[0]


def full_ko(p):
    return ' '.join(s['korean'] for s in p['sentences'])


def text_of(p, idx=None):
    return ' '.join(s['english'] for i, s in enumerate(p['sentences'], 1) if idx is None or i in idx)


def q_choice(p, kind, prompt, ok, wrong, explain, rnd, fixed=False):
    ch = [ok] + list(wrong)
    assert len(ch) == len(set(ch)) == 5, (p['id'], kind, ch)
    if not fixed:
        rnd.shuffle(ch)
    return dict(q=prompt, choices=ch, correct=ch.index(ok), explain=explain, source='공통영어2 교과서 ' + p['lesson'].split(' (')[0],
                kind=kind, passage=p['id'], fixed=fixed or None)


def q_pos(p, kind, prompt, correct, explain):
    return dict(q=prompt, choices=CIRC[:], correct=correct, explain=explain, source='공통영어2 교과서 ' + p['lesson'].split(' (')[0],
                kind=kind, passage=p['id'], fixed=True)


def underline_q(p, kind, items, wrong_i, stem, label):
    """items: [(target, wrong, why)] — 본문에서 5개를 밑줄 ①~⑤로 표시하고 그중 하나(wrong_i)를 틀린 것으로 바꾼다"""
    text = text_of(p)
    spots = []
    for t, w, why in items:
        pre, word, post = (t.split('[')[0], t.split('[')[1].split(']')[0], t.split(']')[1]) if '[' in t else ('', t, '')
        ctx = pre + word + post
        m = [x.start() for x in re.finditer(re.escape(ctx), text)]
        assert len(m) == 1, (p['id'], kind, t, len(m))
        spots.append((m[0] + len(pre), word, w, why, t))
    spots.sort()
    out, last = '', 0
    ans = None
    for k, (pos, word, w, why, key) in enumerate(spots):
        shown = w if items[wrong_i][0] == key else word
        if items[wrong_i][0] == key:
            ans = k
        out += esc(text[last:pos]) + CIRC[k] + '<u>' + esc(shown) + '</u>'
        last = pos + len(word)
    out += esc(text[last:])
    word, w, why = spots[ans][1], spots[ans][2], spots[ans][3]
    exp = f'정답 {CIRC[ans]}: {w} → {word}\n{why}\n\n' + '\n'.join(f'{CIRC[k]} {sp[1]}: 맞음' for k, sp in enumerate(spots) if k != ans) + '\n\n해석: ' + full_ko(p)
    return q_pos(p, kind, stem + box(label, out), ans, exp)


def build_passage(p, pi):
    rnd = random.Random(1000 + pi)
    S = p['sentences']
    n = len(S)
    whole = esc(text_of(p))
    qs = []
    ok, wrong = p['topic']
    qs.append(q_choice(p, 'topic', '다음 글의 주제로 가장 적절한 것은?' + box('지문', whole), ok, wrong, f'정답: {ok}\n\n해석: ' + full_ko(p), rnd))
    ok, wrong = p['title_q']
    qs.append(q_choice(p, 'title', '다음 글의 제목으로 가장 적절한 것은?' + box('지문', whole), ok, wrong, f'정답: {ok}\n\n해석: ' + full_ko(p), rnd))
    T = [s for s, v in p['tf'] if v]
    F = [s for s, v in p['tf'] if not v]
    for k in range(2):
        f = F[k]
        qs.append(q_choice(p, 'detail', '다음 글의 내용과 일치하지 않는 것은?' + box('지문', whole), f, T[k:k + 4] if k + 4 <= len(T) else T[:4],
                           f'정답: {f}\n(본문과 다른 내용)\n\n해석: ' + full_ko(p), rnd))
    t = T[-1]
    qs.append(q_choice(p, 'detail', '다음 글의 내용과 일치하는 것은?' + box('지문', whole), t, F[:4], f'정답: {t}\n나머지는 본문과 다르다.\n\n해석: ' + full_ko(p), rnd))
    def spot(t):
        ctx = t.replace('[', '').replace(']', '')
        return text_of(p).index(ctx) + (t.index('[') if '[' in t else 0)

    def pick5(items, wi, a):
        """wi번째 항목을 틀린 것으로 하고, 그것이 a번째(0~4) 밑줄이 되도록 앞뒤에서 4개를 고른다"""
        srt = sorted(items, key=lambda x: spot(x[0]))
        w = items[wi]
        k = srt.index(w)
        before, after = srt[:k], srt[k + 1:]
        nb = min(a, len(before)); na = 4 - nb
        if na > len(after): na = len(after); nb = 4 - na
        spread = lambda L, m: [L[round(i * (len(L) - 1) / max(m - 1, 1))] for i in range(m)] if m and len(L) > m else L[:m] if m else []
        chosen = spread(before, nb) + spread(after, na)
        assert len(set(map(tuple, chosen))) == 4, (p['id'], w)
        return [tuple(w)] + [tuple(x) for x in chosen]

    G = [tuple(x) for x in p['grammar']]
    for v in range(3):
        wi = (v * len(G) // 3 + pi) % len(G)
        qs.append(underline_q(p, 'grammar', pick5(G, wi, (pi * 2 + v * 3) % 5), 0, '다음 글의 밑줄 친 부분 중, 어법상 틀린 것은?', '지문'))
    V = [tuple(x) for x in p['vocab']]
    for v in range(2):
        wi = (v * len(V) // 2 + pi * 3) % len(V)
        qs.append(underline_q(p, 'vocab', pick5(V, wi, (pi * 3 + v * 2 + 1) % 5), 0, '다음 글의 밑줄 친 부분 중, 문맥상 낱말의 쓰임이 적절하지 않은 것은?', '지문'))
    for v, k in enumerate(p['insert']):
        given = S[k - 1]['english']
        rest = [s['english'] for i, s in enumerate(S, 1) if i != k]
        pos = k - 1  # 빠진 문장이 들어갈 자리: rest[pos] 앞 (pos == len(rest) 이면 맨 끝)
        slots = list(range(1, len(rest) + 1))  # j: rest[j] 앞 (len(rest) = 끝)
        start = max(0, min(slots.index(pos) - (pi + v) % 5, len(slots) - 5)) if pos in slots else 0
        win = slots[start:start + 5]
        assert pos in win and len(win) == 5, (p['id'], k, win)
        out = ''
        for j, sent in enumerate(rest):
            if j in win: out += f' ( {CIRC[win.index(j)]} ) '
            out += esc(sent) + ' '
        if len(rest) in win: out += f' ( {CIRC[win.index(len(rest))]} )'
        prompt = '글의 흐름으로 보아, 주어진 문장이 들어가기에 가장 적절한 곳은?' + box('주어진 문장', esc(given)) + box('지문', out.strip())
        qs.append(q_pos(p, 'insert', prompt, win.index(pos), f'정답 {CIRC[win.index(pos)]}\n주어진 문장: {given}\n해석: {S[k - 1]["korean"]}\n\n전체 해석: ' + full_ko(p)))
    if p.get('order'):
        o = p['order']
        blocks = o['blocks']
        perms = [(0, 1, 2), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0), (0, 2, 1)]
        perm = perms[pi % len(perms)]
        shown = [blocks[j] for j in perm]
        ans = ' → '.join('ABC'[perm.index(j)] for j in range(3))
        allc = ['A → C → B', 'B → A → C', 'B → C → A', 'C → A → B', 'C → B → A', 'A → B → C']
        ch = [c for c in allc if c != ans][:4] + [ans]
        ch.sort(key=['A → B → C', 'A → C → B', 'B → A → C', 'B → C → A', 'C → A → B', 'C → B → A'].index)
        prompt = '주어진 글 다음에 이어질 글의 순서로 가장 적절한 것은?' + box('주어진 글', esc(text_of(p, range(1, o['given'] + 1))))
        for L, b in zip('ABC', shown):
            prompt += box(f'({L})', esc(text_of(p, b)))
        qs.append(dict(q=prompt, choices=ch, correct=ch.index(ans), explain=f'정답 순서: {ans}\n\n해석: ' + full_ko(p), source='공통영어2 교과서 ' + p['lesson'].split(' (')[0],
                       kind='sequence', passage=p['id'], fixed=True))
    for si, phrase, wrong, why in p['blank']:
        sent = S[si - 1]['english']
        assert phrase in sent, (p['id'], phrase)
        body = ' '.join(esc(s['english'].replace(phrase, '__________') if i == si else s['english']) for i, s in enumerate(S, 1))
        qs.append(q_choice(p, 'blank', '다음 빈칸에 들어갈 말로 가장 적절한 것은?' + box('지문', body), phrase, wrong, f'정답: {phrase}\n{why}\n\n해석: ' + full_ko(p), rnd))
    if p.get('irrelevant'):
        ir = p['irrelevant']
        win = ir['window']
        seq = []
        for i in win:
            if i == ir['at']: seq.append(('X', ir['sentence']))
            seq.append((i, S[i - 1]['english']))
        full = [(i, S[i - 1]['english']) for i in range(1, n + 1)]
        xi = [i for i, (k, _) in enumerate(full) if k == ir['at']][0]
        full.insert(xi, ('X', ir['sentence']))
        want = pi % 5
        st = max(1, min(xi - want, len(full) - 5))
        numbered = full[st:st + 5]
        before = ' '.join(t for _, t in full[:st])
        after_idx = [k for k, _ in full[st + 5:]]
        body = esc(before) + ' ' + ' '.join(CIRC[k] + ' ' + esc(t) for k, (_, t) in enumerate(numbered)) + ' ' + esc(' '.join(S[i - 1]['english'] for i in after_idx))
        ans = [x[0] for x in numbered].index('X')
        qs.append(q_pos(p, 'irrelevant', '다음 글에서 전체 흐름과 관계 없는 문장은?' + box('지문', body.strip()), ans,
                        f'정답 {CIRC[ans]}: {ir["sentence"]}\n글의 중심 소재와 관계없는 문장이다.\n\n해석: ' + full_ko(p)))
    stext, okp, wrongp = p['summary']
    fmt = lambda a: f'(A) {a[0]} …… (B) {a[1]}'
    qs.append(q_choice(p, 'summary', '다음 글의 내용을 한 문장으로 요약하고자 한다. 빈칸 (A), (B)에 들어갈 말로 가장 적절한 것은?' + box('지문', whole) + box('요약문', esc(stext)),
                       fmt(okp), [fmt(x) for x in wrongp], f'정답: {fmt(okp)}\n\n해석: ' + full_ko(p), rnd))
    return [{k: v for k, v in q.items() if v is not None} for q in qs]


def add(title, questions, topic):
    sets.append(questions)
    titles.append(title)
    topics[str(len(sets) - 1)] = topic
    return len(sets) - 1


units = []
for lesson, lname in [('Lesson 3', '교과서 Lesson 3 · Go Beyond Korea'), ('Lesson 4', '교과서 Lesson 4 · Technology and Our Lives')]:
    idx = []
    for pi, p in enumerate(SRC['passages']):
        if not p['lesson'].startswith(lesson): continue
        qs = build_passage(p, pi)
        idx.append(add(f'{lesson} · {p["title"]} — 주제·내용·어법·어휘·삽입·순서·빈칸·요약', qs,
                       ['교과서 본문 그대로 (사진 자료)', '어법·어휘 밑줄 · 문장 삽입 · 글의 순서', '빈칸 · 무관한 문장 · 요약문']))
    voc = [v for v in SRC['vocab'] if v[2] == lesson[0] + lesson[-1] or v[2] == 'L' + lesson[-1]]
    rnd = random.Random(77 + len(units))
    vq = []
    for k, (w, d, _) in enumerate(voc):
        others = [x[0] for x in voc if x[0] != w]
        rnd.shuffle(others)
        ch = [w] + others[:4]
        rnd.shuffle(ch)
        vq.append(dict(q='다음 영영풀이에 해당하는 단어로 가장 적절한 것은?' + box('영영풀이', esc(d)), choices=ch, correct=ch.index(w),
                       explain=f'정답: {w}\n{d}', source='공통영어2 교과서 ' + lesson, kind='vocab-def', passage=lesson))
    idx.append(add(f'{lesson} · 교과서 핵심 어휘 영영풀이', vq, ['본문 핵심 어휘', '영영풀이 → 단어', lesson]))
    units.append(dict(name=lname, desc='교과서 본문(사진) 기반 · 주제·제목·일치·어법·어휘·삽입·순서·빈칸·무관한 문장·요약', indices=idx))

# 문장·해석 빈칸 (10월 모의고사와 같은 방식)
stop = set('the and that this those these with from have has had will would could should their there they them then than what when where which while because before after some same more most many much into just only also very even each such other first second third last part been being does through about under over people things something anything'.split())


def target_english(text):
    words = re.findall(r"[A-Za-z]+(?:[’'-][A-Za-z]+)*", text)
    cands = [w for w in words if w.lower() not in stop and len(w) > 3]
    low = [w for w in cands if w[0].islower()] or cands   # 고유명사(Korean, NASA …)보다 내용어를 우선
    uniq = [w for w in low if words.count(w) == 1]
    return max(uniq or low or words, key=len)


def target_korean(text):
    toks = re.findall(r'[가-힣]+', text)
    cands = [w for w in toks if len(w) >= 3 and w not in ['그것은', '그것이', '이것은', '우리는', '그들은', '그것의']]
    uniq = [w for w in cands if text.count(w) == 1]
    return max(uniq or cands or toks, key=len)


cloze_idx = []
for lang, label in [('english', '영어 빈칸'), ('korean', '해석 빈칸')]:
    pick = target_english if lang == 'english' else target_korean
    pool = list(dict.fromkeys(pick(s[lang]) for p in SRC['passages'] for s in p['sentences']))
    for pi, p in enumerate(SRC['passages']):
        qs = []
        for i, s in enumerate(p['sentences']):
            ans = pick(s[lang])
            others = [x for x in pool if x.lower() != ans.lower()]
            st = (i * 7 + pi * 3) % (len(others) - 4)
            ch = [ans] + others[st:st + 4]
            blanked = s[lang].replace(ans, '__________', 1)
            prompt = f'{p["id"]} · {i + 1}번째 문장 · {label}을 채우세요.'
            prompt += (box('우리말 해석', esc(s['korean'])) + box('영어 빈칸', esc(blanked))) if lang == 'english' else (box('영어 원문', esc(s['english'])) + box('해석 빈칸', esc(blanked)))
            qs.append(dict(q=prompt, choices=ch, correct=0, explain=f'정답: {ans}\n영어: {s["english"]}\n해석: {s["korean"]}',
                           source='공통영어2 교과서 ' + p['lesson'].split(' (')[0], kind=lang + '-cloze', passage=p['id'], sentence=i + 1,
                           cloze=dict(answer=ans, language=lang)))
        cloze_idx.append(add(f'교과서 {p["id"]} · {p["title"].split(" – ")[0]} · 문장별 {label}', qs, ['교과서 본문 문장', '영어·해석 함께 쓰기', p['lesson']]))
units.append(dict(name='교과서 Lesson 3·4 · 문장·해석 빈칸', notebook=True, desc='개념노트처럼 교과서 본문 영어와 해석을 한 화면에서 함께 채우기', indices=cloze_idx))


def hl(text, ans):
    a, b = text.split(ans, 1)
    return esc(a) + '<mark class="mk-hl">' + esc(ans) + '</mark>' + esc(b)


sections = []
for p in SRC['passages']:
    pairs = ''.join(
        f'<article class="en-note-pair" data-sentence="{i}"><div class="en-note-num">{i:02d} 문장</div>'
        f'<p class="en-note-line" lang="en">{hl(s["english"], target_english(s["english"]))}</p>'
        f'<p class="en-note-line en-note-translation" lang="ko">{hl(s["korean"], target_korean(s["korean"]))}</p></article>'
        for i, s in enumerate(p['sentences'], 1))
    sections.append(dict(tag='교과서 ' + p['id'], passage=p['id'], title=p['title'], html=pairs))

payload = dict(quiz=sets, titles=titles, units=units, topics=topics, sections=sections)
(ROOT / 'english/textbook-2026.js').write_text('// Generated by tools/build_english_textbook.py from english/textbook-2026-source.json\nwindow.SEOIK_ENGLISH_TEXTBOOK = '
                                               + json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + ';\n')
print(f'{len(sets)} sets, {sum(map(len, sets))} questions ({sum(len(sets[i]) for u in units[:2] for i in u["indices"])} exam-style)')
