const testState={
  run_identity:"greenfield-owner-acceptance-2026-09-23",
  edition_date:"2026-09-23",
  mode:"shadow",
  environment:"greenfield-owner-acceptance",
  status:"ready_for_owner_testing",
  phase:"deployed_acceptance",
  qa:{contracts:"pass",reader_surface:"pass",command_center_surface:"pass",production_isolation:"pass"},
  freshness:{state:"representative_test_data"},
  recovery:{resume_state:"checkpoint_reusable",prior_iteration_reexecution:0,duplicate_prs:0,duplicate_ci_for_same_head:0}
};
async function buildMeta(){try{const r=await fetch("../build.json",{cache:"no-store"});if(!r.ok)throw new Error();return await r.json()}catch{return null}}
function show(d,b){document.getElementById("run-id").textContent=d.run_identity;document.getElementById("run-mode").textContent=`${d.edition_date} · ${d.mode} · ${d.environment}`;document.getElementById("run-status").textContent=d.status.replaceAll("_"," ");document.getElementById("run-phase").textContent=d.phase.replaceAll("_"," ");document.getElementById("qa-state").textContent=Object.values(d.qa).every(x=>x==="pass")?"PASS":"CHECK";document.getElementById("freshness").textContent=d.freshness.state.replaceAll("_"," ");document.getElementById("source-sha").textContent=b?`Deployed source ${b.source_sha}`:"Deployment identity unavailable";document.getElementById("resume-state").textContent=d.recovery.resume_state.replaceAll("_"," ");document.getElementById("anti-rework").textContent=`Prior reexecution ${d.recovery.prior_iteration_reexecution} · duplicate PRs ${d.recovery.duplicate_prs} · duplicate exact-head CI ${d.recovery.duplicate_ci_for_same_head}`;document.getElementById("build-meta").textContent=b?`Source ${b.source_sha.slice(0,12)} · deployed ${b.deployed_at}`:"Deployment identity unavailable"}
(async()=>{show(testState,await buildMeta())})();
