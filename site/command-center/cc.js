"use strict";

const REPO="gttome/New-Daily-AI-Brief";
const API=`https://api.github.com/repos/${REPO}`;
let snapshot=null;
let liveRuns=[];

const $=id=>document.getElementById(id);
const esc=value=>String(value??"Unavailable").replace(/[&<>'"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));
const fmt=value=>value===null||value===undefined||value===""?"Unavailable":String(value);
const stateClass=state=>{const v=String(state||"").toLowerCase();return /pass|verified|ready|succeeded|published|accepted|complete/.test(v)?"safe":/block|fail|critical|high/.test(v)?"blocked":/pending|warn|attention|unavailable|not_created/.test(v)?"warn":"neutral"};
const pill=state=>`<span class="pill ${stateClass(state)}">${esc(fmt(state).replaceAll("_"," "))}</span>`;
const metric=(label,value,note="")=>`<div class="metric-card"><span class="label">${esc(label)}</span><strong>${esc(fmt(value))}</strong>${note?`<small>${esc(note)}</small>`:""}</div>`;
const mini=(label,value)=>`<div class="mini-metric"><strong>${esc(fmt(value))}</strong><span>${esc(label)}</span></div>`;
const listItem=(title,note="")=>`<div class="list-item"><strong>${esc(title)}</strong>${note?`<small>${esc(note)}</small>`:""}</div>`;

async function fetchJson(url){const r=await fetch(url,{cache:"no-store",headers:{Accept:"application/vnd.github+json"}});if(!r.ok)throw new Error(`${r.status} ${r.statusText}`);return r.json()}
async function loadSnapshot(){const r=await fetch("state.json",{cache:"no-store"});if(!r.ok)throw new Error("state.json unavailable");return r.json()}
async function refreshLive(){
  const result={branch:null,manual:null,ci:null,parity:null,dataParity:null,error:null};
  try{
    const [branch,manual,ci,parity,dataParity]=await Promise.all([
      fetchJson(`${API}/branches/main`),
      fetchJson(`${API}/actions/workflows/manual-daily-brief.yml/runs?per_page=12`),
      fetchJson(`${API}/actions/workflows/ci.yml/runs?branch=main&per_page=8`),
      fetchJson(`${API}/actions/workflows/reader-parity.yml/runs?branch=main&per_page=8`),
      fetchJson(`${API}/actions/workflows/command-center-data-parity-validation.yml/runs?branch=main&per_page=8`)
    ]);
    result.branch=branch;result.manual=manual;result.ci=ci;result.parity=parity;result.dataParity=dataParity;
  }catch(err){result.error=err instanceof Error?err.message:String(err)}
  return result;
}
function renderExecutive(live){
  const e=snapshot.executive;
  $("executive-cards").innerHTML=[
    metric("Edition",e.edition_date),metric("Overall state",e.overall_state),metric("Production readiness",e.production_readiness),
    metric("Current stage",e.current_run_stage),metric("Latest edition",e.latest_successful_edition),metric("Reader health",e.reader_health),
    metric("Critical defects",e.critical_defects),metric("High defects",e.high_defects),metric("Warnings",e.warning_count),
    metric("Reader Site version",e.site_version),metric("Schedule readiness",e.schedule_readiness),metric("Main SHA",live?.branch?.commit?.sha?.slice(0,12)||snapshot.source.main_sha.slice(0,12),live?.branch?"live GitHub metadata":"committed snapshot")
  ].join("");
  const warnings=snapshot.warnings||[];$("warning-banner").hidden=!warnings.length;$("warning-banner").innerHTML=warnings.length?`<strong>Attention:</strong> ${warnings.map(esc).join(" · ")}`:"";
  $("snapshot-note").textContent=`Snapshot ${snapshot.snapshot_generated_at} · publication ${e.latest_publication_timestamp||"timestamp unavailable"}`;
}
function renderPipeline(){
  $("pipeline-list").innerHTML=snapshot.pipeline.map(s=>`<div class="stage" role="listitem"><h3>${esc(s.name)}</h3><div class="state">${esc(s.status)}</div><dl><dt>Time: </dt><dd>${esc(s.elapsed_seconds==null?"not recorded":`${s.elapsed_seconds}s`)}</dd><br><dt>Attempts: </dt><dd>${esc(s.attempt_count??"not recorded")}</dd><br><dt>Checkpoint: </dt><dd>${esc(s.checkpoint?"durable":"unavailable")}</dd></dl></div>`).join("");
}
function renderStories(){
  const s=snapshot.stories;$("allocation-pill").className=`pill ${s.allocation_pass?"safe":"blocked"}`;$("allocation-pill").textContent=s.allocation_pass?"2 / 2 / 2 + 1 Skill · PASS":"Allocation check";
  const a=s.allocation;$("story-allocation").innerHTML=[mini("Technical",a.technical_ai_engineering),mini("Applied",a.applied_genai_knowledge_workers),mini("Agents",a.agents_non_technical_people),mini("Agent Skills",s.agent_skills_count)].join("");
  $("stories-table").innerHTML=`<table><thead><tr><th>#</th><th>Story</th><th>Category</th><th>Source</th><th>Freshness</th><th>Novelty</th><th>Read</th><th>Book</th></tr></thead><tbody>${s.items.map(x=>`<tr><td>${esc(x.ordinal)}</td><td><strong>${esc(x.headline)}</strong>${x.agent_skills?'<br><span class="pill safe">Agent Skills</span>':""}</td><td>${esc(x.focus)}</td><td>${esc(x.source_organization)}<br><small>${esc(x.source_publication_date)}</small></td><td>${esc(x.freshness)}</td><td>${esc(x.novelty)}</td><td>${esc(x.reading_minutes==null?"—":`${x.reading_minutes} min`)}</td><td>${x.book_bridge?"Yes":"—"}</td></tr>`).join("")}</tbody></table>`;
}
function renderImages(){
  const i=snapshot.images;$("image-pill").className=`pill ${i.accepted_count===6?"safe":"blocked"}`;$("image-pill").textContent=`${i.accepted_count}/6 accepted`;
  $("images-grid").innerHTML=i.items.map(x=>listItem(`${x.ordinal}. ${x.story}`,`${x.dimensions?.join("×")||"dimensions unavailable"} · ${x.format} · QA ${x.visual_qa} · regeneration count ${x.regeneration_count??"not recorded"}`)).join("");
}
function renderMedia(){const m=snapshot.media;$("media-summary").innerHTML=[mini("Videos",m.video_count),mini("Podcasts",m.podcast_count),mini("Video sources",m.video_source_registry_count),mini("Podcast sources",m.podcast_source_registry_count)].join("");const rows=[...m.videos.map((x,i)=>listItem(`Video ${i+1}`,x.details)),...m.podcasts.map((x,i)=>listItem(`Podcast ${i+1}: ${x.title}`,`${x.source||"source not separately encoded"} · ${x.publication_date||"date unavailable"} · ${x.runtime||"runtime unavailable"}`))];$("media-list").innerHTML=rows.join("")}
function renderWatchlist(){const w=snapshot.watchlist;$("watchlist-metrics").innerHTML=[mini("Active",w.active_topics),mini("New",w.new_today),mini("Updated",w.updated_today),mini("Carried",w.carried_forward)].join("");$("watchlist-changes").innerHTML=(w.changed_topics?.length?w.changed_topics:["Changed-topic names not separately encoded for this snapshot"]).map(x=>listItem(x,`Source-state record: ${w.source_state_updated_at||"timestamp unavailable"}`)).join("")}
function renderBooks(){const b=snapshot.book_bridges;$("book-bridges").innerHTML=[mini("Verified references",b.reference_count),mini("Edition mappings",b.edition_mapping_count),mini("Historical bridges",b.historical_reader_bridge_records),mini("Latest explicit bridges",b.latest_edition_explicit_bridge_count)].join("")}
function renderReader(){const r=snapshot.reader_site;$("live-brief-link").href=r.live_edition_url;$("reader-grid").innerHTML=[metric("Bundle",r.reader_bundle_status),metric("HTML pages",r.html_page_count),metric("Archive items",r.archive_item_count),metric("Editions",r.edition_count),metric("Desktop QA",r.desktop_qa),metric("Small-screen QA",r.small_screen_qa),metric("Accessibility",r.accessibility),metric("Ratings",r.ratings),metric("Sharing",r.sharing),metric("Comments",r.comments),metric("Watchlist activity",r.watchlist_interactions),metric("Deployment",r.site_deployment_state,`Site version ${r.site_version}`)].join("")}
function renderControls(live){
  const latest=live?.manual?.workflow_runs?.[0];
  $("control-grid").innerHTML=snapshot.manual_controls.map(c=>{let url=c.url,enabled=c.enabled;if(c.id==="open-current-run"&&latest?.html_url)url=latest.html_url;if(c.id==="rerun-failed"){enabled=Boolean(latest&&latest.conclusion==="failure");if(enabled)url=latest.html_url}if(c.id==="refresh-state")return `<button class="control" type="button" data-refresh="true"><strong>${esc(c.label)}</strong><small>${esc(c.notes)}</small></button>`;return `<a class="control" href="${esc(url||"#")}" target="_blank" rel="noopener noreferrer" aria-disabled="${enabled?"false":"true"}"><strong>${esc(c.label)}</strong><small>${esc(c.notes)}</small></a>`}).join("");
  document.querySelectorAll('[data-refresh="true"]').forEach(btn=>btn.addEventListener("click",refreshAll));
}
function renderReadiness(){const gates=snapshot.readiness_gates;const all=gates.filter(g=>!["not_created"].includes(g.state));const passed=all.filter(g=>g.state==="passed").length;$("readiness-pill").className="pill warn";$("readiness-pill").textContent=`${passed}/${all.length} passed · cutover blocked`;$("readiness-list").innerHTML=gates.map(g=>`<div class="gate">${pill(g.state)}<div><strong>${esc(g.name)}</strong><div class="muted">${esc(g.evidence)}</div></div></div>`).join("")}
function renderSchedules(){const s=snapshot.schedules;$("schedule-blocker").textContent=s.blocker;$("schedule-list").innerHTML=s.planned.map(x=>listItem(`${x.name} · ${x.time} ${x.timezone}`,`${x.status} · created ${x.created} · enabled ${x.enabled}`)).join("")}
function durationSeconds(run){if(!run?.run_started_at||!run?.updated_at)return null;const v=(Date.parse(run.updated_at)-Date.parse(run.run_started_at))/1000;return Number.isFinite(v)&&v>=0?v:null}
function svgBars(values,labels){if(!values.length)return '<div class="chart-empty">No authoritative duration series is available yet.</div>';const max=Math.max(...values,1),w=520,h=130,p=18,bw=Math.max(12,(w-p*2)/values.length-8);return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Recent run duration bars">${values.map((v,i)=>{const bh=(v/max)*(h-38),x=p+i*((w-p*2)/values.length)+4,y=h-22-bh;return `<rect x="${x}" y="${y}" width="${bw}" height="${bh}" rx="3" fill="currentColor" opacity=".65"><title>${esc(labels[i])}: ${Math.round(v/60)} min</title></rect>`}).join("")}<line x1="${p}" y1="${h-22}" x2="${w-p}" y2="${h-22}" stroke="currentColor" opacity=".25"/></svg>`}
function renderParity(live){
  const d=snapshot.data_parity||{},h=snapshot.historical_data||{},p=snapshot.private_owner_data||{},domains=snapshot.data_domains||{};
  const latest=live?.dataParity?.workflow_runs?.[0];
  const pass=d.unresolved_required_families===0&&d.privacy_leakage_defects===0;
  $("parity-pill").className=`pill ${pass?"safe":"blocked"}`;$("parity-pill").textContent=pass?"Mapped · no unexplained gaps":"Parity attention required";
  $("parity-metrics").innerHTML=[
    metric("Required domains",d.required_domain_count),metric("Mapped families",d.mapped_family_count),
    metric("Unresolved required",d.unresolved_required_families),metric("Privacy leakage",d.privacy_leakage_defects),
    metric("Legacy families",h.family_count),metric("Parity validation",latest?.conclusion||latest?.status||"Committed contract","Full System Validation: NOT REQUESTED")
  ].join("");
  $("parity-domains").innerHTML=Object.entries(domains).map(([name,row])=>listItem(name.replaceAll("_"," "),`${row.status} · current: ${row.current_source||"not applicable"} · history: ${row.historical_source||"private"}`)).join("");
  $("history-parity").innerHTML=[
    listItem("Legacy source",`${h.legacy_repository||"Unavailable"} @ ${(h.legacy_reference_sha||"").slice(0,12)}`),
    listItem("Preservation",h.preservation_mode||"Unavailable"),
    ...Object.entries(h.families||{}).map(([name,row])=>listItem(name,`${row.file_count} files · ${row.first_path} → ${row.last_path}`))
  ].join("");
  $("private-owner-data").innerHTML=[
    listItem("Transport",p.transport||"Unavailable"),
    listItem("Repository values",p.values_committed_to_repository?"ERROR — private values present":"None — private values remain outside public GitHub"),
    listItem("Usage History",`dedupe ${p.usage_history?.dedupe_key||"Unavailable"} · missingness ${p.usage_history?.missingness||"Unavailable"} · estimates ${p.usage_history?.estimated_values_allowed?"allowed":"prohibited"}`),
    listItem("Book Change Proposals",`dedupe ${p.book_change_proposals?.dedupe_key||"Unavailable"} · states ${(p.book_change_proposals?.states||[]).join(" / ")} · prior decisions preserved ${p.book_change_proposals?.prior_owner_decisions_preserved}`)
  ].join("");
}
function renderHistory(live){const runs=live?.manual?.workflow_runs||[];liveRuns=runs;const vals=runs.map(durationSeconds).filter(v=>v!=null).reverse(),labels=runs.filter(r=>durationSeconds(r)!=null).map(r=>r.name||r.created_at).reverse();$("run-chart").innerHTML=svgBars(vals,labels);const rows=runs.length?runs.slice(0,8).map(r=>({edition:r.display_title||r.name,start:r.run_started_at,end:r.updated_at,elapsed:durationSeconds(r),state:r.conclusion||r.status,url:r.html_url})):snapshot.run_history;$("run-history").innerHTML=`<table><thead><tr><th>Run / edition</th><th>Start</th><th>End</th><th>Elapsed</th><th>State</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${r.url?`<a class="text-link" href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">${esc(r.edition||"Canonical run")} ↗</a>`:esc(r.edition)}</td><td>${esc(r.start||"not recorded")}</td><td>${esc(r.end||"not recorded")}</td><td>${esc(r.elapsed==null&&r.elapsed_seconds==null?"not recorded":`${Math.round((r.elapsed??r.elapsed_seconds)/60)} min`)}</td><td>${pill(r.state||r.completion_state)}</td></tr>`).join("")}</tbody></table>`}
function renderSourceHealth(){const s=snapshot.source_health;$("source-health").innerHTML=[metric("Source registry",s.source_registry_total),metric("Watchlist sources",s.watchlist_source_total),metric("Video registry",s.video_source_registry_total),metric("Podcast registry",s.podcast_source_registry_total)].join("");const entries=Object.entries(s.source_registry_status||{}),vals=entries.map(([,v])=>v),labels=entries.map(([k])=>k);$("source-chart").innerHTML=svgBars(vals,labels)}
function renderIncidents(){const i=snapshot.incidents;const current=i.current?.length?i.current.map(x=>listItem(x.title||"Incident",x.detail||"")):[listItem("No current Critical/High incident recorded",i.repair_outcome),listItem("Recovery checkpoint",i.latest_recovery_checkpoint||"Unavailable"),listItem("Anti-rework",`Rework avoided: ${i.rework_avoided}`)];$("incidents").innerHTML=current.join("")}
function renderUsage(){const u=snapshot.usage_cost;$("usage-cost").innerHTML=[listItem("Routine production target",u.routine_production_target),listItem("Verified Work usage",u.work_usage??"Unavailable — not estimated"),listItem("Verified credit usage",u.credit_usage??"Unavailable — not estimated"),listItem("Posture",u.note)].join("")}
function renderEngagement(){const e=snapshot.engagement;$("engagement").innerHTML=[metric("Ratings",e.ratings.count??"Unavailable",e.ratings.status),metric("Rating distribution",e.rating_distribution??"Unavailable","Not inferred"),metric("Shares",e.shares.count??"Unavailable",e.shares.status),metric("Private comments",e.private_comments.count??"Unavailable",e.private_comments.status),metric("Watchlist interest",e.watchlist_interest.count??"Unavailable",e.watchlist_interest.status),metric("Read events",e.read_event_activity??"Unavailable",e.note)].join("")}
function renderPrivacy(){const p=snapshot.privacy,c=snapshot.command_center_site;$("privacy").innerHTML=[listItem("Surface",p.surface),listItem("Public reader exposure",String(p.public_reader_exposure)),listItem("Credentials / private IDs / prompts",`${p.contains_credentials}/${p.contains_private_ids}/${p.contains_internal_prompts}`),listItem("Private Site target",`${c.identifier} · ${c.publication_state}`),listItem("Public Pages deployment",c.public_pages_deployment_allowed?"Allowed":"Prohibited for full Command Center")].join("")}
function updateLiveState(live){const ok=Boolean(live?.branch);$("live-state").className=`pill ${ok?"safe":"warn"}`;$("live-state").textContent=ok?"Live GitHub metadata connected":"Committed snapshot · live metadata unavailable";$("footer-meta").textContent=ok?`Live main ${live.branch.commit.sha.slice(0,12)} · snapshot ${snapshot.source.main_sha.slice(0,12)}`:`Snapshot main ${snapshot.source.main_sha.slice(0,12)} · GitHub live refresh unavailable`}
function renderAll(live){renderExecutive(live);renderPipeline();renderStories();renderImages();renderMedia();renderWatchlist();renderBooks();renderReader();renderControls(live);renderReadiness();renderSchedules();renderParity(live);renderHistory(live);renderSourceHealth();renderIncidents();renderUsage();renderEngagement();renderPrivacy();updateLiveState(live)}
async function refreshAll(){const btn=$("refresh");btn.disabled=true;btn.textContent="Refreshing…";try{if(!snapshot)snapshot=await loadSnapshot();const live=await refreshLive();renderAll(live)}catch(err){$("live-state").className="pill blocked";$("live-state").textContent="State load failed";$("warning-banner").hidden=false;$("warning-banner").textContent=`Command Center state could not be loaded: ${err instanceof Error?err.message:String(err)}`}finally{btn.disabled=false;btn.textContent="Refresh state"}}
$("refresh").addEventListener("click",refreshAll);refreshAll();
