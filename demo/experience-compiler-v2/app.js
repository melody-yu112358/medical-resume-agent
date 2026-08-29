const $=s=>document.querySelector(s);let sid=new URLSearchParams(location.search).get("session_id"),state,runtimeInfo;
const devMode=["127.0.0.1","localhost"].includes(location.hostname);
async function api(url,options){const r=await fetch(url,options);const t=await r.text();let b;try{b=JSON.parse(t)}catch{throw Error(`服务返回异常（HTTP ${r.status}）`)}if(!r.ok)throw Error(b.error||"请求失败");return b}
function msg(text,who="ai"){const n=document.createElement("article");n.className=`msg ${who}`;n.textContent=text;$("#chat").append(n);n.scrollIntoView({block:"end"})}
function render(x){state=x.state||state;if(x.assistant_message)msg(x.assistant_message);const c=x.confirmation;$("#confirm").innerHTML=c?`<div class="card"><b>只需确认一件事</b><p>${c.question}</p><button id="confirmNow">确认</button></div>`:"";$("#confirmNow")?.addEventListener("click",()=>send("确认"));const ready=x.audit_status||{ready:0,not_ready:0};$("#audit").textContent=`审计：${ready.ready} 条可用，${ready.not_ready} 条待核实`;
const bullets=x.resume_document?.research_experience?.[0]?.bullets||[];$("#preview").innerHTML=bullets.length?`<article>${bullets.map(b=>`<p>• ${b.text}</p>`).join("")}</article>`:"<article>完成一段可核实经历与必要责任确认后，第一版措辞会显示在这里。</article>";$("#targets").classList.toggle("hidden",!state?.canonical_experience);renderDebug(x.runtime_trace)}
function renderDebug(trace){if(!devMode)return;const panel=$("#debug");panel.classList.remove("hidden");const sha=runtimeInfo?.git_head_sha?.slice(0,12)||"unknown";panel.textContent=`DEV runtime\nbuild: ${sha}\nv2: ${runtimeInfo?.conversation_v2_version||"unknown"}\nsource: ${trace?.final_response_source||"read"}\nplan: ${trace?.model_plan_status||"not available"}\nwriter: ${trace?.presentation_writer_status||"not called"}`}
async function send(text){if(!text)return;$("#error").textContent="";msg(text,"user");try{const x=await api(`/api/conversations-v2/${sid}/messages`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text,consent_confirmed:$("#consent").checked})});$("#input").value="";render(x)}catch(e){$("#error").textContent=e.message}}
async function create(){const x=await api("/api/conversations-v2",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"});sid=x.session_id;history.replaceState(null,"",`?session_id=${sid}`);$("#chat").innerHTML="";state=x.state;msg("说一段真实经历即可；我会只追问最关键的责任信息，并尽快给出第一版。 ");render(x)}
$("#form").onsubmit=e=>{e.preventDefault();send($("#input").value.trim())};document.querySelectorAll("[data-target]").forEach(b=>b.onclick=()=>send(b.dataset.target));$("#new").onclick=create;
if(devMode){api("/api/runtime-info").then(x=>{runtimeInfo=x;renderDebug()}).catch(()=>{})}
if(sid){
  api(`/api/conversations-v2/${sid}`).then(x=>{state=x.state;msg("已恢复 v2 会话。 ");render(x)}).catch(e=>$("#error").textContent=e.message);
}else{
  create().catch(e=>$("#error").textContent=e.message);
}
