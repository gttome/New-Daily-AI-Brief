from __future__ import annotations

from dataclasses import dataclass
from typing import Final

SCHEMA_VERSION: Final = "1.0.0"
RUN_SCHEMA_VERSION: Final = "1.0.0"
RATING_CONTRACT_VERSION: Final = "five-star-v1"
PROJECTION_SCHEMA_VERSION: Final = "1.0.0"
COMPLETION_CONTRACT_VERSION: Final = "1.0.0"
READINESS_SCHEMA_VERSION: Final = "1.0.0"
READINESS_POLICY_VERSION: Final = "1.0.0"
PREFLIGHT_SCHEMA_VERSION: Final = "1.0.0"
PREFLIGHT_POLICY_VERSION: Final = "1.0.0"
PLAN_SCHEMA_VERSION: Final = "1.0.0"
PLAN_POLICY_VERSION: Final = "1.0.0"
ADMISSION_SCHEMA_VERSION: Final = "1.0.0"
ADMISSION_POLICY_VERSION: Final = "1.0.0"
EXECUTION_PREFLIGHT_SCHEMA_VERSION: Final = "1.0.0"
EXECUTION_PREFLIGHT_POLICY_VERSION: Final = "1.0.0"
EXECUTION_REHEARSAL_SCHEMA_VERSION: Final = "1.0.0"
EXECUTION_REHEARSAL_POLICY_VERSION: Final = "1.0.0"
EXECUTION_AUTHORIZATION_REVIEW_SCHEMA_VERSION: Final = "1.0.0"
EXECUTION_AUTHORIZATION_REVIEW_POLICY_VERSION: Final = "1.0.0"
EXECUTION_AUTHORIZATION_DECISION_SCHEMA_VERSION: Final = "1.0.0"
EXECUTION_AUTHORIZATION_DECISION_POLICY_VERSION: Final = "1.0.0"
EXECUTION_AUTHORIZATION_PACKAGE_SCHEMA_VERSION: Final = "1.0.0"
EXECUTION_AUTHORIZATION_PACKAGE_POLICY_VERSION: Final = "1.0.0"
EXECUTION_AUTHORITY_READINESS_SCHEMA_VERSION: Final = "1.0.0"
EXECUTION_AUTHORITY_READINESS_POLICY_VERSION: Final = "1.0.0"
EXECUTION_EXECUTOR_BINDING_READINESS_SCHEMA_VERSION: Final = "1.0.0"
EXECUTION_EXECUTOR_BINDING_READINESS_POLICY_VERSION: Final = "1.0.0"
EXECUTION_EXECUTOR_DESCRIPTOR_VERSION: Final = "1.0.0"
EXECUTION_EXECUTOR_BINDING_READINESS_RECORD_VERSION: Final = "1.0.0"
EXECUTION_EXECUTOR_BINDING_PREFLIGHT_SCHEMA_VERSION: Final = "1.0.0"
EXECUTION_EXECUTOR_BINDING_PREFLIGHT_POLICY_VERSION: Final = "1.0.0"
EXECUTION_EXECUTOR_BINDING_PLAN_DESCRIPTOR_VERSION: Final = "1.0.0"
EXECUTION_EXECUTOR_BINDING_PREFLIGHT_RECORD_VERSION: Final = "1.0.0"

STATES: Final[tuple[str, ...]] = (
    "Ready",
    "Acquiring",
    "Deciding",
    "Building",
    "Validating",
    "Releasing",
    "Deployed",
    "LiveVerified",
    "PostPublicationEvaluation",
    "OperationsReconciled",
    "Complete",
    "Recovering",
)

LEGAL_TRANSITIONS: Final[dict[str, set[str]]] = {
    "Ready": {"Acquiring"},
    "Acquiring": {"Deciding", "Recovering"},
    "Deciding": {"Building", "Recovering"},
    "Building": {"Validating", "Recovering"},
    "Validating": {"Releasing", "Recovering"},
    "Releasing": {"Deployed", "Recovering"},
    "Deployed": {"LiveVerified", "Recovering"},
    "LiveVerified": {"PostPublicationEvaluation"},
    "PostPublicationEvaluation": {"OperationsReconciled", "Recovering"},
    "OperationsReconciled": {"Complete", "Recovering"},
    "Complete": set(),
    "Recovering": {"Acquiring", "Deciding", "Building", "Validating", "Releasing", "Deployed", "PostPublicationEvaluation", "OperationsReconciled"},
}

ARTIFACT_DEPENDENCIES: Final[dict[str, tuple[str, ...]]] = {
    "discovery": (),
    "edition": ("discovery",),
    "media": ("edition",),
    "images": ("edition",),
    "watchlist": ("edition",),
    "book-bridges": ("edition",),
    "rating-contract": (),
    "publication-bundle": ("edition", "media", "images", "watchlist", "book-bridges", "rating-contract"),
    "reader-render": ("publication-bundle",),
    "route-manifest": ("reader-render",),
    "release-package": ("route-manifest",),
    "shadow-deployment": ("release-package",),
    "live-verification": ("shadow-deployment",),
    "book-change-evaluation": ("publication-bundle",),
    "command-center-projection": (
        "discovery",
        "edition",
        "rating-contract",
        "media",
        "watchlist",
        "book-bridges",
        "images",
        "publication-bundle",
        "reader-render",
        "route-manifest",
        "release-package",
        "shadow-deployment",
        "live-verification",
        "book-change-evaluation",
    ),
    "projection-watermark": ("publication-bundle", "book-change-evaluation"),
    "completion": ("publication-bundle", "book-change-evaluation", "projection-watermark"),
    "readiness-admission": ("completion",),
    "production-integration-preflight": ("readiness-admission",),
    "production-integration-plan": ("production-integration-preflight",),
    "production-integration-admission": ("production-integration-plan",),
    "production-integration-execution-preflight": ("production-integration-admission",),
    "production-integration-execution-rehearsal": ("production-integration-execution-preflight",),
    "production-integration-execution-authorization-review": ("production-integration-execution-rehearsal",),
    "production-integration-execution-authorization-decision": ("production-integration-execution-authorization-review",),
    "production-integration-execution-authorization-package": ("production-integration-execution-authorization-decision",),
    "production-integration-execution-authority-readiness": ("production-integration-execution-authorization-package",),
    "production-integration-execution-executor-binding-readiness": ("production-integration-execution-authority-readiness",),
    "production-integration-execution-executor-binding-preflight": ("production-integration-execution-executor-binding-readiness",),
}

ARTIFACT_FILES: Final[dict[str, str]] = {
    "discovery": "discovery.json",
    "edition": "edition.json",
    "media": "media.json",
    "images": "images.json",
    "watchlist": "watchlist.json",
    "book-bridges": "book-bridges.json",
    "rating-contract": "rating-contract.json",
    "publication-bundle": "publication-bundle.json",
    "reader-render": "reader-render.json",
    "route-manifest": "route-manifest.json",
    "release-package": "release-package.json",
    "shadow-deployment": "shadow-deployment.json",
    "live-verification": "live-verification.json",
    "book-change-evaluation": "book-change-evaluation.json",
    "command-center-projection": "command-center-projection.json",
    "projection-watermark": "projection-watermark.json",
    "completion": "completion.json",
    "readiness-admission": "readiness-admission.json",
    "production-integration-preflight": "production-integration-preflight.json",
    "production-integration-plan": "production-integration-plan.json",
    "production-integration-admission": "production-integration-admission.json",
    "production-integration-execution-preflight": "production-integration-execution-preflight.json",
    "production-integration-execution-rehearsal": "production-integration-execution-rehearsal.json",
    "production-integration-execution-authorization-review": "production-integration-execution-authorization-review.json",
    "production-integration-execution-authorization-decision": "production-integration-execution-authorization-decision.json",
    "production-integration-execution-authorization-package": "production-integration-execution-authorization-package.json",
    "production-integration-execution-authority-readiness": "production-integration-execution-authority-readiness.json",
    "production-integration-execution-executor-binding-readiness": "production-integration-execution-executor-binding-readiness.json",
    "production-integration-execution-executor-binding-preflight": "production-integration-execution-executor-binding-preflight.json",
}

MANDATORY_COMPLETION_RECEIPTS: Final[tuple[str, ...]] = (
    "publication_bundle_digest",
    "deployment_identity",
    "live_verification",
    "book_change_evaluation_digest",
    "projection_watermark_digest",
)


@dataclass(frozen=True)
class FailureInjection:
    stage: str
    failure_class: str = "synthetic_validation_failure"
    candidate_id: str | None = None
