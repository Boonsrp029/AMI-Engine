/* Synthetic HTTP/browser contracts. No analyst inference or real reviewer data. */
const http=require('node:http'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.AMI_PLAYWRIGHT_MODULE||'playwright');
const A='a'.repeat(32),B='b'.repeat(32),token='synthetic-browser-token-no-real-credential';
const source={title:'Synthetic source',content:'Synthetic supporting excerpt. <script>window.testPwned=1</script>',page_num:6,published:'2020-01-01',url:'https://example.invalid/source'};
function row(id=A){return {id,query:'Synthetic request '+id[0],request_key:id,status:'running',revision:1,draft:{title:'Synthetic brief',claims:[{text:'Synthetic supported claim.',source_ids:['s1']}],warnings:[]},sources:{s1:source},metrics:{},events:[{seq:1,kind:'attempt_started',payload:{attempt_id:'1'.repeat(32)}}],reviews:[]}}
function branch(id,status,required=true){return {subtask_id:id,operation:'retrieve',status,required,depends_on:id==='s04'?['s03']:[],reason:'none',derived:false,child_attempt_id:id,outcome:status==='completed'?'evidence':null}}
function snap(id=A){return {run:row(id),sequence:10,progress:{availability:'available',mode:'subtasks',attempt_id:'1'.repeat(32),plan_id:'p1',attempt_current:true,phase:'retrieval',branches:[branch('s01','completed'),branch('s02','completed'),branch('s03','running'),branch('s04','waiting_on_dependency'),branch('s05','queued')]}}}
const state={snapshots:{[A]:snap(A),[B]:snap(B)},failure:0,role:'operator',hold:null,pending:null,progressCalls:0,mutations:[],exports:0};
const html=fs.readFileSync(process.env.AMI_UI_FILE||path.resolve(__dirname,'../../src/pilot/index.html'),'utf8').replace('__PILOT_TOKEN__',token);
const server=http.createServer((req,res)=>{
 const route=new URL(req.url,'http://localhost').pathname;
 function json(value,code=200){res.writeHead(code,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(value))}
 if(route==='/'){res.writeHead(200,{'Content-Type':'text/html'});return res.end(html)}
 if(route==='/api/session')return json({role:state.role,identity:'synthetic-reviewer'});
 if(route==='/api/runs')return json(Object.values(state.snapshots).map(s=>s.run));
 const match=route.match(/^\/api\/runs\/([ab]{32})(?:\/(progress|export|review|draft))?$/);
 if(!match)return json({error:'not found'},404);
 const [_,id,action]=match;
 if(req.method!=='GET'){state.mutations.push({id,action});return json({synthetic:true})}
 if(action==='export'){state.exports++;res.writeHead(200,{'Content-Type':'text/markdown'});return res.end('SYNTHETIC CACHED APPROVED EXPORT\n')}
 if(action==='progress'){
  state.progressCalls++;
  if(state.failure)return json({error:'synthetic failure'},state.failure);
  if(state.hold===id){state.pending=()=>json(structuredClone(state.snapshots[id]));return}
  return json(state.snapshots[id]);
 }
 return json(state.snapshots[id].run);
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const port=server.address().port;
 const browser=await chromium.launch({headless:true,channel:process.env.AMI_BROWSER_CHANNEL||'msedge'});
 const context=await browser.newContext({acceptDownloads:true}),page=await context.newPage();
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.clock.install();
 let checks=0;
 async function check(name,fn){await fn();checks++;console.log('PASS '+name)}
 async function waitFor(fn,arg){await page.waitForFunction(fn,arg,{timeout:10000})}
 async function refresh(){const response=page.waitForResponse(r=>r.url().includes('/api/runs/')&&r.url().endsWith('/progress'));await page.locator('#refresh-task').click();await response;await waitFor(()=>document.querySelector('#workspace').getAttribute('aria-busy')==='false')}
 async function change(fn){fn(state.snapshots[A]);state.snapshots[A].sequence++;await refresh()}
 try{
  await page.goto(`http://127.0.0.1:${port}/?run=${A}&progress=1`);await waitFor(()=>document.querySelectorAll('.branch').length===5);
  await check('active states, dependency detail and no premature review/export',async()=>{
   assert.match(await page.locator('#subtask-summary').innerText(),/2 of 5 subtasks completed/);
   assert.ok(await page.locator('#approve').isDisabled());assert.ok(await page.locator('#export').isDisabled());
   await page.locator('[data-subtask-id="s04"] summary').click();assert.match(await page.locator('[data-subtask-id="s04"]').innerText(),/Depends on: s03/);
  });
  await check('source inspection preserves PDF page and escapes source text',async()=>{
   await page.locator('#sources summary').click();assert.match(await page.locator('#sources').innerText(),/PDF page 7/);assert.equal(await page.evaluate(()=>window.testPwned),undefined);
  });
  await check('completed branches still await composition and safety',async()=>{
   await change(s=>{s.progress.branches.forEach(b=>b.status='completed');s.progress.phase='composition'});
   assert.match(await page.locator('#subtask-consequence').innerText(),/preparing the brief/);assert.ok(await page.locator('#approve').isDisabled());
   await change(s=>s.progress.phase='safety');assert.match(await page.locator('#subtask-consequence').innerText(),/checking the brief/);
  });
  await check('same-revision polling preserves edits, review inputs and expanded details',async()=>{
   await change(s=>s.run.status='needs_review');await page.getByText('Correct this draft',{exact:true}).click();await page.locator('.claim-text').fill('Unsaved reviewer wording');await page.locator('#note').fill('Review note stays');await page.locator('#support').check();
   await page.locator('[data-subtask-id="s01"] summary').click();await refresh();
   assert.equal(await page.locator('.claim-text').inputValue(),'Unsaved reviewer wording');assert.equal(await page.locator('#note').inputValue(),'Review note stays');assert.ok(await page.locator('#support').isChecked());assert.ok(await page.locator('[data-subtask-id="s01"]').evaluate(e=>e.open));assert.ok(await page.locator('#approve').isDisabled());
  });
  await check('equal-sequence new revision creates a conflict without overwriting edits',async()=>{
   state.snapshots[A].run.revision=2;state.snapshots[A].run.draft.claims[0].text='New server revision';await refresh();
   assert.ok(await page.locator('#revision-conflict').isVisible());assert.equal(await page.locator('.claim-text').inputValue(),'Unsaved reviewer wording');assert.ok(await page.locator('#save').isDisabled());
   page.once('dialog',d=>d.accept());await page.locator('#reload-revision').click();await waitFor(()=>document.querySelector('.claim-text').value==='New server revision');assert.ok(await page.locator('#revision-conflict').isHidden());
  });
  await check('outage preserves view, disables actions and follows bounded backoff',async()=>{
   await page.locator('#note').fill('Offline note');state.failure=503;await page.locator('#refresh-task').click();await waitFor(()=>document.querySelector('#connection-status').textContent.includes('3 seconds'));
   assert.equal(await page.locator('#note').inputValue(),'Offline note');assert.ok(await page.locator('#approve').isDisabled());
   await page.clock.fastForward(3000);await waitFor(()=>document.querySelector('#connection-status').textContent.includes('6 seconds'));
   await page.clock.fastForward(6000);await waitFor(()=>document.querySelector('#connection-status').textContent.includes('12 seconds'));
   await page.clock.fastForward(12000);await waitFor(()=>document.querySelector('#connection-status').textContent.includes('30 seconds'));
   state.failure=0;await refresh();assert.equal(await page.locator('#note').inputValue(),'Offline note');
  });
  await check('auth failure stops polling and reconnects without storing credentials',async()=>{
   state.failure=403;await page.locator('#refresh-task').click();await waitFor(()=>!document.querySelector('#access').hidden);
   const calls=state.progressCalls;await page.clock.fastForward(60000);assert.equal(state.progressCalls,calls);
   state.failure=0;await page.locator('#access-token').fill(token);await page.locator('#connect').click();await waitFor(()=>document.querySelector('#access').hidden);await waitFor(()=>document.querySelector('#connection-status').textContent.startsWith('Updated'));
   assert.equal(await page.evaluate(()=>localStorage.length+sessionStorage.length),0);assert.ok(!page.url().includes(token));
  });
  await check('older watermark cannot roll back current revision',async()=>{
   const old=structuredClone(state.snapshots[A]);state.snapshots[A].sequence=1;state.snapshots[A].run.revision=0;await refresh();assert.match(await page.locator('#notice').innerText(),/revision 2/);state.snapshots[A]=old;
  });
  await check('optional failures expose partial coverage and required failures block readiness',async()=>{
   await change(s=>{s.progress.branches[4]={...branch('s05','failed',false),reason:'operation_failed'};s.run.draft.warnings=['Optional s05 is missing; brief is partial.']});
   assert.match(await page.locator('#subtask-consequence').innerText(),/Optional work did not complete/);
   await change(s=>{s.progress.branches[4].required=true;s.progress.branches[3]={...branch('s04','blocked'),reason:'dependency_failed'};s.run.status='failed'});
   assert.match(await page.locator('#subtask-consequence').innerText(),/Required work did not complete/);assert.ok(await page.locator('#approve').isDisabled());
  });
  await check('interruption is derived and queued retries label old branch history',async()=>{
   await change(s=>{s.progress.branches[4]={...branch('s05','cancelled'),reason:'interrupted',derived:true};s.run.status='interrupted'});
   assert.match(await page.locator('[data-subtask-id="s05"]').textContent(),/Recovered state after interruption/);
   await change(s=>{s.run.status='queued';s.progress.attempt_current=false});assert.match(await page.locator('#subtask-summary').innerText(),/Previous attempt \(retry queued\)/);
  });
  await check('unavailable projection is explicit, no-plan retains sequential view',async()=>{
   await change(s=>s.progress={availability:'unavailable',mode:'unavailable'});assert.match(await page.locator('#subtask-summary').innerText(),/progress unavailable/);
   await change(s=>s.progress={availability:'no_plan',mode:'sequential',plan_id:null});assert.ok(await page.locator('#subtask-panel').isHidden());
  });
  await check('switching tasks ignores a late response from the previous selection',async()=>{
   // Clear the retained review input deliberately before leaving the task.
   await page.locator('#note').fill('');await page.evaluate(()=>{reviewDirty=false;editorDirty=false});state.hold=A;await page.locator('#refresh-task').click();await waitFor(()=>true);
   while(!state.pending)await new Promise(resolve=>setImmediate(resolve));
   await page.locator('#history button').filter({hasText:'Synthetic request b'}).click();await waitFor(id=>document.querySelector('#notice').textContent.includes(id.slice(0,8)),B);
   state.hold=null;state.pending();state.pending=null;assert.match(await page.locator('#notice').innerText(),/bbbbbbbb/);
  });
  await check('refresh restores selected run and read-only opt-in flag',async()=>{
   await page.reload();await waitFor(()=>document.querySelector('#notice').textContent.includes('bbbbbbbb'));
   assert.ok(await page.locator('#show-subtasks').isChecked());assert.ok(page.url().includes('run='+B));assert.equal(await page.locator('#query').inputValue(),'Synthetic request b');
  });
  await check('approved export remains distinct and empty claims never enable approval',async()=>{
   state.snapshots[B].run.status='needs_review';state.snapshots[B].run.draft.claims=[];state.snapshots[B].sequence++;await refresh();assert.ok(await page.locator('#approve').isDisabled());
   state.snapshots[B].progress.branches.forEach(b=>b.status='completed');state.snapshots[B].run.status='approved';state.snapshots[B].run.draft.claims=[{text:'Synthetic checked',source_ids:['s1']}];state.snapshots[B].run.revision++;state.snapshots[B].sequence++;await refresh();
   const downloaded=page.waitForEvent('download');await page.locator('#export').click();const download=await downloaded;assert.equal(fs.readFileSync(await download.path(),'utf8'),'SYNTHETIC CACHED APPROVED EXPORT\n');
   assert.equal(state.exports,1);assert.equal(state.mutations.length,0);
  });
  await check('reader can inspect but cannot edit, review or export',async()=>{
   state.role='reader';await page.evaluate(()=>connect());
   for(const id of ['save','approve','reject','export','retry','cancel'])assert.ok(await page.locator('#'+id).isDisabled());
  });
  assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'passed',checks,model_calls:0,real_reviewer_data:false}));
  if(process.env.AMI_UI_SCREENSHOT){state.snapshots[B].run.status='needs_review';state.snapshots[B].progress.branches[3]={...branch('s04','failed',false),reason:'operation_failed'};state.snapshots[B].run.draft.warnings=['Optional s04 is missing; the brief has incomplete coverage.'];state.snapshots[B].sequence++;await refresh();await page.screenshot({path:process.env.AMI_UI_SCREENSHOT,fullPage:true})}
 }catch(error){console.error('UI diagnostics',await page.locator('#notice').textContent(),errors);throw error}finally{await context.close();await browser.close();await new Promise(resolve=>server.close(resolve))}
})().catch(e=>{console.error(e);server.close();process.exitCode=1});
