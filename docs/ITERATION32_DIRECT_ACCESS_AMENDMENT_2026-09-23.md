# New Daily AI Brief — Iteration 32 Direct-Access Amendment
## Superseding the private-owner Command Center access requirement

Prepared September 23, 2026. Repository: `gttome/New-Daily-AI-Brief`.

This amendment records the owner's explicit Iteration 32 direction to remove the private-owner access mechanism because it creates unnecessary operational friction during hands-on testing.

## Controlling access change

For Iteration 32 testing, every requirement in the Iteration 32 handoff or start prompt that requires a **private**, **owner-only**, encrypted, keyed, authenticated, or URL-fragment-gated Command Center is superseded.

The greenfield Command Center must instead:

- be directly reachable from the greenfield reader through a normal stable URL;
- require no owner-only key, URL fragment, encryption handshake, login gate, or separate private-site mechanism for the Iteration 32 acceptance environment;
- expose only safe representative greenfield test state;
- contain no credentials, secrets, private IDs, private prompts, personal data, production controls, production executor authority, publication authority, cutover authority, decommission authority, or other prohibited private information;
- remain clearly labeled as greenfield, test-only, and pre-cutover;
- remain separate from the existing production Daily AI Brief;
- remain responsive and testable on desktop and phone/small screens.

## Safety boundary

This amendment changes **access mechanics only**. It does not authorize exposing genuinely private operational data. It does not authorize production credentials, production execution, production publication, reader cutover, production routing, subscriber changes, schedule changes, legacy-system modification, or paid dependencies.

Where existing Iteration 32 documents say not to expose private Command Center data publicly, interpret that requirement as: **do not place private data in the directly accessible Iteration 32 Command Center at all**. Use only safe representative test state.

## Process and stop gate

All Iteration 31 process-hardening rules remain in force. Reuse the existing Iteration 32 branch, PR, and exact-head CI. Do not create duplicate CI or duplicate PRs because of this amendment.

The Iteration 32 interim stop gate is unchanged except that the Command Center URL is now a direct-access test URL. After the reader URL and direct-access Command Center URL are deployed and verified on desktop and phone, provide both URLs and the acceptance checklist, then stop for owner testing. Do not close Iteration 32 or begin Iteration 33 until explicitly instructed after testing.
