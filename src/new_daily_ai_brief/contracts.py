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
