"""Build the October English practice sets from reviewed sentence-aligned PDF data."""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / 'english/october-2026-source.json').read_text())
passages = source['passages']
sets, titles, units, topics = [], [], [], {}


def box(label, text):
    return '<div class="mat-wrap"><div class="mat-label">' + html.escape(label) + '</div><div class="mat-box">' + html.escape(text) + '</div></div>'


def add(title, questions):
    index = len(sets)
    sets.append(questions)
    titles.append(title)
    topics[str(index)] = ['첨부 필기 자료의 본문 기준', '정답과 원문·해석 확인', '18~24번·29~45번 (장문은 공통 지문)']
    return index


def question(p, kind, prompt, choices, answer, explanation, sentence=None):
    assert len(choices) == len(set(choices)) == 5
    return dict(q=prompt, choices=choices, correct=choices.index(answer), explain=explanation,
                source=f'2026년 10월 고1 {p["number"]}번', kind=kind,
                passage=p['number'], sentence=sentence)


reading = []
for kind, label, field in [('topic', '주제', 'topic'), ('gist', '요지', 'summary')]:
    questions = []
    for i, p in enumerate(passages):
        choices = [passages[(i + offset) % len(passages)][field] for offset in range(5)]
        choices = choices[i % 5:] + choices[:i % 5]
        text = ' '.join(s['english'] for s in p['sentences'])
        prompt = f'{p["number"]}번 · 다음 글의 {label}로 가장 적절한 것은?' + box('지문', text)
        questions.append(question(p, kind, prompt, choices, p[field], f'정답: {p[field]}\n{p["summary"]}\n\n전체 해석: ' + ' '.join(s['korean'] for s in p['sentences'])))
    reading.append(add(f'10월 모의고사 {label} (18~24·29~45번)', questions))

questions = []
orders = [(0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1)]
for i, p in enumerate(passages):
    sentences = p['sentences']
    rest = sentences[1:]
    cut1, cut2 = len(rest) // 3, len(rest) * 2 // 3
    blocks = [rest[:cut1], rest[cut1:cut2], rest[cut2:]]
    permutation = orders[i % 5]
    shown = [blocks[j] for j in permutation]
    answer = ' → '.join('ABC'[permutation.index(j)] for j in range(3))
    choices = ['A → B → C', 'A → C → B', 'B → A → C', 'B → C → A', 'C → A → B', 'C → B → A']
    choices.remove(next(x for x in reversed(choices) if x != answer))
    prompt = f'{p["number"]}번 · 주어진 글 다음에 이어질 글의 순서로 가장 적절한 것은?' + box('주어진 글', sentences[0]['english'])
    for letter, block in zip('ABC', shown):
        prompt += box(f'({letter})', ' '.join(s['english'] for s in block))
    explanation = f'정답 순서: {answer}\n{p["summary"]}\n'
    explanation += '\n'.join(f'{j+1}. ' + ' '.join(s['korean'] for s in block) for j, block in enumerate(blocks))
    questions.append(question(p, 'sequence', prompt, choices, answer, explanation))
reading.append(add('10월 모의고사 순서 (18~24·29~45번)', questions))
units.append(dict(name='모의고사 · 주제·요지·순서', desc='첨부한 10월 모의고사 · 21개 지문', indices=reading))

stop = set('the and that this those these with from have has had will would could should their there they them then than what when where which while because before after some same more most many much into just only also very even each such other first second third last part been being does dont doesnt cannot through about under over people things something anything everyone ourselves yourself myself sincerely grandma'.split())


def target_english(text):
    words = re.findall(r"[A-Za-z]+(?:[’'-][A-Za-z]+)*", text)
    candidates = [w for w in words if w.lower() not in stop and len(w) > 3]
    unique = [w for w in candidates if words.count(w) == 1]
    return max(unique or candidates or words, key=len)


def target_korean(text):
    # Keep a complete phrase, including its particles, so the answer restores the original exactly.
    tokens = re.findall(r'[가-힣]+', text)
    candidates = [w for w in tokens if len(w) >= 3 and w not in ['그것은', '그것이', '이것은', '우리는', '그들은', '여러분은', '자신의', '그들의', '우리의']]
    unique = [w for w in candidates if text.count(w) == 1]
    return max(unique or candidates or tokens, key=len)


for lang, label in [('english', '영어 빈칸'), ('korean', '해석 빈칸')]:
    indices = []
    pool = list(dict.fromkeys((target_english if lang == 'english' else target_korean)(s[lang]) for p in passages for s in p['sentences']))
    for p in passages:
        questions = []
        for i, s in enumerate(p['sentences']):
            answer = (target_english if lang == 'english' else target_korean)(s[lang])
            others = [x for x in pool if x.lower() != answer.lower()]
            start = (i * 7 + int(p['number'].split('-')[0])) % (len(others) - 4)
            choices = [answer] + others[start:start+4]
            blanked = s[lang].replace(answer, '__________', 1)
            prompt = f'{p["number"]}번 · {i+1}번째 문장 · {label}을 채우세요.'
            if lang == 'english':
                prompt += box('우리말 해석', s['korean']) + box('영어 빈칸', blanked)
            else:
                prompt += box('영어 원문', s['english']) + box('해석 빈칸', blanked)
            explanation = f'정답: {answer}\n영어: {s["english"]}\n해석: {s["korean"]}'
            q = question(p, lang + '-cloze', prompt, choices, answer, explanation, i + 1)
            q['cloze'] = dict(answer=answer, language=lang)
            questions.append(q)
        indices.append(add(f'10월 모의고사 {p["number"]}번 · 문장별 {label}', questions))
    units.append(dict(name=f'모의고사 · 문장별 {label}', desc='직접 입력·자동 채점 · 필요하면 보기 확인', indices=indices))

payload = dict(quiz=sets, titles=titles, units=units, topics=topics)
(ROOT / 'english/october-2026.js').write_text('// Generated by tools/build_english_october.py from reviewed PDF transcription.\nwindow.SEOIK_ENGLISH_OCTOBER = ' + json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + ';\n')
print(f'{len(sets)} sets, {sum(map(len, sets))} questions')
