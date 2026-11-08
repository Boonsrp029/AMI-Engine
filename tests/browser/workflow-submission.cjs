/* Fixed HTTP responses test frontend admission/recovery only, not real scheduling. */
const http=require('node:http'),fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.AMI_PLAYWRIGHT_MODULE||'playwright');
const token='synthetic-only-workflow-token',storageKey='ami.pending-submission.v1';
const html=fs.readFileSync(process.env.AMI_UI_FILE||path.resolve(__dirname,'../../src/pilot/index.html'),'utf8').replace('__PILOT_TOKEN__',token);
const state={capability:true,runs:new Map(),posts:[],mode:'normal',hold:null};
function makeRun(body,workflow){return {id:(state.runs.size+1).toString(16).padStart(32,'0'),query:body.query,request_key:body.request_key,workflow,status:'queued',revision:0,draft:null,sources:{},metrics:{},events:[],reviews:[]}}
const server=http.createServer((req,res)=>{
 const route=new URL(req.url,'http://localhost').pathname;
 const json=(v,code=200)=>{res.writeHead(code,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(v))};
 if(route==='/'){res.writeHead(200,{'Content-Type':'text/html'});return res.end(html)}
 if(route==='/api/session')return json({role:'operator',identity:'synthetic-owner',capabilities:{bounded_subtasks:state.capability}});
 if(route==='/api/runs'&&req.method==='GET')return json([...state.runs.values()]);
 if(route.startsWith('/api/runs/by-request/')){const row=state.runs.get(decodeURIComponent(route.split('/').at(-1)));return row?json({id:row.id,workflow:row.workflow}):json({},404)}
 if(req.method==='POST'&&['/api/runs','/api/runs/subtasks'].includes(route)){
  let raw='';req.on('data',c=>raw+=c);req.on('end',()=>{
   const body=JSON.parse(raw),workflow=route.endsWith('/subtasks')?'bounded_subtasks':'sequential';state.posts.push({body,workflow});
   if(state.mode==='lost-before'){req.socket.destroy();return}
   let row=state.runs.get(body.request_key);
   if(row&&(row.query!==body.query||row.workflow!==workflow))return json({},409);
   if(!row){row=makeRun(body,workflow);state.runs.set(body.request_key,row)}
   if(state.mode==='lost-after'){req.socket.destroy();return}
   if(state.mode==='held'){state.hold=()=>json({id:row.id,workflow});return}
   return json({id:row.id,workflow});
  });return;
 }
 const match=route.match(/^\/api\/runs\/([a-f0-9]{32})(\/progress)?$/);
 if(match){const row=[...state.runs.values()].find(r=>r.id===match[1]);if(!row)return json({},404);return json(match[2]?{run:row,sequence:0,progress:{availability:'no_plan',mode:'sequential',plan_id:null,branches:[]}}:row)}
 json({},404);
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const url=`http://127.0.0.1:${server.address().port}/`;
 const browser=await chromium.launch({headless:true,channel:process.env.AMI_BROWSER_CHANNEL||'msedge'}),context=await browser.newContext(),page=await context.newPage();
 const errors=[];page.on('pageerror',e=>errors.push(e.message));let count=0;
 const wait=fn=>page.waitForFunction(fn,null,{timeout:10000});
 async function fillPlan(){await page.locator('.branch-query').nth(0).fill('Synthetic first evidence');await page.locator('.branch-query').nth(1).fill('Synthetic dependent evidence');await page.locator('.branch-dependencies').nth(1).fill('s01')}
 async function ready(){await wait(()=>!document.querySelector('#start').disabled)}
 async function check(name,fn){await fn();count++;console.log('PASS '+name)}
 try{
  await page.goto(url);await ready();
  await check('sequential default and capability-gated explicit bounded selection',async()=>{
   assert.equal(await page.locator('#workflow').inputValue(),'sequential');state.capability=false;await page.reload();await ready();assert.ok(await page.locator('#workflow option[value="bounded_subtasks"]').isDisabled());
   state.capability=true;await page.reload();await ready();await page.locator('#query').fill('Synthetic sequential question');await page.locator('#start').click();await wait(()=>document.querySelector('#notice').textContent.includes('revision 0'));assert.equal(state.posts.at(-1).workflow,'sequential');
   assert.equal(await page.evaluate(()=>sessionStorage.length),0);
  });
  await check('inflight locking prevents duplicate admission and freezes workflow',async()=>{
   state.mode='held';await page.locator('#workflow').selectOption('bounded_subtasks');await fillPlan();await page.locator('#query').fill('Synthetic bounded question');const before=state.posts.length;
   await page.locator('#start').click();await wait(()=>document.querySelector('#start').disabled);await page.evaluate(()=>document.querySelector('#start').click());assert.ok(await page.locator('#workflow').isDisabled());
   await page.waitForFunction(()=>document.querySelector('#submission-status')!==null);while(!state.hold)await new Promise(r=>setTimeout(r,10));assert.equal(state.posts.length,before+1);
   const meta=JSON.parse(await page.evaluate(k=>sessionStorage.getItem(k),storageKey));assert.deepEqual(Object.keys(meta).sort(),['request_key','version','workflow']);assert.equal(meta.workflow,'bounded_subtasks');assert.ok(!JSON.stringify(meta).includes('Synthetic bounded'));
   state.hold();state.hold=null;state.mode='normal';await ready();assert.ok(await page.locator('#show-subtasks').isChecked());assert.equal(await page.evaluate(()=>sessionStorage.length),0);
   assert.equal(state.posts.at(-1).body.subtasks.length,2);assert.deepEqual(state.posts.at(-1).body.subtasks[1].dependencies,['s01']);
  });
  await check('committed request with lost response survives refresh without another POST',async()=>{
   state.mode='lost-after';await page.locator('#query').fill('Synthetic committed lost confirmation');await page.locator('#start').click();await wait(()=>document.querySelector('#submission-status').textContent.includes('unconfirmed'));
   const before=state.posts.length,last=state.posts.at(-1),id=state.runs.get(last.body.request_key).id;state.mode='normal';await page.reload();await page.waitForFunction(id=>new URL(location.href).searchParams.get('run')===id,id);await ready();
   assert.equal(state.posts.length,before);assert.equal(new URL(page.url()).searchParams.get('run'),id);assert.equal(await page.evaluate(()=>sessionStorage.length),0);
  });
  await check('unadmitted request refresh performs lookup only then explicitly retries same key',async()=>{
   state.mode='lost-before';await fillPlan();await page.locator('#query').fill('Synthetic before admission');await page.locator('#start').click();await wait(()=>document.querySelector('#submission-status').textContent.includes('unconfirmed'));
   const before=state.posts.length,key=state.posts.at(-1).body.request_key;await page.reload();await ready();assert.equal(state.posts.length,before);assert.ok(await page.locator('#workflow').isDisabled());
   await page.locator('#query').fill('Synthetic before admission');await fillPlan();state.mode='normal';await page.locator('#start').click();await wait(()=>document.querySelector('#submission-status').textContent==='');await ready();assert.equal(state.posts.at(-1).body.request_key,key);assert.ok(state.runs.has(key));
  });
  await check('explicit bounded plan rejects missing queries and cyclic dependencies before admission',async()=>{
   await page.locator('#workflow').selectOption('bounded_subtasks');const before=state.posts.length;await page.locator('.branch-query').nth(0).fill('');await page.locator('#start').click();await wait(()=>document.querySelector('#notice').textContent.includes('Each retrieval branch'));assert.equal(state.posts.length,before);
   await fillPlan();await page.locator('.branch-dependencies').nth(0).fill('s02');await page.locator('#start').click();await wait(()=>document.querySelector('#notice').textContent.includes('cycle'));assert.equal(state.posts.length,before);assert.equal(await page.evaluate(()=>sessionStorage.length),0);
  });
  await check('unreadable pending identity blocks creation rather than inventing another key',async()=>{
   await page.evaluate(k=>sessionStorage.setItem(k,'not json'),storageKey);await page.reload();await wait(()=>document.querySelector('#submission-status').textContent.includes('blocked'));assert.ok(await page.locator('#start').isDisabled());await page.evaluate(()=>sessionStorage.clear());
  });
  await check('confirming a new request cannot silently discard current review edits',async()=>{
   await page.reload();await ready();await page.locator('#note').fill('Unsent review note must survive task confirmation');await page.locator('#query').fill('Another synthetic sequential question');state.mode='held';await page.locator('#start').click();while(!state.hold)await new Promise(r=>setTimeout(r,10));
   page.once('dialog',d=>d.dismiss());state.hold();state.hold=null;state.mode='normal';await ready();assert.equal(await page.locator('#note').inputValue(),'Unsent review note must survive task confirmation');assert.match(await page.locator('#notice').innerText(),/current edits are retained/);
  });
  assert.deepEqual(errors,[]);console.log(JSON.stringify({status:'passed',checks:count,model_calls:0,proof:'frontend fixed-response admission/recovery only'}));
 }finally{await browser.close();await new Promise(r=>server.close(r))}
})().catch(e=>{console.error(e);process.exitCode=1;server.close()});
