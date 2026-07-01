// Harn-LLM Tester Dashboard
let harness='opencode',execMode='single',targets=[],atTimer=null,statusFilter='',sourceFilter='';
window.activeSessions = [];
const MAX_TARGET_ZIP_BYTES = 37 * 1024 * 1024;

async function readApiResponse(response){
  const text = await response.text();
  try{
    return text ? JSON.parse(text) : {};
  }catch(e){
    return {success:false,error:text || `HTTP ${response.status}`};
  }
}

document.addEventListener('DOMContentLoaded',()=>{
  renderHarnessBtns();refreshTargets();refreshAutotestStatus();refreshActiveSessions();
  atTimer=setInterval(refreshAutotestStatus,10000);
  // Initial monitor badge load + periodic refresh
  fetch('/api/tmux/sessions').then(r=>r.json()).then(d=>{
    const n=(d.sessions||[]).length;
    const badge=document.getElementById('monitorBadge');
    if(badge)badge.textContent=n?`(${n})`:'';
  }).catch(()=>{});
  setInterval(()=>{if(document.getElementById('panel-monitor')?.classList.contains('active'))refreshTmux();},10000);
  setInterval(refreshActiveSessions,5000); // Refresh active sessions every 5s
  setInterval(checkAutoRunStatus, 5000); // Check auto-run status every 5s
  // Periodic re-fetch sessions using DB-synced endpoint to fix stuck "running" status
  setInterval(async () => {
    try {
      const r = await fetch('/api/monitor/status');
      const d = await r.json();
      if (d.success) {
        // Re-render cards to update Auto-Run button states
        if (typeof renderCards === 'function') renderCards();
      }
    } catch (e) {}
  }, 8000);
});

function switchPanel(name,btn){
  document.querySelectorAll('[data-panel]').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  // Only toggle content panels (sections), not nav/harness panels
  document.querySelectorAll('section.panel').forEach(p=>p.classList.remove('active'));
  const el=document.getElementById('panel-'+name);
  if(el)el.classList.add('active');
  if(name==='monitor')refreshTmux();
  if(name==='autotest')loadAgentsConfig();
}

// ── Active Sessions ──────────────────────────────────────────────────────
async function refreshActiveSessions(){
  try{
    // Use the new monitor/status endpoint which combines DB state
    const r=await fetch('/api/monitor/status');
    const d=await r.json();
    const sessions=d.sessions||[];

    // Only running/attention sessions should mark target cards as active.
    // Done/failed/dead remain visible in Monitor but should not look like an active run.
    const activeSessions = sessions.filter(s => {
      const status = s.health?.status || 'running';
      return status === 'running' || status === 'attention';
    });

    // Parse session names to extract source/target
    window.activeSessions = activeSessions.map(s=>{
      const name=s.session_name||'';
      const parts=name.split('__');
      // Format: autotester__{ts}__{harness}__{stage}__{source}__{target}
      const source=parts[4]||'';
      const target=parts.slice(5).join('__')||'';
      const stage=parts[3]||'';
      const health=s.health||{};

      return {
        session_name: name,
        source: source,
        target: target,
        stage: stage,
        status: health.status || 'running',
        label: health.label || 'Running'
      };
    }).filter(s=>s.source && s.target); // Only keep valid sessions

    // Re-render cards to update Auto-Run button states
    renderCards();
  }catch(e){
    console.error('Failed to refresh active sessions:',e);
  }
}

// ── Harness ──────────────────────────────────────────────────────────────
function renderHarnessBtns(){
  ['opencode','claude','kimi','codex'].forEach(h=>{
    const b=document.createElement('button');
    b.className='runner-btn'+(h===harness?' active':'');
    b.textContent=h;b.onclick=()=>pickHarness(h);
    document.getElementById('harnessBtns')?.appendChild(b);
  });
}
function pickHarness(h){harness=h;
  document.querySelectorAll('#harnessBtns .runner-btn').forEach(b=>b.classList.toggle('active',b.textContent===h));
  document.getElementById('harnessBadge').textContent=h;
}
function setExecMode(m){execMode=m;
  document.getElementById('modeSingle').classList.toggle('active',m==='single');
  document.getElementById('modeDual').classList.toggle('active',m==='dual');
}

// ── Filters ──────────────────────────────────────────────────────────────
function filterTargets(btn,type,val){
  if(type==='status'){statusFilter=val;
    document.querySelectorAll('.filter-group .filter-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
  }else{sourceFilter=val;}
  applyFilters();
}
function applyFilters(){
  document.querySelectorAll('.card').forEach(c=>{
    c.style.display=(!statusFilter||c.dataset.status===statusFilter)&&(!sourceFilter||c.dataset.source===sourceFilter)?'':'none';
  });
}

// ── Targets ──────────────────────────────────────────────────────────────
async function refreshTargets(){
  try{
    const r=await fetch('/api/targets?refresh=1');if(!r.ok)throw new Error(r.status);
    const d=await r.json();targets=d.targets||[];
    renderStats(d.summary);renderCards();
    // Populate source filter buttons
    const sources=[...new Set(targets.map(t=>t.source).filter(Boolean))].sort();
    const fg=document.querySelector('.filter-group');
    // Remove old source buttons (keep status buttons + spacer)
    fg.querySelectorAll('.src-btn').forEach(b=>b.remove());
    sources.forEach(s=>{
      const b=document.createElement('button');
      b.className='filter-btn src-btn';b.textContent=s;
      b.onclick=()=>{sourceFilter=s===''?'':s;
        fg.querySelectorAll('.src-btn').forEach(x=>x.classList.remove('active'));
        b.classList.add('active');applyFilters();
      };
      fg.appendChild(b);
    });
  }catch(e){toast('Failed: '+e.message,'err');}
}

function renderStats(s){
  if(!s)return;
  const items=[['all','All',s.total||0],['completed','Completed',s.completed||0],['exec','Exec complete',s.exec_completed||0],['sample','Sample complete',s.sample_completed||0],['new','Not started',s.new||0]];
  document.getElementById('statsRow').innerHTML=items.map(([cls,lbl,n])=>`<div class="stat-item stat-${cls}"><div class="stat-number">${n}</div><div class="stat-label">${lbl}</div></div>`).join('');
}

function renderCards(){
  const grid=document.getElementById('cards');
  if(!targets.length){grid.innerHTML='<div style="color:#64748b;text-align:center;padding:48px;font-size:1.05rem">No test targets yet. Click "+ Add New Test" to create one.</div>';return;}
  grid.innerHTML=targets.map(renderCard).join('');
  bindTargetCardClicks();
  applyFilters();
}

function renderCard(t){
  const st=t.status||'new';
  const stages=t.stages||{};
  const sampleL=(stages.sample||{}).label||'pending';
  const execL=(stages.exec||{}).label||'pending';
  const specL=(stages.spec||{}).label||'pending';
  const execDetail=(stages.exec||{}).detail_label||'';
  const execDone=execL==='done',specDone=specL==='done';
  const sampleDone=sampleL==='done';

  const metaChip=(lbl,label)=>`<span class="meta-chip meta-${label==='done'?'done':label==='partial'?'partial':'pending'}">${lbl}</span>`;

  const desc=(t.description||'').substring(0,180);
  const nm=escAttr(t.name);

  // Check if there's an active session for this target
  const activeSession = window.activeSessions?.find(s =>
    String(s.source||'').toLowerCase() === String(t.source||'').toLowerCase()
    && String(s.target||'').toLowerCase() === String(t.target||'').toLowerCase()
  );
  const isRunning = !!activeSession;

  // Button disabled states
  const sampleDisabled = sampleDone ? 'disabled style="opacity:0.5;cursor:not-allowed"' : '';
  const execDisabled = execDone ? 'disabled style="opacity:0.5;cursor:not-allowed"' : '';
  const specDisabled = specDone ? 'disabled style="opacity:0.5;cursor:not-allowed"' : '';

  const statusLabels={completed:'Completed',exec_completed:'Exec complete',sample_completed:'Sample complete',new:'Not started'};

  // Auto-Run button
  let autoRunBtn = '';
  if (st === 'completed') {
    autoRunBtn = `<button class="btn btn-exec-track auto-run-btn" disabled style="opacity:0.5;cursor:not-allowed">✓ Completed</button>`;
  } else if (isRunning) {
    autoRunBtn = `<button class="btn btn-success auto-run-btn" onclick="goToMonitor()" style="background:linear-gradient(135deg,#10b981,#059669)">▶ Running...</button>`;
  } else {
    // Show what stage will run next
    let nextStage = '';
    if(sampleL !== 'done') nextStage = 'Sample';
    else if(execL !== 'done') nextStage = 'Exec';
    else if(specL !== 'done') nextStage = 'Spec';

    autoRunBtn = `<button class="btn btn-exec-track auto-run-btn" onclick="autoRun('${nm}')" title="Will auto-run all remaining stages (${nextStage} → ...)">🚀 Auto-Run (${nextStage})</button>`;
  }

  return `<div class="card target-card-clickable" data-status="${st}" data-source="${esc(t.source||'')}" data-target-name="${esc(t.name)}" role="button" tabindex="0">
    <div class="card-content">
      <div class="card-header">
        <h3><span class="card-source">${esc(t.source||'')}/</span>${esc(t.target||t.name)}</h3>
        <span class="status-badge status-${st}">${statusLabels[st]||st.replace(/_/g,' ')}</span>
      </div>
      <div class="card-desc">${esc(desc)}${(t.description||'').length>180?'...':''}</div>
      ${execDetail?`<div style="font-size:.78rem;color:#92400e;margin-bottom:8px">⚠ ${esc(execDetail)}</div>`:''}
      <div class="card-meta">
        ${metaChip('S',sampleL)}${metaChip('E',execL)}${metaChip('P',specL)}
        ${execDone||specDone?`<a href="/results/${encodeURIComponent(t.name)}" class="results-link" target="_blank" onclick="event.stopPropagation()">📋 Results</a>`:`<a href="/results/${encodeURIComponent(t.name)}" class="results-link results-link-dim" target="_blank" onclick="event.stopPropagation()">📋 Results</a>`}
      </div>
      <div class="card-actions" onclick="event.stopPropagation()">
        <button class="btn btn-sample" ${sampleDisabled} onclick="${sampleDone?'':`launch('sample','${nm}')`}" title="${sampleDone?'Sample complete':'Run Sample stage'}">Sample</button>
        <button class="btn btn-exec" ${execDisabled} onclick="${execDone?'':`launchExec('${nm}')`}" title="${execDone?'Exec complete':'Run Exec stage'}">Exec</button>
        <button class="btn btn-spec" ${specDisabled} onclick="${specDone?'':`launch('spec','${nm}')`}" title="${specDone?'Spec complete':'Run Spec stage'}">Spec</button>
      </div>
      <div class="card-actions-secondary" onclick="event.stopPropagation()">
        ${autoRunBtn}
      </div>
    </div>
  </div>`;
}

function bindTargetCardClicks(){
  document.querySelectorAll('.target-card-clickable').forEach(card=>{
    card.addEventListener('click',event=>{
      if(event.target.closest('button,a,input,select,textarea,label'))return;
      openRequirement(card.dataset.targetName||'');
    },true);
    card.addEventListener('keydown',event=>{
      if(event.key!=='Enter'&&event.key!==' ')return;
      if(event.target.closest('button,a,input,select,textarea,label'))return;
      event.preventDefault();
      openRequirement(card.dataset.targetName||'');
    });
  });
}

// Auto-Run function - launches a controller that runs all stages automatically
async function autoRun(name){
  try{
    // Check if target is already fully completed
    const target = targets.find(t => t.name === name);
    if(!target){
      toast('Target not found','err');
      return;
    }

    const stages = target.stages || {};
    const sampleL = (stages.sample||{}).label || 'pending';
    const execL = (stages.exec||{}).label || 'pending';
    const specL = (stages.spec||{}).label || 'pending';

    if(sampleL === 'done' && execL === 'done' && specL === 'done'){
      toast('All stages already completed!','info');
      return;
    }

    toast(`Starting Auto-Run controller for ${name}...`,'info');

    // Start the auto-run controller
    const r = await fetch('/api/autotest/auto-run',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({target: name, harness: harness})
    });
    const d = await r.json();

    if(d.success){
      toast(`Auto-Run controller started! Will manage all stages.`, 'ok');
      // Switch to monitor view to watch progress
      setTimeout(()=>{
        refreshTargets();
        switchPanel('monitor', document.querySelector('[data-panel="monitor"]'));
      }, 1500);
    }else{
      toast(d.error || 'Failed to start auto-run', 'err');
    }
  }catch(e){
    toast('Error: '+e.message, 'err');
  }
}

// Check auto-run status
async function checkAutoRunStatus(){
  try{
    const r = await fetch('/api/autotest/auto-run/status');
    const d = await r.json();
    if(d.success && d.state){
      const state = d.state;
      if(state.target_name && state.status === 'running'){
        // Update the auto-run button for this target
        const btn = document.querySelector(`[data-target-name="${state.target_name}"] .auto-run-btn`);
        if(btn){
          btn.className = 'btn btn-success auto-run-btn';
          btn.textContent = `▶ Running ${state.current_stage || '...'}`;
          btn.onclick = goToMonitor;
        }
      }
    }
  }catch(e){
    // Ignore errors
  }
}

// Go to monitor
function goToMonitor(){
  switchPanel('monitor',document.querySelector('[data-panel="monitor"]'));
}

function esc(s){if(!s)return'';const d=document.createElement('span');d.textContent=s;return d.innerHTML;}
function escAttr(s){return (s||'').replace(/\\/g,'\\\\').replace(/'/g,'\\\'');}

function parseMarkdown(text){
  if(!text)return'';
  return esc(text)
    .replace(/^### (.+)$/gm,'<h3>$1</h3>')
    .replace(/^## (.+)$/gm,'<h2>$1</h2>')
    .replace(/^# (.+)$/gm,'<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/```(\w+)?\n([\s\S]+?)```/g,'<pre><code>$2</code></pre>')
    .replace(/`(.+?)`/g,'<code>$1</code>')
    .replace(/^- (.+)$/gm,'<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s,'<ul>$1</ul>')
    .replace(/\n\n/g,'</p><p>')
    .replace(/\n/g,'<br>');
}

async function openRequirement(name){
  const dlg=document.getElementById('requirementModal');
  const title=document.getElementById('requirementTitle');
  const pathEl=document.getElementById('requirementPath');
  const body=document.getElementById('requirementBody');
  if(!dlg||!title||!body)return;

  title.textContent=name;
  if(pathEl)pathEl.textContent='';
  body.innerHTML='<div class="loading">Loading requirement.md...</div>';
  dlg.showModal();

  try{
    const r=await fetch(`/api/targets/${encodeURIComponent(name)}/requirement`);
    const d=await r.json();
    if(!d.success){
      body.innerHTML=`<div class="requirement-error">${esc(d.error||'Failed to load requirement.md')}</div>`;
      return;
    }
    if(pathEl)pathEl.textContent=d.path||'';
    body.innerHTML=parseMarkdown(d.content||'');
  }catch(e){
    body.innerHTML=`<div class="requirement-error">Error: ${esc(e.message)}</div>`;
  }
}

function closeRequirementModal(){
  document.getElementById('requirementModal')?.close();
}

// ── Launch ────────────────────────────────────────────────────────────────
async function launch(stage,name){
  try{const r=await fetch(`/api/stage/${stage}/${encodeURIComponent(name)}?harness=${harness}`,{method:'POST'});const d=await r.json();toast(d.success?d.message:(d.error||'Failed'),d.success?'ok':'err');if(d.success)setTimeout(refreshTargets,3000);}catch(e){toast('Error: '+e.message,'err');}
}
async function launchExec(name){
  try{const r=await fetch(`/api/stage/exec/${encodeURIComponent(name)}?harness=${harness}&mode=${execMode}`,{method:'POST'});const d=await r.json();toast(d.success?d.message:(d.error||'Failed'),d.success?'ok':'err');if(d.success)setTimeout(refreshTargets,3000);}catch(e){toast('Error: '+e.message,'err');}
}
async function launchTrack(track,name){
  try{const r=await fetch(`/api/stage/exec/${encodeURIComponent(name)}?harness=${harness}&track=${track}`,{method:'POST'});const d=await r.json();toast(d.success?d.message:(d.error||'Failed'),d.success?'ok':'err');if(d.success)setTimeout(refreshTargets,3000);}catch(e){toast('Error: '+e.message,'err');}
}

// ── Modal ─────────────────────────────────────────────────────────────────
function openAddModal(){document.getElementById('addModal').showModal();}
function closeAddModal(){document.getElementById('addModal').close();document.getElementById('addForm').reset();}
async function submitTarget(e){
  e.preventDefault();
  const body={name:document.getElementById('targetName').value.trim(),description:document.getElementById('targetDesc').value.trim()};
  const file=document.getElementById('targetZip').files?.[0];
  if(file){
    if(file.size > MAX_TARGET_ZIP_BYTES){
      toast('Zip file is too large. Keep it under 37 MB.','err');
      return;
    }
    const buf=await file.arrayBuffer();const bytes=new Uint8Array(buf);let bin='';for(let i=0;i<bytes.length;i++)bin+=String.fromCharCode(bytes[i]);body.source_zip=btoa(bin);
  }
  try{
    const r=await fetch('/api/targets',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d=await readApiResponse(r);
    if(r.ok&&d.success){toast('Created: '+d.name,'ok');closeAddModal();refreshTargets();}
    else toast(`Create failed HTTP ${r.status}: ${d.error||d.message||'Failed'}`,'err');
  }catch(e){toast('Error: '+e.message,'err');}
}

// ── Tmux Monitor ──────────────────────────────────────────────────────────
async function refreshTmux(){
  const el=document.getElementById('tmuxContent');
  // Show loading only on first load
  if(!el.dataset.loaded){
    el.innerHTML='<div class="loading">Loading sessions...</div>';
  }
  try{
    const r=await fetch('/api/tmux/sessions');const d=await r.json();
    const sessions=d.sessions||[];
    if(!sessions.length){el.innerHTML='<div style="color:#64748b;text-align:center;padding:36px;font-size:.95rem">No active sessions</div>';el.dataset.loaded='1';return;}

    // Health summary row
    const summary=d.summary||{};
    const summaryChips=[['running','Running',''],['done','Done','health-done'],['failed','Failed','health-failed'],['exited','Exited','health-exited'],['dead','Dead','health-failed'],['attention','Attention','health-attention']];
    let html='<div class="action-bar" style="margin-bottom:10px"><span style="font-weight:700;font-size:.9rem">Sessions:</span> '+
      summaryChips.map(([k,lbl,cls])=>summary[k]?`<span class="session-health-chip ${cls}" style="font-size:.78rem"><span class="session-health-dot"></span>${lbl}: ${summary[k]}</span>`:'').join('')+
      '</div>';

    // Health chips
    html+='<div class="autotest-session-list">';
    html+=sessions.map(s=>{
      const h=s.health||{};const status=h.status||'running';
      const cls=status==='done'?'health-done':(status==='failed'||status==='dead')?'health-failed':status==='attention'?'health-attention':status==='exited'?'health-exited':'';
      return `<span class="session-health-chip ${cls}" title="${esc(h.detail||'')}">
        <span class="session-health-dot"></span>
        <span class="session-health-name">${esc(h.label||status)} · ${esc(s.stage||'?')}/${esc(s.harness||'?')} · ${esc(s.source||'?')}/${esc(s.target||'?')}</span>
      </span>`;
    }).join('');
    html+='</div>';

    // Detail cards (no tail by default for performance)
    html+='<div style="margin-top:12px">';
    html+=sessions.map((s, idx)=>{
      const h=s.health||{};
      return `<div class="session-card">
        <div class="session-head">
          <span class="session-stage">${esc(s.stage||'?')}</span>
          <span class="session-harness">${esc(s.harness||'?')}</span>
          <span class="session-target">${esc(s.source||'?')}/${esc(s.target||'?')}</span>
          <span class="session-health-chip ${(h.status==='done'?'health-done':h.status==='failed'||h.status==='dead'?'health-failed':h.status==='exited'?'health-exited':h.status==='attention'?'health-attention':'')}" style="margin-left:6px">${esc(h.label||h.status||'?')}</span>
          <span style="font-size:.74rem;color:#64748b;margin-left:auto">${s.window_count||0} windows · ${esc(h.detail||'')}</span>
          <button class="btn btn-danger" onclick="killSession('${escAttr(s.session_name)}')" style="padding:4px 10px;font-size:.72rem;margin-left:6px">Kill</button>
          <button class="btn btn-neutral tail-toggle-btn" data-idx="${idx}" data-session="${escAttr(s.session_name)}" style="padding:4px 10px;font-size:.72rem;margin-left:4px">📋 Tail</button>
        </div>
        <div id="tail-${idx}" class="session-tail-container"></div>
      </div>`;
    }).join('');
    html+='</div>';

    // Save which tails are currently expanded before re-rendering
    const expandedTails = {};
    document.querySelectorAll('.session-tail-container').forEach(c => {
      if (c.dataset.loaded === '1') {
        const id = c.id;
        expandedTails[id] = true;
      }
    });

    el.innerHTML=html;
    el.dataset.loaded='1';

    // Restore expanded tails after re-rendering
    Object.keys(expandedTails).forEach(id => {
      const container = document.getElementById(id);
      if (!container) return;
      // Extract idx from id like "tail-0"
      const idx = id.replace('tail-', '');
      const btn = document.querySelector(`.tail-toggle-btn[data-idx="${idx}"]`);
      if (!btn) return;
      const sessionName = btn.dataset.session;
      // Re-fetch and re-render the tail content
      loadSessionTail(sessionName, parseInt(idx), true).then(() => {
        // Update button text to "Hide"
        btn.textContent = '🔽 Hide';
      });
    });

    // Bind click handlers for tail toggle buttons
    document.querySelectorAll('.tail-toggle-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = btn.dataset.idx;
        const sessionName = btn.dataset.session;
        loadSessionTail(sessionName, parseInt(idx), false).then(() => {
          // Update button text based on state
          const container = document.getElementById(`tail-${idx}`);
          if (container && container.dataset.loaded === '1') {
            btn.textContent = '🔽 Hide';
          } else {
            btn.textContent = '📋 Tail';
          }
        });
      });
    });

    // Update monitor badge
    const badge=document.getElementById('monitorBadge');
    if(badge){const n=sessions.length;badge.textContent=n?`(${n})`:'';}
  }catch(e){
    console.error('Refresh error:', e);
    if(!el.dataset.loaded){
      el.innerHTML='<div style="color:#b91c1c;padding:24px">Error loading sessions</div>';
    }
  }
}

// Load session tail on demand - persists across refreshes
async function loadSessionTail(sessionName, idx, isRestore=false){
  const container=document.getElementById(`tail-${idx}`);
  if(!container) return;

  // If already loaded and we're not forcing a refresh, toggle it off
  if(!isRestore && container.dataset.loaded){
    container.innerHTML='';
    container.dataset.loaded='';
    return false;
  }

  // If restoring or first load, fetch content
  if(!isRestore){
    container.innerHTML='<div class="loading" style="padding:10px">Loading tail...</div>';
  }

  try{
    const r=await fetch(`/api/tmux/pane?target=${encodeURIComponent(sessionName)}&lines=200`);
    const d=await r.json();
    if(d.success && d.content){
      container.innerHTML=`<pre class="autotest-log" style="margin-top:8px;max-height:500px;font-size:.78rem;overflow:auto;padding:12px;background:#1a1a1a;color:#dce9e0;border-radius:8px">${esc(d.content)}</pre>`;
      container.dataset.loaded='1';
      return true;
    } else {
      container.innerHTML='<div style="color:#64748b;padding:8px;font-size:.78rem">No tail available</div>';
      return false;
    }
  }catch(e){
    container.innerHTML='<div style="color:#b91c1c;padding:8px">Failed to load</div>';
    return false;
  }
}

// ── AutoTest ──────────────────────────────────────────────────────────────
async function startAutoTest(){
  const body={stage:document.getElementById('atStage').value,scope:document.getElementById('atScope').value,test_mode:document.getElementById('atMode').value,launch_mode:'once',once:true,runner_plan:[harness+':3']};
  try{const r=await fetch('/api/autotest/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json();toast(d.success?'Started':'Failed: '+(d.error||''),d.success?'ok':'err');refreshAutotestStatus();}catch(e){toast('Error: '+e.message,'err');}
}
async function stopAutoTest(){
  try{const r=await fetch('/api/autotest/stop',{method:'POST'});toast((await r.json()).message,'info');refreshAutotestStatus();}catch(e){}
}
async function refreshAutotestStatus(){
  try{
    const r=await fetch('/api/autotest/status');const d=await r.json();
    const el=document.getElementById('autotestStatus');
    if(!d.running){el.textContent='Not running';return;}
    el.textContent='Running | Workers: '+(d.worker_count||0)+'\n\n'+JSON.stringify(d.state,null,2)+'\n\n--- Log ---\n'+(d.log_tail||[]).slice(-15).join('\n');
  }catch(e){}
}
async function killSession(name){
  if(!confirm('Kill session: '+name+'?'))return;
  try{
    // Kill individual session by name
    const r=await fetch('/api/autotest/kill-session/'+encodeURIComponent(name),{method:'POST'});
    const d=await r.json();
    if(d.success){
      toast('Killed: '+name,'info');
    }else{
      toast('Failed to kill: '+(d.error||d.message),'err');
    }
    setTimeout(refreshTmux,1500);
  }catch(e){toast('Error: '+e.message,'err');}
}

async function killAllSessions(){
  if(!confirm('Kill ALL autotester sessions?'))return;
  try{
    const r=await fetch('/api/autotest/kill-sessions',{method:'POST'});
    const d=await r.json();
    toast('Killed '+d.killed+' sessions','info');
    setTimeout(refreshTmux,1500);
  }catch(e){toast('Error: '+e.message,'err');}
}

// ── Agents Config ────────────────────────────────────────────────────────
async function loadAgentsConfig(){
  try{
    const r=await fetch('/api/agents');const d=await r.json();
    const agents=d.agents||[];
    const grid=document.getElementById('agentsCards');
    grid.innerHTML=agents.map(a=>`<div class="card">
      <div class="card-content">
        <div class="card-header">
          <h3>${esc(a.name||a.key)}</h3>
          <span class="status-badge status-sample_completed">${esc(a.key)}</span>
        </div>
        <div class="card-desc">${esc(a.description||'')}</div>
        <div style="display:flex;gap:8px;align-items:center;margin-top:10px">
          <label style="font-size:.78rem;font-weight:700;white-space:nowrap">Model:</label>
          <input class="autotest-input" id="agentModel_${esc(a.key)}" value="${esc(a.model||'')}" style="flex:1;padding:6px 10px;font-size:.82rem">
          <button class="btn btn-neutral" onclick="updateAgentModel('${esc(a.key)}')" style="padding:7px 10px;font-size:.78rem">Save</button>
        </div>
      </div>
    </div>`).join('');
  }catch(e){}
}

async function updateAgentModel(agent){
  const input=document.getElementById('agentModel_'+agent);
  if(!input)return;
  const model=input.value.trim();
  if(!model){toast('Model name required','err');return;}
  try{
    const r=await fetch('/api/agents/'+encodeURIComponent(agent),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({model})});
    const d=await r.json();
    if(d.success)toast('Updated: '+agent+' → '+model,'ok');
    else toast(d.error||'Failed','err');
  }catch(e){toast('Error: '+e.message,'err');}
}

function toast(msg,type){const t=document.getElementById('toast');t.textContent=msg;t.className='toast '+type+' show';clearTimeout(t._tid);t._tid=setTimeout(()=>t.classList.remove('show'),3000);}
