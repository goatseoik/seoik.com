const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname, '..');
const source = JSON.parse(fs.readFileSync(path.join(root, 'english/october-2026-source.json'), 'utf8'));
const context = {window:{}};
vm.runInNewContext(fs.readFileSync(path.join(root, 'english/october-2026.js'), 'utf8'), context);
const extra = JSON.parse(JSON.stringify(context.window.SEOIK_ENGLISH_OCTOBER));

test('all 21 passage translations follow the newly supplied official interpretation PDF', () => {
  const reference=JSON.parse(fs.readFileSync(path.join(root,'english/october-2026-translation-reference.json'),'utf8'));
  const norm=text=>text.normalize('NFKC').replace(/\s+/g,'');
  assert.match(source.translation_source,/해석\.pdf/);
  assert.equal(reference.source,source.translation_source);
  assert.deepEqual(Object.keys(reference.passages),source.passages.map(p=>p.number));
  for(const p of source.passages) {
    let expected=norm(reference.passages[p.number]);
    if(p.number==='18') expected=expected.replace(/^Ms\.Palmer귀하/,'').replace(/KarenWhitfield드림$/,'');
    if(p.number==='30') expected=expected.replace('감소(→증가)','증가');
    if(p.number==='35') expected=expected.replace(/\(개인들은.*?있다\.\)/,'');
    if(p.number==='40') expected=expected.split('\uf000')[0];
    if(p.number==='41-42') expected=expected.replace('영향력이없고(→영향력이크고)','영향력이크고');
    expected=expected.replace(/\([A-Da-e]\)/g,'');
    assert.equal(norm(p.sentences.map(s=>s.korean).join(' ')),expected,p.number+'번 해석');
  }
  const story=source.passages.find(p=>p.number==='43-45').sentences;
  assert.match(story[0].korean,/자신의 학교 복도/);
  assert.match(story[12].korean,/그녀\(Emily\)의 목소리가 떨렸다/);
  assert.match(story[21].korean,/엉망진창 속에서 아름다움을 찾는 지혜/);
});

test('October English covers the requested passages and every aligned sentence in both languages', () => {
  assert.deepEqual(source.passages.map(p=>p.number), ['18','19','20','21','22','23','24','29','30','31','32','33','34','35','36','37','38','39','40','41-42','43-45']);
  assert.equal(source.passages.reduce((n,p)=>n+p.sentences.length,0),184);
  assert.equal(extra.quiz.length,45);
  assert.equal(extra.quiz.flat().length,431);
  for (const p of source.passages) {
    assert(p.topic && p.summary);
    const all = extra.quiz.flat().filter(q=>q.passage===p.number);
    for (const kind of ['topic','gist','sequence']) assert.equal(all.filter(q=>q.kind===kind).length,1);
    for (const [i,s] of p.sentences.entries()) {
      assert(s.english && s.korean);
      assert.doesNotMatch(s.english,/요지|Youtube|◆|→/);
      for (const lang of ['english','korean']) {
        const questions=all.filter(q=>q.kind===lang+'-cloze' && q.sentence===i+1);
        assert.equal(questions.length,1);
        const q=questions[0], answer=q.choices[q.correct];
        assert.equal(answer,q.cloze.answer);
        assert(s[lang].includes(answer));
        assert(q.q.includes(s[lang].replace(answer,'__________').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#x27;')));
        assert(q.explain.includes(s.english));
        assert(q.explain.includes(s.korean));
      }
    }
  }
});

test('all generated sets have usable choices and are reachable from the new units', () => {
  assert.deepEqual(extra.units.flatMap(u=>u.indices),extra.quiz.map((_,i)=>i));
  assert.equal(extra.titles.length,extra.quiz.length);
  for(const q of extra.quiz.flat()) {
    assert.equal(q.choices.length,5);
    assert.equal(new Set(q.choices).size,5);
    assert(q.correct>=0 && q.correct<5);
    assert(q.explain && q.source);
  }
  for(const p of source.passages) {
    const topic=extra.quiz[0].find(q=>q.passage===p.number);
    const gist=extra.quiz[1].find(q=>q.passage===p.number);
    assert.equal(topic.choices[topic.correct],p.topic);
    assert.equal(gist.choices[gist.correct],p.summary);
  }
});

test('sequence answers reconstruct the complete original paragraph order', () => {
  const decode=s=>s.replaceAll('&#x27;',"'").replaceAll('&quot;','"').replaceAll('&gt;','>').replaceAll('&lt;','<').replaceAll('&amp;','&');
  for(const q of extra.quiz[2]) {
    const p=source.passages.find(p=>p.number===q.passage);
    const boxes=[...q.q.matchAll(/class="mat-box">([\s\S]*?)<\/div>/g)].map(m=>decode(m[1]));
    const sequence=q.choices[q.correct].split(' → ').map(letter=>boxes['ABC'.indexOf(letter)+1]);
    assert.equal([boxes[0],...sequence].join(' '),p.sentences.map(s=>s.english).join(' '));
  }
});

test('paired notebook keeps every English sentence directly above its translation', () => {
  assert.equal(extra.notes.paired,true);
  assert.equal(extra.notes.sections.length,21);
  assert.equal(extra.units.filter(u=>u.notebook).length,1);
  assert.equal(extra.units.find(u=>u.notebook).indices.length,42);
  const decode=s=>s.replaceAll('&#x27;',"'").replaceAll('&quot;','"').replaceAll('&gt;','>').replaceAll('&lt;','<').replaceAll('&amp;','&');
  for(const [i,p] of source.passages.entries()) {
    const section=extra.notes.sections[i];
    assert.equal(section.passage,p.number);
    const pairs=[...section.html.matchAll(/<article class="en-note-pair" data-sentence="(\d+)">([\s\S]*?)<\/article>/g)];
    assert.equal(pairs.length,p.sentences.length);
    for(const [j,pair] of pairs.entries()) {
      assert.equal(Number(pair[1]),j+1);
      const lines=[...pair[2].matchAll(/<p class="[^"]*" lang="(en|ko)">([\s\S]*?)<\/p>/g)];
      assert.deepEqual(lines.map(l=>l[1]),['en','ko']);
      for(const [k,lang] of ['english','korean'].entries()) {
        assert.equal(decode(lines[k][2].replace(/<\/?mark[^>]*>/g,'')),p.sentences[j][lang]);
        assert.equal([...lines[k][2].matchAll(/<mark class="mk-hl">/g)].length,1);
      }
    }
  }
});

test('notebook list combines two legacy banks without changing saved set indices', () => {
  const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
  const helper=html.match(/function unitStudyIndices\(subject, unit\)\{[\s\S]*?\n\}/)[0];
  const ctx={}; vm.runInNewContext(helper,ctx);
  const subject={quiz:extra.quiz};
  const indices=ctx.unitStudyIndices(subject,extra.units.find(u=>u.notebook));
  assert.equal(indices.length,21);
  assert.deepEqual(Array.from(indices),Array.from({length:21},(_,i)=>i+3));
  for(const [i,p] of source.passages.entries()) {
    assert.equal(extra.quiz[3+i][0].passage,p.number);
    assert.equal(extra.quiz[24+i][0].passage,p.number);
  }
});

test('sentence cloze uses typed practice while mock exams retain sheet compatibility', () => {
  const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
  const normalize=html.match(/function normalizeEnglishCloze\(value\)\{[\s\S]*?\n\}/)[0];
  const routing=html.match(/function sheetUsable\(\)\{[\s\S]*?\n\}/)[0];
  const q=extra.quiz[3][0];
  const ctx={quizItems:[{sid:'en_f',set:0,q:0}],quizMode:'set',subjById:()=>({quiz:[[q]]})};
  vm.runInNewContext(normalize+'\n'+routing,ctx);
  assert.equal(ctx.sheetUsable(),false);
  ctx.quizMode='mock';
  assert.equal(ctx.sheetUsable(),true);
  assert.equal(ctx.normalizeEnglishCloze('  CON TRIBUTE  '),'contribute');
  assert.equal(ctx.normalizeEnglishCloze('기 여 하 다'),'기여하다');
  assert.equal(ctx.normalizeEnglishCloze('It’s'),"it's");
});
