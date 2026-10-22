/* Browser contract tests use an explicit fake API host; no Azure services are simulated as verified. */
const fs=require('node:fs');
const http=require('node:http');
const path=require('node:path');
const assert=require('node:assert/strict');
const {chromium}=require(process.env.VICA_PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
function fakeHost(){
  const clone=v=>JSON.parse(JSON.stringify(v));
  const state={me:null,apps:[],configs:{},calls:[],next:1};window.fixtureState=state;
  const scopes=['acquisition','funnel','overview','documents','financials','risk','memo','decision','policy'];
  function bodyFor(c){return clone(c);}
  function handle(m){
    state.calls.push({path:m.path,method:m.method||'GET',body:m.body});
    if(m.path==='/configuration')return Object.fromEntries(scopes.map(s=>[s,clone(state.configs[s]||{version:0,data:{}})]));
    if(m.path.startsWith('/configuration/')){if(!state.me.roles.includes('Admin'))throw Error('Role does not permit this action');const key=m.path.split('/').at(-1),previous=state.configs[key]?.version||0;if(m.body.expected_version!==previous)throw Error('Configuration changed. Refresh before saving.');return clone(state.configs[key]={version:previous+1,data:m.body.data});}
    if(m.path==='/policy')return {version:'PENDING-CONFIRMATION',status:'pending_confirmation',source:'Bank policy confirmation required',rules:[]};
    if(m.path==='/applications'){
      if(m.method==='POST'){const c={...m.body,id:'case-'+state.next++,version:1,created_at:new Date().toISOString(),owner:state.me.subject,members:[state.me.subject],status:'draft',clearances:{},prepared_by:null,credit_reviewer:null,current_assessment:null,conditions:[],documents:[],fields:[],notes:[],narratives:[],assessments:[],tasks:[],audits:[],events:[],decision:null};state.apps.push(c);return bodyFor(c);}
      return state.apps.filter(c=>state.me.roles.includes('Admin')||c.members.includes(state.me.subject)).map(bodyFor);
    }
    const parts=m.path.split('/').filter(Boolean),c=state.apps.find(c=>c.id===parts[1]);if(!c)throw Error('Application not found');
    if(parts.length===2)return bodyFor(c);
    const b=m.body||{},kind=parts[2],id=parts[3],action=parts[4];
    const bump=()=>{c.version++;return bodyFor(c);};
    if(kind==='members'){assertVersion(c,b);c.members.push(b.subject);return bump();}
    if(kind==='documents'){
      if(m.file){const doc={id:'doc-'+state.next++,version:1,filename:m.file.name,mime:m.file.type,state:'processed',document_type:'other',reviewed:false,page_count:1};c.documents.push(doc);c.status='data_review';bump();return {document_id:doc.id,state:'queued'};}
      const d=c.documents.find(d=>d.id===id);if(!d)throw Error('Document not found');
      if(action==='pages')return [{page:1,text:'شركة الاختبار — السجل التجاري — إيرادات 1000000'}];
      if(action==='content')return new Blob(['شركة الاختبار'],{type:'text/plain'});
      if(action==='review'){assertVersion(d,b);Object.assign(d,b,{reviewed:true,version:d.version+1});bump();return clone(d);}
    }
    if(kind==='fields'){
      if(!id){const f={...b,id:'field-'+state.next++,version:1,reviewed:false,active:false};c.fields.push(f);bump();return clone(f);}
      const f=c.fields.find(f=>f.id===id);assertVersion(f,b);Object.assign(f,{value:b.value,reviewed:true,active:true,version:f.version+1});bump();return clone(f);
    }
    if(kind==='assessments'){assertVersion(c,b);const a={id:'assessment-'+state.next++,version:1,period:b.period,values:{revenue:'1000000',cash_available:'300000'},financial:{metrics:{revenue:'1000000',dscr:'1.5',downside_dscr:'1.2',current_ratio:'1.8',debt_to_equity:'1.0',debt_service:'200000'}},checks:[{description:'Fixture rule',rule_id:'TEST-1',source:'Fixture only',outcome:'pass'}],blockers:[]};c.assessments.push(a);c.current_assessment=a.id;c.prepared_by=state.me.subject;c.status='credit_assessment';bump();return clone(a);}
    if(kind==='narratives'){
      if(!id){assertVersion(c,b);const n={id:'narrative-'+state.next++,version:1,created_at:new Date().toISOString(),origin:b.text?'human':'azure_ai',text:b.text||'1. Executive summary\nFixture analysis: reviewed source inputs.\n\n2. Evidence and outstanding actions\nSource: doc-2. Independent review required.',reviewed:false};c.narratives.push(n);return clone(n);}
      const n=c.narratives.find(n=>n.id===id);assertVersion(n,b);Object.assign(n,{text:b.text,reviewed:true,version:n.version+1});c.current_narrative=n.id;c.prepared_by=state.me.subject;bump();return clone(n);
    }
    if(kind==='transitions'){assertVersion(c,b);if(b.action==='submit'){if(!c.current_narrative)throw Error('Reviewed narrative required');c.status='credit_review';}if(b.action==='review_accept'){if(state.me.subject===c.prepared_by)throw Error('Independent reviewer must differ from preparing officer');c.credit_reviewer=state.me.subject;c.status='pending_decision';}if(b.action==='return')c.status='data_review';return bump();}
    if(kind==='decisions'){assertVersion(c,b);if(!state.me.roles.includes('Approver')||c.status!=='pending_decision'||[c.prepared_by,c.credit_reviewer].includes(state.me.subject))throw Error('Independent approver and completed review required');c.decision={...b,by:state.me.subject,at:new Date().toISOString()};c.status=b.decision;c.conditions=b.conditions.map((text,i)=>({id:'condition-'+i,text,status:'open'}));return bump();}
    if(kind==='clearances'){assertVersion(c,b);c.clearances[b.category]={...b,reviewer:state.me.subject};return bump();}
    if(kind==='notes'){const n={...b,id:'note-'+state.next++,author:state.me.subject};c.notes.push(n);return clone(n);}
    if(kind==='reports')return new Blob(['Fixture report'],{type:'text/html'});
    throw Error('Unimplemented fixture endpoint: '+m.path);
  }
  function assertVersion(record,body){if(record.version!==body.expected_version)throw Error('Version changed. Refresh before applying changes.');}
  window.addEventListener('message',event=>{
    const iframe=document.querySelector('iframe');if(event.origin!==location.origin||event.source!==iframe.contentWindow)return;
    const m=event.data,send=data=>iframe.contentWindow.postMessage(data,location.origin);
    if(m.type==='vica:ready'){send({type:'vica:session',local:true,me:state.me,error:state.me?'':'Sign in required'});return;}
    if(m.type==='vica:login'){state.me={subject:m.subject,roles:[m.role],mode:'local'};send({type:'vica:session',local:true,me:state.me});return;}
    if(m.type==='vica:request'){try{const result=handle(m);send({type:'vica:response',id:m.id,result});}catch(error){send({type:'vica:response',id:m.id,error:error.message});}}
  });
}
(async()=>{
  const server=http.createServer((request,response)=>{
    const pathname=new URL(request.url,'http://localhost').pathname;
    if(pathname==='/test-host.html'){response.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});response.end('<!doctype html><style>body{margin:0}iframe{border:0;width:100%;height:100vh}</style><script>('+fakeHost.toString()+')()</script><iframe src="/vica-review.html?connected=1"></iframe>');return;}
    const files={'/vica-review.html':'vica-review.html','/vica-live.js':'vica-live.js','/vica-live.css':'vica-live.css'};
    if(!files[pathname]){response.writeHead(404);response.end();return;}
    response.writeHead(200,{'Content-Type':pathname.endsWith('.js')?'text/javascript; charset=utf-8':pathname.endsWith('.css')?'text/css; charset=utf-8':'text/html; charset=utf-8'});response.end(fs.readFileSync(path.join(root,'04_Frontend/public',files[pathname])));
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const browser=await chromium.launch({headless:true,...(process.env.VICA_CHROME?{executablePath:process.env.VICA_CHROME}:{})});
  try{
    const page=await browser.newPage({viewport:{width:1360,height:1000}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto('http://127.0.0.1:'+server.address().port+'/test-host.html');const f=page.frameLocator('iframe');
    const clickAction=(action)=>f.locator('[data-live-action="'+action+'"]').first().click();
    const nav=(screen)=>f.locator('.vc-nav [data-screen="'+screen+'"]').click();
    const tab=(name)=>f.locator('[data-live-action="tab"][data-tab="'+name+'"]').click();
    const login=async(role,subject)=>{await f.locator('[name="token"]').fill('fixture-token-not-a-live-secret');await f.locator('[name="role"]').selectOption(role);await f.locator('[name="subject"]').fill(subject);await f.locator('[data-live-form="login"] button[type="submit"]').click();await f.locator('[data-live-action="new-case"]').waitFor();};
    assert.equal(await f.locator('text=Al-Noor Industrial Logistics LLC').count(),0);await login('Admin','demo-admin');
    const passed=['No synthetic sample dossiers in connected sign-in or empty portfolio'];
    await clickAction('new-case');await f.locator('[name="borrower_name"]').fill('شركة الاختبار للتجارة');await f.locator('[name="requested_amount"]').fill('250000');await f.locator('[data-live-form="create-case"] button[type="submit"]').click();await f.locator('.vc-case-banner h1').waitFor();assert.match(await f.locator('.vc-case-banner h1').innerText(),/شركة الاختبار/);
    for(const subject of ['demo-reviewer','demo-approver']){await f.locator('[data-live-form="member"] [name="subject"]').fill(subject);await f.locator('[data-live-form="member"] button').click();await f.locator('.vc-case-banner h1').waitFor();}
    passed.push('Application creation, Arabic borrower name and case membership API contracts');
    await tab('documents');await f.locator('[name="files"]').setInputFiles({name:'registration-arabic.txt',mimeType:'text/plain',buffer:Buffer.from('شركة الاختبار — السجل التجاري')});await f.locator('[data-live-form="upload"] button').click();await f.locator('[data-live-action="view-document"]').waitFor();await clickAction('view-document');assert.match(await f.locator('.live-source').innerText(),/السجل التجاري/);await f.locator('[name="document_type"]').selectOption('registration');await f.locator('[data-live-form="review-document"] [name="rationale"]').fill('Entity identity and source document checked.');await f.locator('[data-live-form="review-document"] button').click();await f.locator('[name="files"]').waitFor();
    const manual=f.locator('[data-live-form="field"]');await manual.locator('[name="name"]').selectOption('revenue');await manual.locator('[name="value"]').fill('1000000');await manual.locator('[name="rationale"]').fill('Documented fixture figure for the selected period.');await manual.locator('button').click();const review=f.locator('[data-live-form="review-field"]').first();await review.waitFor();await review.locator('[name="rationale"]').fill('Confirmed period and base units.');await review.locator('button').click();await f.locator('[data-live-form="review-field"] .vc-badge.good').waitFor();passed.push('Document upload, Arabic source viewing, classification and reviewed field requests');
    await tab('financials');await f.locator('[data-live-form="assess"] [name="period"]').fill('FY 2025');await f.locator('[name="confirmed"]').check();await f.locator('[data-live-form="assess"] button').click();await f.locator('text=Ready for independent review, subject to the workflow gates.').waitFor();passed.push('Assessment calculation request and confirmed metrics rendering');
    await tab('risk');await f.locator('[name="cashShock"]').fill('20');await f.locator('[name="serviceShock"]').fill('0');await f.locator('[data-live-form="stress"] button').click();assert.match(await f.locator('#live-content').innerText(),/1\.20×/);passed.push('Stress calculation uses assessment cash and debt-service figures');
    await tab('memo');await clickAction('generate-memo');await f.locator('#live-memo-text').waitFor();await page.waitForTimeout(50);const memo=await f.locator('#live-memo-text').inputValue();assert.match(memo,/Executive summary/);await f.locator('#live-memo-text').fill(memo+'\nAnalyst review: مراجعة المحلل.');await clickAction('save-memo');await f.locator('#live-message').filter({hasText:'saved server-side'}).waitFor();await clickAction('review-memo');await f.locator('#live-content').filter({hasText:'Reviewed · human'}).waitFor();passed.push('AI draft request, Arabic analyst edits, server draft save and narrative confirmation');
    await tab('decision');const transition=f.locator('[data-live-form="transition"]');await transition.locator('[name="rationale"]').fill('Ready for independent reviewer.');await transition.locator('button').click();await f.locator('.vc-case-meta').filter({hasText:'credit review'}).waitFor();await transition.locator('[name="action"]').selectOption('review_accept');await transition.locator('[name="rationale"]').fill('Attempt self review must be rejected.');await transition.locator('button').click();await f.locator('#live-message').filter({hasText:'must differ'}).waitFor();passed.push('Independent review server rejection is displayed without a fake approval');
    await nav('acquisition');await f.locator('[data-live-action="configure"][data-scope="acquisition"]').click();await clickAction('indicator-add');const last=f.locator('.live-indicator').last();await last.locator('input[name^="k-name-"]').fill('Cases requiring credit review');await last.locator('select[name^="k-type-"]').selectOption('KRI');await last.locator('select[name^="k-metric-"]').selectOption('review_count');await last.locator('select[name^="k-direction-"]').selectOption('lower');await last.locator('input[name^="k-warning-"]').fill('5');await last.locator('input[name^="k-critical-"]').fill('10');await f.locator('[name="cfg-rationale"]').fill('Add a credit review queue indicator.');await f.locator('[data-live-form="configuration"] button[type="submit"]').click();await f.locator('[data-live-metric]').filter({hasText:'Cases requiring credit review'}).waitFor();
    await f.locator('[data-live-action="configure"][data-scope="acquisition"]').click();await f.locator('.live-indicator').first().locator('[data-live-action="indicator-remove"]').click();await f.locator('[name="cfg-rationale"]').fill('Remove an unnecessary acquisition KPI.');await f.locator('[data-live-form="configuration"] button[type="submit"]').click();assert.equal(await f.locator('[data-live-metric]').count(),4);passed.push('Add and remove KPI/KRI definitions and save shared configuration');
    await page.evaluate(()=>document.querySelector('iframe').contentWindow.location.reload());await f.locator('[data-live-action="new-case"]').waitFor();assert.equal(await f.locator('[data-live-metric]').count(),4);assert.match(await f.locator('#live-content').innerText(),/Cases requiring credit review/);passed.push('Configuration is reloaded from the server after page reload');
    await nav('policy');const cfgButtons=f.locator('[data-live-action="configure"]');assert.equal(await cfgButtons.count(),8);passed.push('All dashboards and six cockpit sections have Manage KPIs/KRIs');
    await clickAction('session');await login('Reviewer','demo-reviewer');await nav('queue');await clickAction('open-case');await tab('decision');await f.locator('[data-live-form="transition"] [name="action"]').selectOption('review_accept');await f.locator('[data-live-form="transition"] [name="rationale"]').fill('Independent credit assessment completed.');await f.locator('[data-live-form="transition"] button').click();await f.locator('.vc-case-meta').filter({hasText:'pending decision'}).waitFor();
    await clickAction('session');await login('Approver','demo-approver');await nav('queue');await clickAction('open-case');await tab('decision');await f.locator('[data-live-form="decision"] [name="rationale"]').fill('Conditional approval after independent assessment.');await f.locator('[data-live-form="decision"] [name="conditions"]').fill('Verify the sponsor undertaking.');await f.locator('[data-live-form="decision"] button').click();await f.locator('.vc-case-meta').filter({hasText:'conditional'}).waitFor();passed.push('Separate reviewer and approver identities submit versioned workflow requests');
    const output=process.env.VICA_QA_OUTPUT||path.resolve(root,'..','outputs','azure-final-qa');fs.mkdirSync(output,{recursive:true});await page.screenshot({path:path.join(output,'connected-decision.png'),fullPage:true});
    for(const width of [1024,360,320]){await page.setViewportSize({width,height:900});for(const t of ['overview','documents','financials','risk','memo','decision']){await tab(t);const overflow=await page.frames()[1].evaluate(()=>document.documentElement.scrollWidth>innerWidth);assert.equal(overflow,false,'Overflow '+width+' '+t);}}
    passed.push('Six cockpit sections fit 1024, 360 and 320 pixel widths');assert.deepEqual(errors,[]);
    const calls=await page.evaluate(()=>window.fixtureState.calls);assert(calls.some(c=>c.path.endsWith('/decisions')));const result={test_type:'Browser API-contract tests with explicit fixture server; not an Azure/provider integration test',passed,errors,request_count:calls.length};fs.writeFileSync(path.join(root,'10_Verification/connected-browser-results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error.stack);process.exit(1);});
