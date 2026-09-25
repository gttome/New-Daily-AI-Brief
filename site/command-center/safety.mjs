export const STATES=['Pending review','Approved','Rejected','Proposed','Accepted','Applied','Deferred','Dismissed'];
export const NOTICE='Anything submitted here is public. Do not enter credentials, account/payment information, or personal information about another person.';
const secret=/(?:sk-[a-zA-Z0-9_-]{16,}|gh[pousr]_[a-zA-Z0-9]{16,}|github_pat_[a-zA-Z0-9_]+|Bearer\s+[A-Za-z0-9._-]{12,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|\b(?:\d[ -]?){13,19}\b|\b\d{3}-\d{2}-\d{4}\b)/i;
export function unsafeText(s){return secret.test(s)||/\b(?:password|api[_ -]?key|access[_ -]?token|account number|routing number|home address|phone number)\s*[:=]/i.test(s);}
export function canonical(x){if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';if(x&&typeof x==='object')return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';return JSON.stringify(x);}
export async function hash(x){const bytes=new TextEncoder().encode(typeof x==='string'?x:canonical(x));return [...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');}
export function validateRevision(body,family){
 const keys=['idempotency_key','base_revision','status','notes','priority','client_schema_version','application_evidence'];
 if(!body||typeof body!=='object'||Object.keys(body).some(k=>!keys.includes(k)))throw new Error('Unknown or invalid fields');
 if(!/^[\w-]{16,100}$/.test(body.idempotency_key||'')||!Number.isSafeInteger(body.base_revision)||body.base_revision<0)throw new Error('Invalid request key or base revision');
 if(!STATES.includes(body.status))throw new Error('Invalid status');
 if(typeof body.notes!=='string'||new TextEncoder().encode(body.notes).length>4096||unsafeText(body.notes))throw new Error('Review text exceeds limits or contains sensitive information');
 if(body.application_evidence!=null){const e=body.application_evidence;if(typeof e!=='object'||Array.isArray(e)||Object.keys(e).some(k=>!['commit_sha','target_path'].includes(k))||!/^[a-f0-9]{40}$/.test(e.commit_sha||'')||typeof e.target_path!=='string'||e.target_path.length>512||!/^[a-zA-Z0-9_./ -]+$/.test(e.target_path)||unsafeText(e.target_path))throw new Error('Invalid application evidence');}
 if(body.priority!=null&&!['high','medium','low'].includes(body.priority))throw new Error('Invalid priority');
 return {...body,notes:body.notes.normalize('NFC').replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/g,'')};
}
