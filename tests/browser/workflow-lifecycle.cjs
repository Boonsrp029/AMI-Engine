/* Real FastAPI + SQLite + owned-runner browser acceptance. Fixed callbacks only. */
const fs=require('node:fs'),fsp=require('node:fs/promises'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.AMI_PLAYWRIGHT_MODULE||'playwright');
const root=process.env.AMI_E_FIXTURE_ROOT,base=process.env.AMI_E_BASE_URL;
if(!root||!base||!/^http:\/\/127\.0\.0\.1:\d+$/.test(base))throw Error('Explicit synthetic fixture directory and localhost URL required');
assert.equal(fs.readFileSync(path.join(root,'fixture-kind.txt'),'utf8').replace(/\r\n/g,'\n'),'AMI E synthetic fixture v1\n');
const session=JSON.parse(fs.readFileSync(path.join(root,'session.json'),'utf8'));assert.equal(session.synthetic_only,true);assert.equal(session.actual_provider_calls,0);
const headers={'X-Pilot-Token':session.token,'Content-Type':'application/json'};
async function api(route,method='GET',body,status=200){const res=await fetch(base+route,{method,headers,body:body===undefined?undefined:JSON.stringify(body)});assert.equal(res.status,status,`${method} ${route}: ${await (res.status===status?Promise.resolve(''):res.text())}`);return res}
async function data(route){return (await api(route)).json()}
async function until(fn){const deadline=Date.now()+60000;while(Date.now()<deadline){const value=await fn();if(value)return value;await new Promise(r=>setTimeout(r,100))}throw Error('Synthetic persisted-state condition was not reached')}
async function release(id,stage,fail=false){await api(`/__fixture/runs/${id}/release`,'POST',{stage,fail})}
async function gates(id,stage){return until(async()=>{const g=await data(`/__fixture/runs/${id}`);return g.entered.includes(stage)&&g})}
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.AMI_BROWSER_CHANNEL||'msedge'}),context=await browser.newContext({acceptDownloads:true}),page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));let checks=0;
 async function check(name,fn){await fn();checks++;console.log('PASS '+name)}
 async function refresh(){await page.locator('#refresh-task').click();await page.waitForFunction(()=>document.querySelector('#workspace').getAttribute('aria-busy')==='false')}
 async function status(value){const id=new URL(page.url()).searchParams.get('run');await until(async()=>{const row=await data(`/api/runs/${id}`);return value.startsWith('revision ')?row.revision===Number(value.split(' ')[1]):row.status===(value==='Ready for review'?'needs_review':value)});await refresh();await page.waitForFunction(value=>document.querySelector('#notice').textContent.includes(value),value);}
 async function submit(question,count=3){
  await page.locator('#workflow').selectOption('bounded_subtasks');await page.locator('#query').fill(question);
  while(await page.locator('#plan-branches > fieldset').count()<count)await page.locator('#add-branch').click();
  while(await page.locator('#plan-branches > fieldset').count()>count)await page.locator('#remove-branch').click();
  for(let i=0;i<count;i++){await page.locator('.branch-query').nth(i).fill('Fictional district '+(i+1)+' units in 2020');await page.locator('.branch-dependencies').nth(i).fill(i===2?'s01':'');await page.locator('.branch-required').nth(i).check()}
  const result=page.waitForResponse(r=>r.url()===base+'/api/runs/subtasks'&&r.request().method()==='POST');await page.locator('#start').click();const row=await(await result).json();assert.ok(row.id);await page.waitForFunction(id=>new URL(location.href).searchParams.get('run')===id,row.id);return row.id;
 }
 async function download(){const pending=page.waitForEvent('download');await page.locator('#export').click();const file=await pending;return fsp.readFile(await file.path())}
 try{
  await page.goto(base);await page.waitForFunction(()=>!document.querySelector('#start').disabled);
  await check('default request uses the real sequential route and still awaits approval',async()=>{
   assert.equal(await page.locator('#workflow').inputValue(),'sequential');await page.locator('#query').fill('Fictional district one in 2020');const reply=page.waitForResponse(r=>r.url()===base+'/api/runs'&&r.request().method()==='POST');await page.locator('#start').click();const {id}=await(await reply).json();await page.waitForFunction(id=>new URL(location.href).searchParams.get('run')===id,id);await status('Ready for review');assert.ok(await page.locator('#export').isDisabled());
  });
  const id=await submit('Compare three fictional districts in 2020');
  await check('real persisted independent branches run while dependency waits',async()=>{
   await until(async()=>{const s=await data(`/api/runs/${id}/progress`);return s.progress.branches.map(b=>b.status).join(',')==='running,running,waiting_on_dependency'});await refresh();
   assert.equal(await page.locator('.branch[data-status="running"]').count(),2);assert.equal(await page.locator('.branch[data-status="waiting_on_dependency"]').count(),1);assert.ok(await page.locator('#approve').isDisabled());assert.ok(await page.locator('#export').isDisabled());
   await page.locator('[data-subtask-id="s03"] summary').click();assert.match(await page.locator('[data-subtask-id="s03"]').innerText(),/Depends on: s01/);
  });
  await check('completed retrieval does not imply a draft, safety result or approval',async()=>{
   await release(id,'s01');await release(id,'s02');await gates(id,'s03');await release(id,'s03');await gates(id,'composition');await until(async()=>(await data(`/api/runs/${id}/progress`)).progress.phase==='composition');await refresh();
   assert.match(await page.locator('#subtask-summary').innerText(),/3 of 3/);assert.match(await page.locator('#subtask-consequence').innerText(),/preparing the brief/);assert.match(await page.locator('#brief').innerText(),/No draft/);assert.ok(await page.locator('#approve').isDisabled());
   await release(id,'composition');await gates(id,'safety');await refresh();assert.match(await page.locator('#subtask-consequence').innerText(),/checking the brief/);assert.ok(await page.locator('#export').isDisabled());await release(id,'safety');await status('Ready for review');
  });
  let original,final;
  await check('source inspection, exact revision approval and byte-identical cached export',async()=>{
   const summaries=page.locator('#sources summary');assert.equal(await summaries.count(),3);for(const s of await summaries.all())await s.click();assert.match(await page.locator('#sources').innerText(),/PDF page 1/);assert.match(await page.locator('#sources').innerText(),/PDF page 7/);
   await page.locator('#reviewer').fill('synthetic-E');await page.locator('#support').check();await page.locator('#approve').click();await status('approved');original=await download();assert.ok(original.includes(Buffer.from('PDF page 7')));assert.deepEqual(await download(),original);
  });
  await check('editing invalidates approval, blocks stale review/export and retains review history',async()=>{
   await page.getByText('Correct this draft',{exact:true}).click();await page.locator('#edit-title').fill('Synthetic corrected revision');await refresh();assert.equal(await page.locator('#edit-title').inputValue(),'Synthetic corrected revision');assert.ok(await page.locator('#export').isDisabled());await page.locator('#save').click();await status('revision 2');
   await api(`/api/runs/${id}/review`,'POST',{revision:1,decision:'approve',reviewer:'synthetic-E',support_confirmed:true},409);await api(`/api/runs/${id}/export`,'GET',undefined,409);
   await page.locator('#reject').click();await status('rejected');assert.ok(await page.locator('#export').isDisabled());await page.locator('#edit-title').fill('Synthetic final revision');await page.locator('#save').click();await status('revision 3');await page.locator('#support').check();await page.locator('#approve').click();await status('approved');final=await download();assert.notDeepEqual(final,original);
   const stored=await data(`/api/runs/${id}`);assert.equal(stored.revision,3);assert.equal(stored.reviews.length,3);
  });
  await check('page refresh reconstructs approved revision without resubmission',async()=>{
   const before=(await data('/api/runs')).length;await page.reload();await page.waitForFunction(()=>!document.querySelector('#export').disabled);assert.deepEqual(await download(),final);assert.equal((await data('/api/runs')).length,before);assert.match(await page.locator('#notice').innerText(),/revision 3/);assert.equal(await page.evaluate(()=>sessionStorage.length+localStorage.length),0);
   if(process.env.AMI_UI_SCREENSHOT)await page.screenshot({path:process.env.AMI_UI_SCREENSHOT,fullPage:true});
  });
  await check('real authentication failure disables stale actions; reconnect retains exact approved revision',async()=>{
   const before=(await data('/api/runs')).length;await page.evaluate(()=>{token='invalid-synthetic-token'});await page.locator('#refresh-task').click();await page.waitForFunction(()=>!document.querySelector('#access').hidden);assert.ok(await page.locator('#export').isDisabled());assert.match(await page.locator('#notice').innerText(),/revision 3/);
   await page.locator('#access-token').fill(session.token);await page.locator('#connect').click();await page.waitForFunction(()=>document.querySelector('#access').hidden&&!document.querySelector('#export').disabled);assert.deepEqual(await download(),final);assert.equal((await data('/api/runs')).length,before);assert.equal(await page.evaluate(()=>sessionStorage.length+localStorage.length),0);
  });
  const failed=await submit('Synthetic required branch failure',2);await gates(failed,'s01');
  const queued=await submit('Synthetic queued cancellation',2);
  await check('queued plan is visible and cancellable without an attempt',async()=>{
   await status('queued');assert.equal(await page.locator('.branch[data-status="queued"]').count(),2);await page.locator('#cancel').click();await status('interrupted');assert.match(await page.locator('#notice').innerText(),/Task canceled/);assert.equal(await page.locator('.branch[data-status="cancelled"]').count(),2);assert.ok(await page.locator('#approve').isDisabled());assert.equal((await data(`/__fixture/runs/${queued}`)).attempt_id,null);
  });
  await page.locator(`#history [data-run-id="${failed}"]`).click();await release(failed,'s01',true);
  await check('required failure is explicit; retry retains history and active cancellation prevents readiness',async()=>{
   await status('failed');assert.match(await page.locator('#subtask-consequence').innerText(),/Required work did not complete/);assert.ok(await page.locator('#export').isDisabled());const old=(await data(`/__fixture/runs/${failed}`)).attempt_id;
   await page.locator('#retry').click();await until(async()=>{const s=await data(`/api/runs/${failed}/progress`);return s.progress.attempt_id&&s.progress.attempt_id!==old&&s.progress.branches.length===2&&s.progress.branches.every(b=>b.status==='running')});await refresh();assert.equal(await page.locator('.branch[data-status="running"]').count(),2);await page.locator('#cancel').click();await status('interrupted');assert.equal(await page.locator('.branch[data-status="cancelled"]').count(),2);assert.ok(await page.locator('#approve').isDisabled());assert.ok(await page.locator('#export').isDisabled());assert.equal((await data(`/api/runs/${failed}`)).draft,null);
  });
  await check('lost bounded POST confirmation recovers through real request lookup without duplicate work',async()=>{
   const before=(await data('/api/runs')).length;let admitted=null,posts=0;
   await page.locator('#workflow').selectOption('bounded_subtasks');await page.locator('#query').fill('Synthetic lost confirmation after durable admission');
   const route=base+'/api/runs/subtasks';await page.route(route,async intercept=>{posts++;const response=await intercept.fetch();assert.equal(response.status(),202);admitted=await response.json();await intercept.abort('failed')},{times:1});
   await page.locator('#start').click();await page.waitForFunction(()=>document.querySelector('#submission-status').textContent.includes('unconfirmed'));assert.ok(admitted?.id);const pending=await page.evaluate(()=>JSON.parse(sessionStorage.getItem('ami.pending-submission.v1')));
   assert.deepEqual(await data('/api/runs/by-request/'+pending.request_key),{id:admitted.id,workflow:'bounded_subtasks'});
   await page.reload();await page.waitForFunction(id=>new URL(location.href).searchParams.get('run')===id,admitted.id);await page.waitForFunction(()=>!document.querySelector('#cancel').hidden&&!document.querySelector('#cancel').disabled);assert.equal(posts,1);assert.equal((await data('/api/runs')).length,before+1);assert.equal(await page.evaluate(()=>sessionStorage.length),0);
   await page.locator('#cancel').click();await status('interrupted');assert.ok(await page.locator('#export').isDisabled());
  });
  assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'passed',checks,actual_provider_calls:0,proof:'real HTTP/SQLite/owned runner with fixed callbacks; synthetic review only'}));
 }finally{await browser.close();for(const row of await data('/api/runs'))if(['queued','running'].includes(row.status))await api(`/api/runs/${row.id}/cancel`,'POST')}
})().catch(e=>{console.error(e);process.exitCode=1});
