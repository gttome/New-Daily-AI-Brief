# Schema & Contract Version Policy

## Scope

Every authoritative Iteration 1 record carries an explicit semantic schema version. Consumers must use the version field, never a filename or implicit repository history, to infer compatibility.

## Versioning

The initial canonical version is `1.0.0`.

- **PATCH**: clarification or validation tightening that does not change valid stored semantics.
- **MINOR**: backward-compatible fields or enum extensions.
- **MAJOR**: incompatible semantic or structural change requiring an explicit migration.

## Migration rule

A reader may accept its current version and explicitly enumerated older versions for which a deterministic migration exists. Unknown versions fail closed. Migration must preserve the original source record until the upgraded record is safely written.

Iteration 1 includes a deterministic `run.json` migration from `0.9.0` to `1.0.0` as the contract fixture proving this path.

## Artifact identity

Artifact content identity is SHA-256 over semantic fields. Volatile timestamps are excluded from content identity. Therefore identical locked inputs and contract versions reproduce the same publication-bundle digest.

## Reader interactions

The greenfield rating contract is `five-star-v1`. Historical rating data keeps its original contract/version. No historical scale is silently converted to five stars.

## Missingness

`unknown`, `unavailable`, `suppressed`, and numeric zero are distinct states. Missing post-publication book evaluation is incomplete/degraded; it is never interpreted as zero proposals.
