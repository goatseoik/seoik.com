"""올림포스 영어독해의 기본2 Unit 10·11·12·14 → 시험형 문항 + 문장·해석 빈칸 (english/olympus-2026.js)

원문·해석(분석 자료 PDF 그대로)·출제 포인트는 english/olympus-2026-source.json 에 있다. 수정 후:
    python3 tools/build_english_olympus.py
"""
import html
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = json.loads((ROOT / 'english/olympus-2026-source.json').read_text())
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
    return dict(q=prompt, choices=ch, correct=ch.index(ok), explain=explain, source=p['lesson'],
                kind=kind, passage=p['id'], fixed=fixed or None)


def q_pos(p, kind, prompt, correct, explain):
    return dict(q=prompt, choices=CIRC[:], correct=correct, explain=explain, source=p['lesson'],
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



P = SRC['passages']


def others(p, key, k, rnd):
    """다른 지문의 같은 항목(주제·요지·제목)에서 길이가 비슷한 것으로 오답 k개"""
    pool = [x[key] for x in P if x['id'] != p['id'] and x[key] and x[key] != p[key]]
    pool.sort(key=lambda s: abs(len(s) - len(p[key])))
    near = pool[:8]
    rnd.shuffle(near)
    return near[:k]


def build_passage(p, pi):
    rnd = random.Random(2000 + pi)
    S = p['sentences']
    n = len(S)
    whole = esc(text_of(p))
    qs = []
    qs.append(q_choice(p, 'topic', '다음 글의 주제로 가장 적절한 것은?' + box('지문', whole), p['topic_en'], others(p, 'topic_en', 4, rnd),
                       f'정답: {p["topic_en"]}\n({p["topic_ko"]})\n\n해석: ' + full_ko(p), rnd))
    qs.append(q_choice(p, 'title', '다음 글의 제목으로 가장 적절한 것은?' + box('지문', whole), p['title'], others(p, 'title', 4, rnd),
                       f'정답: {p["title"]}\n({p["title_ko"]})\n\n해석: ' + full_ko(p), rnd))
    qs.append(q_choice(p, 'gist', '다음 글의 요지로 가장 적절한 것은?' + box('지문', whole), p['summary_ko'], others(p, 'summary_ko', 4, rnd),
                       f'정답: {p["summary_ko"]}\n\n해석: ' + full_ko(p), rnd))
    si, phrase, wrong, why = p['blank']
    sent = S[si - 1]['english']
    assert sent.count(phrase) == 1, (p['id'], phrase)
    body = ' '.join(esc(s['english'].replace(phrase, '__________') if i == si else s['english']) for i, s in enumerate(S, 1))
    qs.append(q_choice(p, 'blank', '다음 빈칸에 들어갈 말로 가장 적절한 것은?' + box('지문', body), phrase, wrong,
                       f'정답: {phrase}\n{why}\n\n빈칸 문장 해석: {S[si - 1]["korean"]}\n\n전체 해석: ' + full_ko(p), rnd))
    G = [tuple(x) for x in p['grammar']]
    qs.append(underline_q(p, 'grammar', G, 0, '다음 글의 밑줄 친 부분 중, 어법상 틀린 것은?', '지문'))
    # 글의 순서: 첫 문장(들)을 주어진 글로, 나머지를 세 덩어리로
    g = 1 if n <= 7 else 2
    rest = list(range(g + 1, n + 1))
    cut = [round(len(rest) * k / 3) for k in range(4)]
    blocks = [rest[cut[k]:cut[k + 1]] for k in range(3)]
    assert all(blocks), p['id']
    perms = [(1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0), (0, 2, 1)]
    perm = perms[pi % len(perms)]
    shown = [blocks[j] for j in perm]
    ans = ' → '.join('ABC'[perm.index(j)] for j in range(3))
    order_all = ['A → B → C', 'A → C → B', 'B → A → C', 'B → C → A', 'C → A → B', 'C → B → A']
    ch = [c for c in order_all if c != ans and c != 'A → B → C'][:4] + [ans]
    ch.sort(key=order_all.index)
    prompt = '주어진 글 다음에 이어질 글의 순서로 가장 적절한 것은?' + box('주어진 글', esc(text_of(p, range(1, g + 1))))
    for L, b in zip('ABC', shown):
        prompt += box(f'({L})', esc(text_of(p, b)))
    qs.append(dict(q=prompt, choices=ch, correct=ch.index(ans), explain=f'정답 순서: {ans}\n\n해석: ' + full_ko(p), source=p['lesson'],
                   kind='sequence', passage=p['id'], fixed=True))
    # 문장 삽입 (6문장 이상인 지문만)
    if n >= 6:
        k = n // 2 + 1 + (pi % 2)
        k = min(k, n)
        given = S[k - 1]['english']
        rest_s = [s['english'] for i, s in enumerate(S, 1) if i != k]
        pos = k - 1
        slots = list(range(1, len(rest_s) + 1))
        start = max(0, min(slots.index(pos) - pi % 5, len(slots) - 5))
        win = slots[start:start + 5]
        assert pos in win and len(win) == 5, (p['id'], k, win)
        out = ''
        for j, s2 in enumerate(rest_s):
            if j in win: out += f' ( {CIRC[win.index(j)]} ) '
            out += esc(s2) + ' '
        if len(rest_s) in win: out += f' ( {CIRC[win.index(len(rest_s))]} )'
        qs.append(q_pos(p, 'insert', '글의 흐름으로 보아, 주어진 문장이 들어가기에 가장 적절한 곳은?' + box('주어진 문장', esc(given)) + box('지문', out.strip()),
                        win.index(pos), f'정답 {CIRC[win.index(pos)]}\n주어진 문장: {given}\n해석: {S[k - 1]["korean"]}\n\n전체 해석: ' + full_ko(p)))
    return [{k: v for k, v in q.items() if v is not None} for q in qs]


def add(title, questions, topic):
    sets.append(questions)
    titles.append(title)
    topics[str(len(sets) - 1)] = topic
    return len(sets) - 1


UNITS = [('10', '단어 빈칸'), ('11', '짧은 어구 빈칸'), ('12', '긴 어구 빈칸'), ('14', '글의 순서 배열')]
units = []
for u, uname in UNITS:
    idx = []
    for pi, p in enumerate(P):
        if p['unit'] != u: continue
        idx.append(add(f'올림포스 {u}강 {p["label"]} · {p["title"]} — 주제·제목·요지·빈칸·어법·순서·삽입', build_passage(p, pi),
                       ['올림포스 분석 자료 원문 그대로', '주제·제목·요지 · 빈칸', '어법 밑줄 · 글의 순서 · 문장 삽입']))
    units.append(dict(name=f'올림포스 독해의 기본2 · {u}강 {uname}', desc='분석 자료 원문 그대로 · 주제·제목·요지·빈칸·어법·순서·삽입', indices=idx))

stop = set('the and that this those these with from have has had will would could should their there they them then than what when where which while because before after some same more most many much into just only also very even each such other first second third last part been being does through about under over people things something anything'.split())


def target_english(text):
    words = re.findall(r"[A-Za-z]+(?:[’'-][A-Za-z]+)*", text)
    cands = [w for w in words if w.lower() not in stop and len(w) > 3]
    low = [w for w in cands if w[0].islower()] or cands
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
    pool = list(dict.fromkeys(pick(s[lang]) for p in P for s in p['sentences']))
    for pi, p in enumerate(P):
        qs = []
        for i, s in enumerate(p['sentences']):
            ans = pick(s[lang])
            oth = [x for x in pool if x.lower() != ans.lower()]
            st = (i * 7 + pi * 3) % (len(oth) - 4)
            ch = [ans] + oth[st:st + 4]
            blanked = s[lang].replace(ans, '__________', 1)
            prompt = f'올림포스 {p["id"]} · {i + 1}번째 문장 · {label}을 채우세요.'
            prompt += (box('우리말 해석', esc(s['korean'])) + box('영어 빈칸', esc(blanked))) if lang == 'english' else (box('영어 원문', esc(s['english'])) + box('해석 빈칸', esc(blanked)))
            qs.append(dict(q=prompt, choices=ch, correct=0, explain=f'정답: {ans}\n영어: {s["english"]}\n해석: {s["korean"]}',
                           source=p['lesson'], kind=lang + '-cloze', passage=p['id'], sentence=i + 1, cloze=dict(answer=ans, language=lang)))
        cloze_idx.append(add(f'올림포스 {p["id"]} · {p["title"]} · 문장별 {label}', qs, ['올림포스 원문 문장', '영어·해석 함께 쓰기', p['lesson']]))
units.append(dict(name='올림포스 독해의 기본2 · 문장·해석 빈칸', notebook=True, desc='개념노트처럼 올림포스 원문 영어와 해석을 한 화면에서 함께 채우기', indices=cloze_idx))


def hl(text, ans):
    a, b = text.split(ans, 1)
    return esc(a) + '<mark class="mk-hl">' + esc(ans) + '</mark>' + esc(b)


sections = []
for p in P:
    pairs = ''.join(
        f'<article class="en-note-pair" data-sentence="{i}"><div class="en-note-num">{i:02d} 문장</div>'
        f'<p class="en-note-line" lang="en">{hl(s["english"], target_english(s["english"]))}</p>'
        f'<p class="en-note-line en-note-translation" lang="ko">{hl(s["korean"], target_korean(s["korean"]))}</p></article>'
        for i, s in enumerate(p['sentences'], 1))
    pairs += f'<p class="en-note-line en-note-translation" lang="ko"><b>주제</b> {esc(p["topic_ko"])} · <b>요약</b> {esc(p["summary_ko"])}</p>'
    sections.append(dict(tag='올림포스 ' + p['id'], passage=p['id'], title=p['title'] + ' (' + p['title_ko'] + ')', html=pairs))

payload = dict(quiz=sets, titles=titles, units=units, topics=topics, sections=sections)
(ROOT / 'english/olympus-2026.js').write_text('// Generated by tools/build_english_olympus.py from english/olympus-2026-source.json\nwindow.SEOIK_ENGLISH_OLYMPUS = '
                                              + json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + ';\n')
print(f'{len(sets)} sets, {sum(map(len, sets))} questions ({sum(len(sets[i]) for u in units[:-1] for i in u["indices"])} exam-style)')
