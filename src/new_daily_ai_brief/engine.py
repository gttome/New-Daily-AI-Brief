from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

from .build import BuildBoundaryFailure, BuildFailureInjection, BuildStagePipeline
from .completion import CompletionBoundaryFailure, FinalCompletionPipeline
from .contracts import (
    ARTIFACT_DEPENDENCIES,
    LEGAL_TRANSITIONS,
    MANDATORY_COMPLETION_RECEIPTS,
    PROJECTION_SCHEMA_VERSION,
    RATING_CONTRACT_VERSION,
    RUN_SCHEMA_VERSION,
    SCHEMA_VERSION,
    FailureInjection,
)
from .editorial import DiscoveryEditorialPipeline, EditorialCandidateFailure, EditorialFailureInjection
from .evaluation import EvaluationBoundaryFailure, PostPublicationEvaluationPipeline
from .operations import OperationsBoundaryFailure, OperationsReconciliationPipeline
from .pre_release import ImageBoundaryFailure, PreReleasePipeline, ValidationBoundaryFailure
from .render import ReaderSurfaceRenderer, RenderBoundaryFailure
from .release import ReleaseBoundaryFailure, ShadowReleasePipeline
from .readiness import ProductionReadinessPipeline
from .integration_preflight import ProductionIntegrationPreflight
from .integration_plan import ProductionIntegrationPlan
from .integration_admission import ProductionIntegrationAdmission
from .integration_execution_preflight import ProductionIntegrationExecutionPreflight
from .integration_execution_rehearsal import ProductionIntegrationExecutionRehearsal
from .integration_execution_authorization_review import ProductionIntegrationExecutionAuthorizationReview
from .integration_execution_authorization_decision import ProductionIntegrationExecutionAuthorizationDecision
from .integration_execution_authorization_package import ProductionIntegrationExecutionAuthorizationPackage
from .integration_execution_authority_readiness import ProductionIntegrationExecutionAuthorityReadiness
from .integration_execution_executor_binding_readiness import ProductionIntegrationExecutionExecutorBindingReadiness
from .integration_execution_executor_binding_preflight import ProductionIntegrationExecutionExecutorBindingPreflight
from .integration_execution_executor_binding_rehearsal import ProductionIntegrationExecutionExecutorBindingRehearsal
from .integration_execution_executor_binding_authorization_review import ProductionIntegrationExecutionExecutorBindingAuthorizationReview
from .integration_execution_executor_binding_authorization_decision import ProductionIntegrationExecutionExecutorBindingAuthorizationDecision
from .integration_execution_executor_binding_authorization_package import ProductionIntegrationExecutionExecutorBindingAuthorizationPackage
from .integration_execution_executor_binding_authorization_package_readiness import ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadiness
from .integration_execution_executor_binding_authorization_package_readiness_preflight import ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflight
from .integration_execution_executor_binding_authorization_package_readiness_rehearsal import ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsal
from .integration_execution_executor_binding_authorization_package_readiness_authorization_review import ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationReview
from .integration_execution_executor_binding_authorization_package_readiness_authorization_decision import ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecision
from .store import CanonicalStore, ContractError, utc_now


class IllegalTransition(ContractError):
    pass


class SyntheticFailure(RuntimeError):
    pass


class IncompleteCompletion(ContractError):
    pass


class RunEngine:
    def __init__(
        self,
        state_root: Path | str,
        edition_date: str,
        mode: str = "synthetic",
        owner: str = "orchestrator",
        failure_injection: FailureInjection | None = None,
        editorial_fixture_root: Path | str | None = None,
        editorial_only: bool = False,
        build_fixture_root: Path | str | None = None,
        build_only: bool = False,
        pre_release_fixture_root: Path | str | None = None,
        validation_only: bool = False,
        render_fixture_root: Path | str | None = None,
        render_only: bool = False,
        release_fixture_root: Path | str | None = None,
        release_only: bool = False,
        evaluation_fixture_root: Path | str | None = None,
        evaluation_only: bool = False,
        operations_fixture_root: Path | str | None = None,
        reconcile_only: bool = False,
        completion_fixture_root: Path | str | None = None,
        completion_only: bool = False,
        readiness_fixture_root: Path | str | None = None,
        readiness_only: bool = False,
        integration_preflight_fixture_root: Path | str | None = None,
        integration_preflight_only: bool = False,
        integration_plan_fixture_root: Path | str | None = None,
        integration_plan_only: bool = False,
        integration_admission_fixture_root: Path | str | None = None,
        integration_admission_only: bool = False,
        integration_execution_preflight_fixture_root: Path | str | None = None,
        integration_execution_preflight_only: bool = False,
        integration_execution_rehearsal_fixture_root: Path | str | None = None,
        integration_execution_rehearsal_only: bool = False,
        integration_execution_authorization_review_fixture_root: Path | str | None = None,
        integration_execution_authorization_review_only: bool = False,
        integration_execution_authorization_decision_fixture_root: Path | str | None = None,
        integration_execution_authorization_decision_only: bool = False,
        integration_execution_authorization_package_fixture_root: Path | str | None = None,
        integration_execution_authorization_package_only: bool = False,
        integration_execution_authority_readiness_fixture_root: Path | str | None = None,
        integration_execution_authority_readiness_only: bool = False,
        integration_execution_executor_binding_readiness_fixture_root: Path | str | None = None,
        integration_execution_executor_binding_readiness_only: bool = False,
        integration_execution_executor_binding_preflight_fixture_root: Path | str | None = None,
        integration_execution_executor_binding_preflight_only: bool = False,
        integration_execution_executor_binding_rehearsal_fixture_root: Path | str | None = None,
        integration_execution_executor_binding_rehearsal_only: bool = False,
        integration_execution_executor_binding_authorization_review_fixture_root: Path | str | None = None,
        integration_execution_executor_binding_authorization_review_only: bool = False,
        integration_execution_executor_binding_authorization_decision_fixture_root: Path | str | None = None,
        integration_execution_executor_binding_authorization_decision_only: bool = False,
        integration_execution_executor_binding_authorization_package_fixture_root: Path | str | None = None,
        integration_execution_executor_binding_authorization_package_only: bool = False,
        integration_execution_executor_binding_authorization_package_readiness_fixture_root: Path | str | None = None,
        integration_execution_executor_binding_authorization_package_readiness_only: bool = False,
        integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root: Path | str | None = None,
        integration_execution_executor_binding_authorization_package_readiness_preflight_only: bool = False,
        integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root: Path | str | None = None,
        integration_execution_executor_binding_authorization_package_readiness_rehearsal_only: bool = False,
        integration_execution_executor_binding_authorization_package_readiness_authorization_review_fixture_root: Path | str | None = None,
        integration_execution_executor_binding_authorization_package_readiness_authorization_review_only: bool = False,
        integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root: Path | str | None = None,
        integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only: bool = False,
    ):
        if mode not in {"synthetic", "shadow", "production"}:
            raise ValueError(f"unsupported mode: {mode}")
        self.store = CanonicalStore(Path(state_root), edition_date, mode)
        self.edition_date = edition_date
        self.mode = mode
        self.run_id = f"dab-{edition_date}-{mode}"
        self.owner = owner
        self.failure_injection = failure_injection
        self._injection_fired = False
        self.editorial_only = editorial_only
        self.build_only = build_only
        self.validation_only = validation_only
        self.render_only = render_only
        self.release_only = release_only
        self.evaluation_only = evaluation_only
        self.reconcile_only = reconcile_only
        self.completion_only = completion_only
        self.readiness_only = readiness_only
        self.integration_preflight_only = integration_preflight_only
        self.integration_plan_only = integration_plan_only
        self.integration_admission_only = integration_admission_only
        self.integration_execution_preflight_only = integration_execution_preflight_only
        self.integration_execution_rehearsal_only = integration_execution_rehearsal_only
        self.integration_execution_authorization_review_only = (
            integration_execution_authorization_review_only
        )
        self.integration_execution_authorization_decision_only = (
            integration_execution_authorization_decision_only
        )
        self.integration_execution_authorization_package_only = (
            integration_execution_authorization_package_only
        )
        self.integration_execution_authority_readiness_only = (
            integration_execution_authority_readiness_only
        )
        self.integration_execution_executor_binding_readiness_only = (
            integration_execution_executor_binding_readiness_only
        )
        self.integration_execution_executor_binding_preflight_only = (
            integration_execution_executor_binding_preflight_only
        )
        self.integration_execution_executor_binding_rehearsal_only = (
            integration_execution_executor_binding_rehearsal_only
        )
        self.integration_execution_executor_binding_authorization_review_only = (
            integration_execution_executor_binding_authorization_review_only
        )
        self.integration_execution_executor_binding_authorization_decision_only = (
            integration_execution_executor_binding_authorization_decision_only
        )
        self.integration_execution_executor_binding_authorization_package_only = (
            integration_execution_executor_binding_authorization_package_only
        )
        self.integration_execution_executor_binding_authorization_package_readiness_only = (
            integration_execution_executor_binding_authorization_package_readiness_only
        )
        self.integration_execution_executor_binding_authorization_package_readiness_preflight_only = (
            integration_execution_executor_binding_authorization_package_readiness_preflight_only
        )
        self.integration_execution_executor_binding_authorization_package_readiness_rehearsal_only = (
            integration_execution_executor_binding_authorization_package_readiness_rehearsal_only
        )
        self.integration_execution_executor_binding_authorization_package_readiness_authorization_review_only = (
            integration_execution_executor_binding_authorization_package_readiness_authorization_review_only
        )
        self.integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only = (
            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only
        )
        if self.integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only and (
            self.editorial_only or self.build_only or self.validation_only or self.render_only
            or self.release_only or self.evaluation_only or self.reconcile_only or self.completion_only
            or self.readiness_only or self.integration_preflight_only or self.integration_plan_only
            or self.integration_admission_only or self.integration_execution_preflight_only
            or self.integration_execution_rehearsal_only or self.integration_execution_authorization_review_only
            or self.integration_execution_authorization_decision_only or self.integration_execution_authorization_package_only
            or self.integration_execution_authority_readiness_only or self.integration_execution_executor_binding_readiness_only
            or self.integration_execution_executor_binding_preflight_only or self.integration_execution_executor_binding_rehearsal_only
            or self.integration_execution_executor_binding_authorization_review_only
            or self.integration_execution_executor_binding_authorization_decision_only
            or self.integration_execution_executor_binding_authorization_package_only
            or self.integration_execution_executor_binding_authorization_package_readiness_only
            or self.integration_execution_executor_binding_authorization_package_readiness_preflight_only
            or self.integration_execution_executor_binding_authorization_package_readiness_rehearsal_only
            or self.integration_execution_executor_binding_authorization_package_readiness_authorization_review_only
        ):
            raise ValueError(
                "integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only "
                "cannot be combined with another bounded execution mode"
            )
        if self.integration_execution_executor_binding_authorization_package_readiness_authorization_review_only and (
            self.editorial_only or self.build_only or self.validation_only or self.render_only
            or self.release_only or self.evaluation_only or self.reconcile_only or self.completion_only
            or self.readiness_only or self.integration_preflight_only or self.integration_plan_only
            or self.integration_admission_only or self.integration_execution_preflight_only
            or self.integration_execution_rehearsal_only or self.integration_execution_authorization_review_only
            or self.integration_execution_authorization_decision_only or self.integration_execution_authorization_package_only
            or self.integration_execution_authority_readiness_only or self.integration_execution_executor_binding_readiness_only
            or self.integration_execution_executor_binding_preflight_only or self.integration_execution_executor_binding_rehearsal_only
            or self.integration_execution_executor_binding_authorization_review_only
            or self.integration_execution_executor_binding_authorization_decision_only
            or self.integration_execution_executor_binding_authorization_package_only
            or self.integration_execution_executor_binding_authorization_package_readiness_only
            or self.integration_execution_executor_binding_authorization_package_readiness_preflight_only
            or self.integration_execution_executor_binding_authorization_package_readiness_rehearsal_only
        ):
            raise ValueError(
                "integration_execution_executor_binding_authorization_package_readiness_authorization_review_only "
                "cannot be combined with another bounded execution mode"
            )
        if self.integration_execution_executor_binding_authorization_package_readiness_rehearsal_only and (
            self.editorial_only or self.build_only or self.validation_only or self.render_only
            or self.release_only or self.evaluation_only or self.reconcile_only or self.completion_only
            or self.readiness_only or self.integration_preflight_only or self.integration_plan_only
            or self.integration_admission_only or self.integration_execution_preflight_only
            or self.integration_execution_rehearsal_only or self.integration_execution_authorization_review_only
            or self.integration_execution_authorization_decision_only or self.integration_execution_authorization_package_only
            or self.integration_execution_authority_readiness_only or self.integration_execution_executor_binding_readiness_only
            or self.integration_execution_executor_binding_preflight_only or self.integration_execution_executor_binding_rehearsal_only
            or self.integration_execution_executor_binding_authorization_review_only
            or self.integration_execution_executor_binding_authorization_decision_only
            or self.integration_execution_executor_binding_authorization_package_only
            or self.integration_execution_executor_binding_authorization_package_readiness_only
            or self.integration_execution_executor_binding_authorization_package_readiness_preflight_only
        ):
            raise ValueError(
                "integration_execution_executor_binding_authorization_package_readiness_rehearsal_only "
                "cannot be combined with another bounded execution mode"
            )
        if self.integration_execution_executor_binding_authorization_package_readiness_preflight_only and (
            self.editorial_only or self.build_only or self.validation_only or self.render_only
            or self.release_only or self.evaluation_only or self.reconcile_only or self.completion_only
            or self.readiness_only or self.integration_preflight_only or self.integration_plan_only
            or self.integration_admission_only or self.integration_execution_preflight_only
            or self.integration_execution_rehearsal_only or self.integration_execution_authorization_review_only
            or self.integration_execution_authorization_decision_only or self.integration_execution_authorization_package_only
            or self.integration_execution_authority_readiness_only or self.integration_execution_executor_binding_readiness_only
            or self.integration_execution_executor_binding_preflight_only or self.integration_execution_executor_binding_rehearsal_only
            or self.integration_execution_executor_binding_authorization_review_only
            or self.integration_execution_executor_binding_authorization_decision_only
            or self.integration_execution_executor_binding_authorization_package_only
            or self.integration_execution_executor_binding_authorization_package_readiness_only
        ):
            raise ValueError(
                "integration_execution_executor_binding_authorization_package_readiness_preflight_only "
                "cannot be combined with another bounded execution mode"
            )
        if self.integration_execution_executor_binding_authorization_package_readiness_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
            or self.readiness_only
            or self.integration_preflight_only
            or self.integration_plan_only
            or self.integration_admission_only
            or self.integration_execution_preflight_only
            or self.integration_execution_rehearsal_only
            or self.integration_execution_authorization_review_only
            or self.integration_execution_authorization_decision_only
            or self.integration_execution_authorization_package_only
            or self.integration_execution_authority_readiness_only
            or self.integration_execution_executor_binding_readiness_only
            or self.integration_execution_executor_binding_preflight_only
            or self.integration_execution_executor_binding_rehearsal_only
            or self.integration_execution_executor_binding_authorization_review_only
            or self.integration_execution_executor_binding_authorization_decision_only
            or self.integration_execution_executor_binding_authorization_package_only
            or self.integration_execution_executor_binding_authorization_package_readiness_preflight_only
        ):
            raise ValueError(
                "integration_execution_executor_binding_authorization_package_readiness_only "
                "cannot be combined with another bounded execution mode"
            )
        if self.render_only and (self.editorial_only or self.build_only or self.validation_only):
            raise ValueError("render_only cannot be combined with earlier bounded execution modes")
        if self.release_only and (
            self.editorial_only or self.build_only or self.validation_only or self.render_only
        ):
            raise ValueError("release_only cannot be combined with earlier bounded execution modes")
        if self.evaluation_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
        ):
            raise ValueError("evaluation_only cannot be combined with earlier bounded execution modes")
        if self.reconcile_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
        ):
            raise ValueError("reconcile_only cannot be combined with earlier bounded execution modes")
        if self.completion_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
        ):
            raise ValueError("completion_only cannot be combined with another bounded execution mode")
        if self.readiness_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
        ):
            raise ValueError("readiness_only cannot be combined with another bounded execution mode")
        if self.integration_preflight_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
            or self.readiness_only
        ):
            raise ValueError(
                "integration_preflight_only cannot be combined with another bounded execution mode"
            )
        if self.integration_plan_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
            or self.readiness_only
            or self.integration_preflight_only
            or self.integration_admission_only
        ):
            raise ValueError(
                "integration_plan_only cannot be combined with another bounded execution mode"
            )
        if self.integration_admission_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
            or self.readiness_only
            or self.integration_preflight_only
            or self.integration_plan_only
        ):
            raise ValueError(
                "integration_admission_only cannot be combined with another bounded execution mode"
            )
        if self.integration_execution_preflight_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
            or self.readiness_only
            or self.integration_preflight_only
            or self.integration_plan_only
            or self.integration_admission_only
        ):
            raise ValueError(
                "integration_execution_preflight_only cannot be combined with another bounded execution mode"
            )
        if self.integration_execution_rehearsal_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
            or self.readiness_only
            or self.integration_preflight_only
            or self.integration_plan_only
            or self.integration_admission_only
            or self.integration_execution_preflight_only
        ):
            raise ValueError(
                "integration_execution_rehearsal_only cannot be combined with another bounded execution mode"
            )
        if self.integration_execution_authorization_review_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
            or self.readiness_only
            or self.integration_preflight_only
            or self.integration_plan_only
            or self.integration_admission_only
            or self.integration_execution_preflight_only
            or self.integration_execution_rehearsal_only
            or self.integration_execution_authorization_decision_only
            or self.integration_execution_authorization_package_only
            or self.integration_execution_authority_readiness_only
        ):
            raise ValueError(
                "integration_execution_authorization_review_only cannot be combined "
                "with another bounded execution mode"
            )
        if self.integration_execution_authorization_decision_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
            or self.readiness_only
            or self.integration_preflight_only
            or self.integration_plan_only
            or self.integration_admission_only
            or self.integration_execution_preflight_only
            or self.integration_execution_rehearsal_only
            or self.integration_execution_authorization_review_only
            or self.integration_execution_authorization_package_only
            or self.integration_execution_authority_readiness_only
        ):
            raise ValueError(
                "integration_execution_authorization_decision_only cannot be combined "
                "with another bounded execution mode"
            )
        if self.integration_execution_authorization_package_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
            or self.readiness_only
            or self.integration_preflight_only
            or self.integration_plan_only
            or self.integration_admission_only
            or self.integration_execution_preflight_only
            or self.integration_execution_rehearsal_only
            or self.integration_execution_authorization_review_only
            or self.integration_execution_authorization_decision_only
            or self.integration_execution_authority_readiness_only
        ):
            raise ValueError(
                "integration_execution_authorization_package_only cannot be combined "
                "with another bounded execution mode"
            )
        if self.integration_execution_authority_readiness_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
            or self.readiness_only
            or self.integration_preflight_only
            or self.integration_plan_only
            or self.integration_admission_only
            or self.integration_execution_preflight_only
            or self.integration_execution_rehearsal_only
            or self.integration_execution_authorization_review_only
            or self.integration_execution_authorization_decision_only
            or self.integration_execution_authorization_package_only
        ):
            raise ValueError(
                "integration_execution_authority_readiness_only cannot be combined "
                "with another bounded execution mode"
            )
        if self.integration_execution_executor_binding_readiness_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
            or self.readiness_only
            or self.integration_preflight_only
            or self.integration_plan_only
            or self.integration_admission_only
            or self.integration_execution_preflight_only
            or self.integration_execution_rehearsal_only
            or self.integration_execution_authorization_review_only
            or self.integration_execution_authorization_decision_only
            or self.integration_execution_authorization_package_only
            or self.integration_execution_authority_readiness_only
        ):
            raise ValueError(
                "integration_execution_executor_binding_readiness_only cannot be combined "
                "with another bounded execution mode"
            )
        if self.integration_execution_executor_binding_preflight_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
            or self.readiness_only
            or self.integration_preflight_only
            or self.integration_plan_only
            or self.integration_admission_only
            or self.integration_execution_preflight_only
            or self.integration_execution_rehearsal_only
            or self.integration_execution_authorization_review_only
            or self.integration_execution_authorization_decision_only
            or self.integration_execution_authorization_package_only
            or self.integration_execution_authority_readiness_only
            or self.integration_execution_executor_binding_readiness_only
        ):
            raise ValueError(
                "integration_execution_executor_binding_preflight_only cannot be combined "
                "with another bounded execution mode"
            )
        if self.integration_execution_executor_binding_rehearsal_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
            or self.readiness_only
            or self.integration_preflight_only
            or self.integration_plan_only
            or self.integration_admission_only
            or self.integration_execution_preflight_only
            or self.integration_execution_rehearsal_only
            or self.integration_execution_authorization_review_only
            or self.integration_execution_authorization_decision_only
            or self.integration_execution_authorization_package_only
            or self.integration_execution_authority_readiness_only
            or self.integration_execution_executor_binding_readiness_only
            or self.integration_execution_executor_binding_preflight_only
        ):
            raise ValueError(
                "integration_execution_executor_binding_rehearsal_only cannot be combined "
                "with another bounded execution mode"
            )
        if self.integration_execution_executor_binding_authorization_review_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
            or self.readiness_only
            or self.integration_preflight_only
            or self.integration_plan_only
            or self.integration_admission_only
            or self.integration_execution_preflight_only
            or self.integration_execution_rehearsal_only
            or self.integration_execution_authorization_review_only
            or self.integration_execution_authorization_decision_only
            or self.integration_execution_authorization_package_only
            or self.integration_execution_authority_readiness_only
            or self.integration_execution_executor_binding_readiness_only
            or self.integration_execution_executor_binding_preflight_only
            or self.integration_execution_executor_binding_rehearsal_only
        ):
            raise ValueError(
                "integration_execution_executor_binding_authorization_review_only cannot be combined "
                "with another bounded execution mode"
            )
        if self.integration_execution_executor_binding_authorization_decision_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
            or self.readiness_only
            or self.integration_preflight_only
            or self.integration_plan_only
            or self.integration_admission_only
            or self.integration_execution_preflight_only
            or self.integration_execution_rehearsal_only
            or self.integration_execution_authorization_review_only
            or self.integration_execution_authorization_decision_only
            or self.integration_execution_authorization_package_only
            or self.integration_execution_authority_readiness_only
            or self.integration_execution_executor_binding_readiness_only
            or self.integration_execution_executor_binding_preflight_only
            or self.integration_execution_executor_binding_rehearsal_only
            or self.integration_execution_executor_binding_authorization_review_only
        ):
            raise ValueError(
                "integration_execution_executor_binding_authorization_decision_only cannot be combined "
                "with another bounded execution mode"
            )
        if self.integration_execution_executor_binding_authorization_package_only and (
            self.editorial_only
            or self.build_only
            or self.validation_only
            or self.render_only
            or self.release_only
            or self.evaluation_only
            or self.reconcile_only
            or self.completion_only
            or self.readiness_only
            or self.integration_preflight_only
            or self.integration_plan_only
            or self.integration_admission_only
            or self.integration_execution_preflight_only
            or self.integration_execution_rehearsal_only
            or self.integration_execution_authorization_review_only
            or self.integration_execution_authorization_decision_only
            or self.integration_execution_authorization_package_only
            or self.integration_execution_authority_readiness_only
            or self.integration_execution_executor_binding_readiness_only
            or self.integration_execution_executor_binding_preflight_only
            or self.integration_execution_executor_binding_rehearsal_only
            or self.integration_execution_executor_binding_authorization_review_only
            or self.integration_execution_executor_binding_authorization_decision_only
        ):
            raise ValueError(
                "integration_execution_executor_binding_authorization_package_only cannot be combined "
                "with another bounded execution mode"
            )
        if editorial_fixture_root is not None:
            self.editorial_fixture_root = Path(editorial_fixture_root)
        elif mode in {"synthetic", "shadow"}:
            self.editorial_fixture_root = Path(__file__).resolve().parents[2] / "fixtures" / "iteration2"
        else:
            self.editorial_fixture_root = None
        if build_fixture_root is not None:
            self.build_fixture_root = Path(build_fixture_root)
        elif mode in {"synthetic", "shadow"}:
            self.build_fixture_root = Path(__file__).resolve().parents[2] / "fixtures" / "iteration3"
        else:
            self.build_fixture_root = None
        if pre_release_fixture_root is not None:
            self.pre_release_fixture_root = Path(pre_release_fixture_root)
        elif mode in {"synthetic", "shadow"}:
            self.pre_release_fixture_root = Path(__file__).resolve().parents[2] / "fixtures" / "iteration4"
        else:
            self.pre_release_fixture_root = None
        if render_fixture_root is not None:
            self.render_fixture_root = Path(render_fixture_root)
        elif mode in {"synthetic", "shadow"}:
            self.render_fixture_root = Path(__file__).resolve().parents[2] / "fixtures" / "iteration5"
        else:
            self.render_fixture_root = None
        if release_fixture_root is not None:
            self.release_fixture_root = Path(release_fixture_root)
        elif mode in {"synthetic", "shadow"}:
            self.release_fixture_root = Path(__file__).resolve().parents[2] / "fixtures" / "iteration6"
        else:
            self.release_fixture_root = None
        if evaluation_fixture_root is not None:
            self.evaluation_fixture_root = Path(evaluation_fixture_root)
        elif mode in {"synthetic", "shadow"}:
            self.evaluation_fixture_root = Path(__file__).resolve().parents[2] / "fixtures" / "iteration7"
        else:
            self.evaluation_fixture_root = None
        if operations_fixture_root is not None:
            self.operations_fixture_root = Path(operations_fixture_root)
        elif mode in {"synthetic", "shadow"}:
            self.operations_fixture_root = Path(__file__).resolve().parents[2] / "fixtures" / "iteration8"
        else:
            self.operations_fixture_root = None
        if completion_fixture_root is not None:
            self.completion_fixture_root = Path(completion_fixture_root)
        elif mode in {"synthetic", "shadow"}:
            self.completion_fixture_root = Path(__file__).resolve().parents[2] / "fixtures" / "iteration9"
        else:
            self.completion_fixture_root = None
        if readiness_fixture_root is not None:
            self.readiness_fixture_root = Path(readiness_fixture_root)
        elif mode in {"synthetic", "shadow"}:
            self.readiness_fixture_root = (
                Path(__file__).resolve().parents[2] / "fixtures" / "iteration10" / "current-blocked"
            )
        else:
            self.readiness_fixture_root = None
        if integration_preflight_fixture_root is not None:
            self.integration_preflight_fixture_root = Path(integration_preflight_fixture_root)
        elif mode in {"synthetic", "shadow"}:
            self.integration_preflight_fixture_root = (
                Path(__file__).resolve().parents[2]
                / "fixtures"
                / "iteration11"
                / "current-unresolved"
            )
        else:
            self.integration_preflight_fixture_root = None
        if integration_plan_fixture_root is not None:
            self.integration_plan_fixture_root = Path(integration_plan_fixture_root)
        elif mode in {"synthetic", "shadow"}:
            self.integration_plan_fixture_root = (
                Path(__file__).resolve().parents[2]
                / "fixtures"
                / "iteration12"
                / "current-blocked"
            )
        else:
            self.integration_plan_fixture_root = None
        if integration_admission_fixture_root is not None:
            self.integration_admission_fixture_root = Path(integration_admission_fixture_root)
        elif mode in {"synthetic", "shadow"}:
            self.integration_admission_fixture_root = (
                Path(__file__).resolve().parents[2]
                / "fixtures"
                / "iteration13"
                / "current-blocked"
            )
        else:
            self.integration_admission_fixture_root = None
        if integration_execution_preflight_fixture_root is not None:
            self.integration_execution_preflight_fixture_root = Path(
                integration_execution_preflight_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_preflight_fixture_root = (
                Path(__file__).resolve().parents[2]
                / "fixtures"
                / "iteration14"
                / "current-blocked"
            )
        else:
            self.integration_execution_preflight_fixture_root = None
        if integration_execution_rehearsal_fixture_root is not None:
            self.integration_execution_rehearsal_fixture_root = Path(
                integration_execution_rehearsal_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_rehearsal_fixture_root = (
                Path(__file__).resolve().parents[2]
                / "fixtures"
                / "iteration15"
                / "current-blocked"
            )
        else:
            self.integration_execution_rehearsal_fixture_root = None
        if integration_execution_authorization_review_fixture_root is not None:
            self.integration_execution_authorization_review_fixture_root = Path(
                integration_execution_authorization_review_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_authorization_review_fixture_root = (
                Path(__file__).resolve().parents[2]
                / "fixtures"
                / "iteration16"
                / "current-blocked"
            )
        else:
            self.integration_execution_authorization_review_fixture_root = None
        if integration_execution_authorization_decision_fixture_root is not None:
            self.integration_execution_authorization_decision_fixture_root = Path(
                integration_execution_authorization_decision_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_authorization_decision_fixture_root = (
                Path(__file__).resolve().parents[2]
                / "fixtures"
                / "iteration17"
                / "current-blocked"
            )
        else:
            self.integration_execution_authorization_decision_fixture_root = None
        if integration_execution_authorization_package_fixture_root is not None:
            self.integration_execution_authorization_package_fixture_root = Path(
                integration_execution_authorization_package_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_authorization_package_fixture_root = (
                Path(__file__).resolve().parents[2]
                / "fixtures"
                / "iteration18"
                / "current-blocked"
            )
        else:
            self.integration_execution_authorization_package_fixture_root = None
        if integration_execution_authority_readiness_fixture_root is not None:
            self.integration_execution_authority_readiness_fixture_root = Path(
                integration_execution_authority_readiness_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_authority_readiness_fixture_root = (
                Path(__file__).resolve().parents[2]
                / "fixtures"
                / "iteration19"
                / "current-blocked"
            )
        else:
            self.integration_execution_authority_readiness_fixture_root = None
        if integration_execution_executor_binding_readiness_fixture_root is not None:
            self.integration_execution_executor_binding_readiness_fixture_root = Path(
                integration_execution_executor_binding_readiness_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_executor_binding_readiness_fixture_root = (
                Path(__file__).resolve().parents[2]
                / "fixtures"
                / "iteration20"
                / "current-blocked"
            )
        else:
            self.integration_execution_executor_binding_readiness_fixture_root = None
        if integration_execution_executor_binding_preflight_fixture_root is not None:
            self.integration_execution_executor_binding_preflight_fixture_root = Path(
                integration_execution_executor_binding_preflight_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_executor_binding_preflight_fixture_root = (
                Path(__file__).resolve().parents[2]
                / "fixtures"
                / "iteration21"
                / "current-blocked"
            )
        else:
            self.integration_execution_executor_binding_preflight_fixture_root = None
        if integration_execution_executor_binding_rehearsal_fixture_root is not None:
            self.integration_execution_executor_binding_rehearsal_fixture_root = Path(
                integration_execution_executor_binding_rehearsal_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_executor_binding_rehearsal_fixture_root = (
                Path(__file__).resolve().parents[2]
                / "fixtures"
                / "iteration22"
                / "current-blocked"
            )
        else:
            self.integration_execution_executor_binding_rehearsal_fixture_root = None
        if integration_execution_executor_binding_authorization_review_fixture_root is not None:
            self.integration_execution_executor_binding_authorization_review_fixture_root = Path(
                integration_execution_executor_binding_authorization_review_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_executor_binding_authorization_review_fixture_root = (
                Path(__file__).resolve().parents[2]
                / "fixtures"
                / "iteration23"
                / "current-blocked"
            )
        else:
            self.integration_execution_executor_binding_authorization_review_fixture_root = None
        if integration_execution_executor_binding_authorization_decision_fixture_root is not None:
            self.integration_execution_executor_binding_authorization_decision_fixture_root = Path(
                integration_execution_executor_binding_authorization_decision_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_executor_binding_authorization_decision_fixture_root = (
                Path(__file__).resolve().parents[2]
                / "fixtures"
                / "iteration24"
                / "current-blocked"
            )
        else:
            self.integration_execution_executor_binding_authorization_decision_fixture_root = None
        if integration_execution_executor_binding_authorization_package_fixture_root is not None:
            self.integration_execution_executor_binding_authorization_package_fixture_root = Path(
                integration_execution_executor_binding_authorization_package_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_executor_binding_authorization_package_fixture_root = (
                Path(__file__).resolve().parents[2]
                / "fixtures"
                / "iteration25"
                / "current-blocked"
            )
        else:
            self.integration_execution_executor_binding_authorization_package_fixture_root = None
        if integration_execution_executor_binding_authorization_package_readiness_fixture_root is not None:
            self.integration_execution_executor_binding_authorization_package_readiness_fixture_root = Path(
                integration_execution_executor_binding_authorization_package_readiness_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_executor_binding_authorization_package_readiness_fixture_root = (
                Path(__file__).resolve().parents[2]
                / "fixtures"
                / "iteration26"
                / "current-blocked"
            )
        else:
            self.integration_execution_executor_binding_authorization_package_readiness_fixture_root = None
        if integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root is not None:
            self.integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root = Path(
                integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root = (
                Path(__file__).resolve().parents[2] / "fixtures" / "iteration27" / "current-blocked"
            )
        else:
            self.integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root = None
        if integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root is not None:
            self.integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root = Path(
                integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root = (
                Path(__file__).resolve().parents[2] / "fixtures" / "iteration28" / "current-blocked"
            )
        else:
            self.integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root = None
        if integration_execution_executor_binding_authorization_package_readiness_authorization_review_fixture_root is not None:
            self.integration_execution_executor_binding_authorization_package_readiness_authorization_review_fixture_root = Path(
                integration_execution_executor_binding_authorization_package_readiness_authorization_review_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_executor_binding_authorization_package_readiness_authorization_review_fixture_root = (
                Path(__file__).resolve().parents[2] / "fixtures" / "iteration29" / "current-blocked"
            )
        else:
            self.integration_execution_executor_binding_authorization_package_readiness_authorization_review_fixture_root = None
        if integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root is not None:
            self.integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root = Path(
                integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root
            )
        elif mode in {"synthetic", "shadow"}:
            self.integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root = (
                Path(__file__).resolve().parents[2] / "fixtures" / "iteration30" / "current-blocked"
            )
        else:
            self.integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root = None

    def _new_run(self) -> dict[str, Any]:
        now = utc_now()
        return {
            "schema_version": RUN_SCHEMA_VERSION,
            "run_id": self.run_id,
            "edition_date": self.edition_date,
            "mode": self.mode,
            "current_state": "Ready",
            "completion_status": "in_progress",
            "created_at": now,
            "updated_at": now,
            "stage_executions": {},
            "stage_receipts": {},
            "recovery_target": None,
            "incident_count": 0,
            "manual_intervention": False,
            "anti_rework": {
                "locked_stage_reexecutions": 0,
                "full_pipeline_restarts": 0,
                "artifact_reuses": 0,
                "artifact_rebuilds": 0,
            },
        }

    def load_or_create(self) -> dict[str, Any]:
        run = self.store.load_run()
        if run:
            return run
        run = self._new_run()
        self.store.write_run(run)
        return run

    def transition(self, run: dict[str, Any], target: str) -> None:
        current = run["current_state"]
        if target not in LEGAL_TRANSITIONS[current]:
            raise IllegalTransition(f"illegal transition {current} -> {target}")
        run["current_state"] = target
        self.store.write_run(run)

    def _count_stage(self, run: dict[str, Any], stage: str) -> None:
        run["stage_executions"][stage] = run["stage_executions"].get(stage, 0) + 1
        self.store.write_run(run)

    def _input_digests(self, artifact_type: str) -> list[str]:
        values: list[str] = []
        for dependency in ARTIFACT_DEPENDENCIES[artifact_type]:
            record = self.store.load_artifact(dependency)
            if not record or record.get("status") != "locked":
                raise ContractError(f"dependency {dependency} is not locked for {artifact_type}")
            values.append(record["content_digest"])
        return values

    def _ensure_artifact(
        self,
        run: dict[str, Any],
        artifact_type: str,
        stage: str,
        data_factory: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        existing = self.store.load_artifact(artifact_type)
        if existing and existing.get("status") == "locked":
            current_inputs = sorted(self._input_digests(artifact_type))
            if sorted(existing.get("input_digests", [])) == current_inputs:
                run["anti_rework"]["artifact_reuses"] += 1
                self.store.write_run(run)
                return existing
            self.store.invalidate(artifact_type, "dependency_digest_changed")
        self._count_stage(run, stage)
        input_digests = self._input_digests(artifact_type)
        artifact, reused = self.store.lock_artifact(
            artifact_type=artifact_type,
            artifact_id=f"{self.run_id}:{artifact_type}",
            data=data_factory(),
            produced_by_stage=stage,
            input_digests=input_digests,
        )
        if reused:
            run["anti_rework"]["artifact_reuses"] += 1
        else:
            run["anti_rework"]["artifact_rebuilds"] += 1
        self.store.write_run(run)
        return artifact

    def _editorial_pipeline(self) -> DiscoveryEditorialPipeline:
        if self.editorial_fixture_root is None:
            raise ContractError(
                "production discovery is intentionally unconfigured in Iteration 3; "
                "use synthetic/shadow fixtures until a later approved cutover iteration"
            )
        injection = None
        if (
            self.failure_injection
            and self.failure_injection.stage == "Acquiring"
            and self.failure_injection.candidate_id
        ):
            injection = EditorialFailureInjection(
                candidate_id=self.failure_injection.candidate_id,
                failure_class=self.failure_injection.failure_class,
            )
        return DiscoveryEditorialPipeline(
            self.store,
            self.edition_date,
            self.editorial_fixture_root,
            injection,
        )

    def _build_pipeline(self) -> BuildStagePipeline:
        if self.build_fixture_root is None:
            raise ContractError(
                "production Build-stage enrichment is intentionally unconfigured in Iteration 3; "
                "use synthetic/shadow fixtures until a later approved cutover iteration"
            )
        injection = None
        if (
            self.failure_injection
            and self.failure_injection.stage == "Building"
            and self.failure_injection.candidate_id
            and not self.failure_injection.candidate_id.startswith("image:")
        ):
            injection = BuildFailureInjection(
                boundary_id=self.failure_injection.candidate_id,
                failure_class=self.failure_injection.failure_class,
            )
        return BuildStagePipeline(
            self.store,
            self.edition_date,
            self.build_fixture_root,
            injection,
        )

    def _pre_release_pipeline(self) -> PreReleasePipeline:
        failure_boundary_id = None
        failure_class = "synthetic_image_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "Building"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("image:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return PreReleasePipeline(
            self.store,
            self.edition_date,
            self.mode,
            self.pre_release_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _render_pipeline(self) -> ReaderSurfaceRenderer:
        failure_boundary_id = None
        failure_class = "synthetic_render_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "Validating"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("render:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ReaderSurfaceRenderer(
            self.store,
            self.edition_date,
            self.mode,
            self.render_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _release_pipeline(self) -> ShadowReleasePipeline:
        failure_boundary_id = None
        failure_class = "synthetic_release_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage in {"Releasing", "Deployed"}
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("release:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ShadowReleasePipeline(
            self.store,
            self.edition_date,
            self.mode,
            self.release_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _evaluation_pipeline(self) -> PostPublicationEvaluationPipeline:
        failure_boundary_id = None
        failure_class = "synthetic_evaluation_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "PostPublicationEvaluation"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("evaluation:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return PostPublicationEvaluationPipeline(
            self.store,
            self.edition_date,
            self.mode,
            self.evaluation_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _operations_pipeline(self) -> OperationsReconciliationPipeline:
        failure_boundary_id = None
        failure_class = "synthetic_operations_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "OperationsReconciled"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("operations:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return OperationsReconciliationPipeline(
            self.store,
            self.edition_date,
            self.mode,
            self.operations_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _completion_pipeline(self) -> FinalCompletionPipeline:
        failure_boundary_id = None
        failure_class = "synthetic_completion_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "OperationsReconciled"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("completion:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return FinalCompletionPipeline(
            self.store,
            self.edition_date,
            self.mode,
            self.completion_fixture_root,
            self.operations_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _readiness_pipeline(self) -> ProductionReadinessPipeline:
        failure_boundary_id = None
        failure_class = "synthetic_readiness_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("readiness:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionReadinessPipeline(
            self.store,
            self.edition_date,
            self.mode,
            self.readiness_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_preflight_pipeline(self) -> ProductionIntegrationPreflight:
        failure_boundary_id = None
        failure_class = "synthetic_integration_preflight_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("preflight:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationPreflight(
            self.store,
            self.edition_date,
            self.mode,
            self.integration_preflight_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_plan_pipeline(self) -> ProductionIntegrationPlan:
        failure_boundary_id = None
        failure_class = "synthetic_integration_plan_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("plan:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationPlan(
            self.store,
            self.edition_date,
            self.mode,
            self.integration_plan_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_admission_pipeline(self) -> ProductionIntegrationAdmission:
        failure_boundary_id = None
        failure_class = "synthetic_integration_admission_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("admission:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationAdmission(
            self.store,
            self.edition_date,
            self.mode,
            self.integration_admission_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_execution_preflight_pipeline(
        self,
    ) -> ProductionIntegrationExecutionPreflight:
        failure_boundary_id = None
        failure_class = "synthetic_integration_execution_preflight_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("execution_preflight:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionPreflight(
            self.store,
            self.edition_date,
            self.mode,
            self.integration_execution_preflight_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_execution_rehearsal_pipeline(
        self,
    ) -> ProductionIntegrationExecutionRehearsal:
        failure_boundary_id = None
        failure_class = "synthetic_integration_execution_rehearsal_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("execution_rehearsal:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionRehearsal(
            self.store,
            self.edition_date,
            self.mode,
            self.integration_execution_rehearsal_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_execution_authorization_review_pipeline(
        self,
    ) -> ProductionIntegrationExecutionAuthorizationReview:
        failure_boundary_id = None
        failure_class = (
            "synthetic_integration_execution_authorization_review_boundary_failure"
        )
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("authorization_review:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionAuthorizationReview(
            self.store,
            self.edition_date,
            self.mode,
            self.integration_execution_authorization_review_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_execution_authorization_decision_pipeline(
        self,
    ) -> ProductionIntegrationExecutionAuthorizationDecision:
        failure_boundary_id = None
        failure_class = (
            "synthetic_integration_execution_authorization_decision_boundary_failure"
        )
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("authorization_decision:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionAuthorizationDecision(
            self.store,
            self.edition_date,
            self.mode,
            self.integration_execution_authorization_decision_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_execution_authorization_package_pipeline(
        self,
    ) -> ProductionIntegrationExecutionAuthorizationPackage:
        failure_boundary_id = None
        failure_class = (
            "synthetic_integration_execution_authorization_package_boundary_failure"
        )
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("authorization_package:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionAuthorizationPackage(
            self.store,
            self.edition_date,
            self.mode,
            self.integration_execution_authorization_package_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_execution_authority_readiness_pipeline(
        self,
    ) -> ProductionIntegrationExecutionAuthorityReadiness:
        failure_boundary_id = None
        failure_class = "synthetic_integration_execution_authority_readiness_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("authority_readiness:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionAuthorityReadiness(
            self.store,
            self.edition_date,
            self.mode,
            self.integration_execution_authority_readiness_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_execution_executor_binding_readiness_pipeline(
        self,
    ) -> ProductionIntegrationExecutionExecutorBindingReadiness:
        failure_boundary_id = None
        failure_class = "synthetic_integration_execution_executor_binding_readiness_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("executor_binding_readiness:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionExecutorBindingReadiness(
            self.store,
            self.edition_date,
            self.mode,
            self.integration_execution_executor_binding_readiness_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )
    def _integration_execution_executor_binding_preflight_pipeline(
        self,
    ) -> ProductionIntegrationExecutionExecutorBindingPreflight:
        failure_boundary_id = None
        failure_class = "synthetic_integration_execution_executor_binding_preflight_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("executor_binding_preflight:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionExecutorBindingPreflight(
            self.store,
            self.edition_date,
            self.mode,
            self.integration_execution_executor_binding_preflight_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_execution_executor_binding_rehearsal_pipeline(
        self,
    ) -> ProductionIntegrationExecutionExecutorBindingRehearsal:
        failure_boundary_id = None
        failure_class = "synthetic_integration_execution_executor_binding_rehearsal_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("executor_binding_rehearsal:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionExecutorBindingRehearsal(
            self.store,
            self.edition_date,
            self.mode,
            self.integration_execution_executor_binding_rehearsal_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_execution_executor_binding_authorization_review_pipeline(
        self,
    ) -> ProductionIntegrationExecutionExecutorBindingAuthorizationReview:
        failure_boundary_id = None
        failure_class = "synthetic_integration_execution_executor_binding_authorization_review_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("executor_binding_authorization_review:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionExecutorBindingAuthorizationReview(
            self.store,
            self.edition_date,
            self.mode,
            self.integration_execution_executor_binding_authorization_review_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_execution_executor_binding_authorization_decision_pipeline(
        self,
    ) -> ProductionIntegrationExecutionExecutorBindingAuthorizationDecision:
        failure_boundary_id = None
        failure_class = "synthetic_integration_execution_executor_binding_authorization_decision_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("executor_binding_authorization_decision:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionExecutorBindingAuthorizationDecision(
            self.store,
            self.edition_date,
            self.mode,
            self.integration_execution_executor_binding_authorization_decision_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_execution_executor_binding_authorization_package_pipeline(
        self,
    ) -> ProductionIntegrationExecutionExecutorBindingAuthorizationPackage:
        failure_boundary_id = None
        failure_class = "synthetic_integration_execution_executor_binding_authorization_package_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith("executor_binding_authorization_package:")
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionExecutorBindingAuthorizationPackage(
            self.store,
            self.edition_date,
            self.mode,
            self.integration_execution_executor_binding_authorization_package_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_execution_executor_binding_authorization_package_readiness_pipeline(
        self,
    ) -> ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadiness:
        failure_boundary_id = None
        failure_class = "synthetic_integration_execution_executor_binding_authorization_package_readiness_boundary_failure"
        if (
            self.failure_injection
            and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith(
                "executor_binding_authorization_package_readiness:"
            )
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadiness(
            self.store,
            self.edition_date,
            self.mode,
            self.integration_execution_executor_binding_authorization_package_readiness_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_execution_executor_binding_authorization_package_readiness_preflight_pipeline(
        self,
    ) -> ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflight:
        failure_boundary_id = None
        failure_class = "synthetic_integration_execution_executor_binding_authorization_package_readiness_preflight_boundary_failure"
        if (
            self.failure_injection and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith(
                "executor_binding_authorization_package_readiness_preflight:"
            )
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflight(
            self.store, self.edition_date, self.mode,
            self.integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_execution_executor_binding_authorization_package_readiness_rehearsal_pipeline(
        self,
    ) -> ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsal:
        failure_boundary_id = None
        failure_class = "synthetic_integration_execution_executor_binding_authorization_package_readiness_rehearsal_boundary_failure"
        if (
            self.failure_injection and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith(
                "executor_binding_authorization_package_readiness_rehearsal:"
            )
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsal(
            self.store, self.edition_date, self.mode,
            self.integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_execution_executor_binding_authorization_package_readiness_authorization_review_pipeline(
        self,
    ) -> ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationReview:
        failure_boundary_id = None
        failure_class = "synthetic_integration_execution_executor_binding_authorization_package_readiness_authorization_review_boundary_failure"
        if (
            self.failure_injection and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith(
                "executor_binding_authorization_package_readiness_authorization_review:"
            )
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationReview(
            self.store, self.edition_date, self.mode,
            self.integration_execution_executor_binding_authorization_package_readiness_authorization_review_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _integration_execution_executor_binding_authorization_package_readiness_authorization_decision_pipeline(
        self,
    ) -> ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecision:
        failure_boundary_id = None
        failure_class = "synthetic_integration_execution_executor_binding_authorization_package_readiness_authorization_decision_boundary_failure"
        if (
            self.failure_injection and self.failure_injection.stage == "Complete"
            and self.failure_injection.candidate_id
            and self.failure_injection.candidate_id.startswith(
                "executor_binding_authorization_package_readiness_authorization_decision:"
            )
        ):
            failure_boundary_id = self.failure_injection.candidate_id
            failure_class = self.failure_injection.failure_class
        return ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecision(
            self.store, self.edition_date, self.mode,
            self.integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root,
            failure_boundary_id=failure_boundary_id,
            failure_class=failure_class,
        )

    def _rating_contract(self) -> dict[str, Any]:
        return {
            "contract_version": RATING_CONTRACT_VERSION,
            "scale": {"min": 1, "max": 5, "step": 1},
            "change_in_session": True,
            "aggregate": "arithmetic_mean_of_recorded_values",
            "privacy": "sender_rating_not_embedded_in_shared_copy",
            "missing_states": ["missing", "suppressed", "unavailable"],
            "legacy_policy": "preserve_original_contract_version_no_silent_conversion",
        }

    def _maybe_inject(self, stage: str) -> None:
        if (
            self.failure_injection
            and not self._injection_fired
            and self.failure_injection.stage == stage
            and not self.failure_injection.candidate_id
        ):
            self._injection_fired = True
            raise SyntheticFailure(self.failure_injection.failure_class)

    def _record_failure(self, run: dict[str, Any], failed_stage: str, exc: Exception) -> None:
        prior = run["current_state"]
        if prior != "Recovering":
            self.transition(run, "Recovering")
        run["recovery_target"] = failed_stage
        run["incident_count"] += 1
        retained = []
        for artifact_type in (
            "discovery", "edition", "media", "images", "watchlist", "book-bridges",
            "rating-contract", "publication-bundle", "reader-render", "route-manifest",
            "release-package", "shadow-deployment", "live-verification",
            "book-change-evaluation", "command-center-projection", "projection-watermark",
            "completion", "readiness-admission", "production-integration-preflight",
            "production-integration-plan", "production-integration-admission",
        ):
            artifact = self.store.load_artifact(artifact_type)
            if artifact and artifact.get("status") == "locked":
                retained.append(artifact_type)
        incident = {
            "schema_version": SCHEMA_VERSION,
            "incident_id": f"{self.run_id}:incident:{run['incident_count']}",
            "run_id": self.run_id,
            "edition_date": self.edition_date,
            "failed_stage": failed_stage,
            "failure_class": str(exc),
            "retained_locks": retained,
            "invalidated_artifacts": [],
            "repair_action": "resume_failed_boundary",
            "attempt": run["incident_count"] + 1,
            "result": "pending_recovery",
            "created_at": utc_now(),
        }
        candidate_id = getattr(exc, "candidate_id", None)
        if candidate_id:
            incident["candidate_id"] = candidate_id
        if isinstance(exc, EditorialCandidateFailure):
            packet_dir = self.store.run_dir / "evidence-packets"
            incident["retained_evidence_packets"] = sorted(
                path.stem for path in packet_dir.glob("*.json")
            ) if packet_dir.exists() else []
        if isinstance(exc, BuildBoundaryFailure):
            incident["boundary_type"] = exc.boundary_type
            incident["boundary_id"] = exc.boundary_id
            incident["retained_build_state"] = {
                name: bool((self.store.run_dir / f"{name}-state.json").exists())
                for name in ("media", "watchlist", "bridges")
            }
        if isinstance(exc, ImageBoundaryFailure):
            incident["boundary_type"] = exc.boundary_type
            incident["boundary_id"] = exc.boundary_id
            image_state = self.store.read_json(self.store.run_dir / "image-state.json") or {}
            incident["retained_image_state"] = {
                "accepted_story_ids": sorted((image_state.get("accepted") or {}).keys()),
                "attempts": deepcopy(image_state.get("attempts") or {}),
            }
        if isinstance(exc, ValidationBoundaryFailure):
            incident["boundary_type"] = exc.boundary_type
            incident["boundary_id"] = exc.boundary_id
            incident["validation_invariant"] = exc.invariant
        if isinstance(exc, RenderBoundaryFailure):
            incident["boundary_type"] = exc.boundary_type
            incident["boundary_id"] = exc.boundary_id
            render_state = self.store.read_json(self.store.run_dir / "reader-render-state.json") or {}
            incident["retained_render_state"] = {
                "completed_route_ids": sorted((render_state.get("outputs") or {}).keys()),
                "attempts": deepcopy(render_state.get("attempts") or {}),
            }
        if isinstance(exc, ReleaseBoundaryFailure):
            incident["boundary_type"] = exc.boundary_type
            incident["boundary_id"] = exc.boundary_id
            release_state = self.store.read_json(self.store.run_dir / "shadow-deployment-state.json") or {}
            incident["retained_release_state"] = {
                "completed_route_ids": sorted((release_state.get("outputs") or {}).keys()),
                "attempts": deepcopy(release_state.get("attempts") or {}),
            }
        if isinstance(exc, EvaluationBoundaryFailure):
            incident["boundary_type"] = exc.boundary_type
            incident["boundary_id"] = exc.boundary_id
            evaluation_state = self.store.read_json(
                self.store.run_dir / "post-publication-evaluation-state.json"
            ) or {}
            incident["retained_evaluation_state"] = {
                "completed_item_ids": sorted((evaluation_state.get("evaluations") or {}).keys()),
                "attempts": deepcopy(evaluation_state.get("attempts") or {}),
            }
        if isinstance(exc, OperationsBoundaryFailure):
            incident["boundary_type"] = exc.boundary_type
            incident["boundary_id"] = exc.boundary_id
            operations_state = self.store.read_json(
                self.store.run_dir / "iteration8-operations-state.json"
            ) or {}
            incident["retained_operations_state"] = {
                "attempts": deepcopy(operations_state.get("attempts") or {}),
                "metrics": deepcopy(operations_state.get("metrics") or {}),
            }
        if isinstance(exc, CompletionBoundaryFailure):
            incident["boundary_type"] = exc.boundary_type
            incident["boundary_id"] = exc.boundary_id
            completion_state = self.store.read_json(
                self.store.run_dir / "iteration9-completion-state.json"
            ) or {}
            incident["retained_completion_state"] = {
                "attempts": deepcopy(completion_state.get("attempts") or {}),
                "metrics": deepcopy(completion_state.get("metrics") or {}),
                "completion_artifact_locked": bool(
                    (self.store.load_artifact("completion") or {}).get("status") == "locked"
                ),
                "final_receipt_present": bool(
                    (self.store.run_dir / "iteration9-final-completion-receipt.json").exists()
                ),
            }
        self.store.write_incident(incident)
        self.store.write_run(run)

    def _recover_if_needed(self, run: dict[str, Any]) -> None:
        if run["current_state"] != "Recovering":
            return
        target = run.get("recovery_target")
        if not target:
            raise ContractError("Recovering state missing recovery_target")
        self.transition(run, target)
        incident = self.store.load_incident()
        if incident:
            receipt = {
                "incident_id": incident["incident_id"],
                "failed_stage": incident["failed_stage"],
                "failure_class": incident["failure_class"],
                "retained_locks": incident["retained_locks"],
                "invalidated_artifacts": incident["invalidated_artifacts"],
                "repair_action": incident["repair_action"],
                "attempt": incident["attempt"],
                "result": "recovered",
                "recovered_at": utc_now(),
            }
            for key in (
                "candidate_id",
                "retained_evidence_packets",
                "boundary_type",
                "boundary_id",
                "retained_build_state",
                "retained_image_state",
                "retained_render_state",
                "retained_release_state",
                "retained_evaluation_state",
                "retained_operations_state",
                "retained_completion_state",
                "validation_invariant",
            ):
                if key in incident:
                    receipt[key] = deepcopy(incident[key])
            incident["recovery_receipt"] = receipt
            incident["result"] = "recovered"
            self.store.write_incident(incident)
        run["recovery_target"] = None
        self.store.write_run(run)

    def _book_evaluation(self) -> dict[str, Any]:
        bundle = self.store.load_artifact("publication-bundle")
        return {
            "evaluated_item_types": ["article", "video", "podcast"],
            "all_included_items_evaluated": True,
            "proposal_count": 0,
            "result": "0 proposals — all included items evaluated; no material book change warranted",
            "final_production_identity": f"synthetic-prod:{bundle['content_digest']}",
        }

    def _projection_watermark(self) -> dict[str, Any]:
        bundle = self.store.load_artifact("publication-bundle")
        evaluation = self.store.load_artifact("book-change-evaluation")
        return {
            "projection_schema_version": PROJECTION_SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "run_id": self.run_id,
            "canonical_record_digest": bundle["content_digest"],
            "final_production_identity": f"synthetic-prod:{bundle['content_digest']}",
            "completion_event_id": f"{self.run_id}:completion",
            "book_change_evaluation_digest": evaluation["content_digest"],
            "synced_at": utc_now(),
        }

    def _completion(self, run: dict[str, Any]) -> dict[str, Any]:
        bundle = self.store.load_artifact("publication-bundle")
        evaluation = self.store.load_artifact("book-change-evaluation")
        watermark = self.store.load_artifact("projection-watermark")
        receipts = {
            "publication_bundle_digest": bundle["content_digest"] if bundle else None,
            "deployment_identity": run["stage_receipts"].get("deployment_identity"),
            "live_verification": run["stage_receipts"].get("live_verification"),
            "book_change_evaluation_digest": evaluation["content_digest"] if evaluation else None,
            "projection_watermark_digest": watermark["content_digest"] if watermark else None,
        }
        missing = [name for name in MANDATORY_COMPLETION_RECEIPTS if not receipts.get(name)]
        if missing:
            raise IncompleteCompletion(f"missing mandatory receipts: {', '.join(missing)}")
        return {
            "completion_event_id": f"{self.run_id}:completion",
            "edition_date": self.edition_date,
            "run_id": self.run_id,
            "final_production_identity": watermark["data"]["final_production_identity"],
            "publication_bundle_digest": bundle["content_digest"],
            "deployment_identity": receipts["deployment_identity"],
            "live_verification_timestamp": receipts["live_verification"]["verified_at"],
            "book_change_evaluation_status": "complete",
            "command_center_watermark": watermark["content_digest"],
            "incident_count": run["incident_count"],
            "manual_intervention": run["manual_intervention"],
            "anti_rework": deepcopy(run["anti_rework"]),
            "overall_state": "Complete",
        }

    def run(self) -> dict[str, Any]:
        run = self.load_or_create()
        if run["current_state"] == "Complete":
            if (
                self.completion_only
                or self.readiness_only
                or self.integration_preflight_only
                or self.integration_plan_only
                or self.integration_admission_only
                or self.integration_execution_preflight_only
                or self.integration_execution_rehearsal_only
                or self.integration_execution_authorization_review_only
                or self.integration_execution_authorization_decision_only
                or self.integration_execution_authorization_package_only
                or self.integration_execution_authority_readiness_only
                or self.integration_execution_executor_binding_readiness_only
                or self.integration_execution_executor_binding_preflight_only
                or self.integration_execution_executor_binding_rehearsal_only
                or self.integration_execution_executor_binding_authorization_review_only
                or self.integration_execution_executor_binding_authorization_decision_only
                or self.integration_execution_executor_binding_authorization_package_only
                or self.integration_execution_executor_binding_authorization_package_readiness_only
                or self.integration_execution_executor_binding_authorization_package_readiness_preflight_only
                or self.integration_execution_executor_binding_authorization_package_readiness_rehearsal_only
                or self.integration_execution_executor_binding_authorization_package_readiness_authorization_review_only
                or self.integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only
            ):
                self.store.acquire_lease(self.run_id, self.owner)
                try:
                    self._completion_pipeline().validate_completed_run(
                        run, record_reuse=not (
                            self.integration_execution_executor_binding_authorization_review_only
                            or self.integration_execution_executor_binding_authorization_decision_only
                            or self.integration_execution_executor_binding_authorization_package_only
                            or self.integration_execution_executor_binding_authorization_package_readiness_only
                            or self.integration_execution_executor_binding_authorization_package_readiness_preflight_only
                            or self.integration_execution_executor_binding_authorization_package_readiness_rehearsal_only
                            or self.integration_execution_executor_binding_authorization_package_readiness_authorization_review_only
                            or self.integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only
                        )
                    )
                    if self.readiness_only:
                        readiness = self._readiness_pipeline()
                        evaluation = readiness.prepare(run)
                        existing = self.store.load_artifact("readiness-admission")
                        readiness.validate_existing(existing, run, evaluation)
                        artifact = self._ensure_artifact(
                            run,
                            "readiness-admission",
                            "complete:readiness",
                            lambda: readiness.build_readiness(run, evaluation),
                        )
                        readiness.finalize(artifact)
                    if self.integration_preflight_only:
                        preflight = self._integration_preflight_pipeline()
                        evaluation = preflight.prepare(run)
                        existing = self.store.load_artifact("production-integration-preflight")
                        preflight.validate_existing(existing, run, evaluation)
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-preflight",
                            "complete:integration-preflight",
                            lambda: preflight.build_preflight(run, evaluation),
                        )
                        preflight.finalize(artifact)
                    if self.integration_plan_only:
                        plan = self._integration_plan_pipeline()
                        compiled = plan.prepare(run)
                        existing = self.store.load_artifact("production-integration-plan")
                        plan.validate_existing(existing, run, compiled)
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-plan",
                            "complete:integration-plan",
                            lambda: plan.build_plan(run, compiled),
                        )
                        plan.finalize(artifact)
                    if self.integration_admission_only:
                        admission = self._integration_admission_pipeline()
                        evaluated = admission.prepare(run)
                        existing = self.store.load_artifact("production-integration-admission")
                        admission.validate_existing(existing, run, evaluated)
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-admission",
                            "complete:integration-admission",
                            lambda: admission.build_admission(run, evaluated),
                        )
                        admission.finalize(artifact)
                    if self.integration_execution_preflight_only:
                        execution_preflight = self._integration_execution_preflight_pipeline()
                        evaluated = execution_preflight.prepare(run)
                        existing = self.store.load_artifact(
                            "production-integration-execution-preflight"
                        )
                        execution_preflight.validate_existing(existing, run, evaluated)
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-preflight",
                            "complete:integration-execution-preflight",
                            lambda: execution_preflight.build_preflight(run, evaluated),
                        )
                        execution_preflight.finalize(artifact)
                    if self.integration_execution_rehearsal_only:
                        execution_rehearsal = self._integration_execution_rehearsal_pipeline()
                        evaluated = execution_rehearsal.prepare(run)
                        existing = self.store.load_artifact(
                            "production-integration-execution-rehearsal"
                        )
                        execution_rehearsal.validate_existing(existing, run, evaluated)
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-rehearsal",
                            "complete:integration-execution-rehearsal",
                            lambda: execution_rehearsal.build_rehearsal(run, evaluated),
                        )
                        execution_rehearsal.finalize(artifact)
                    if self.integration_execution_authorization_review_only:
                        authorization_review = (
                            self._integration_execution_authorization_review_pipeline()
                        )
                        evaluated = authorization_review.prepare(run)
                        existing = self.store.load_artifact(
                            "production-integration-execution-authorization-review"
                        )
                        authorization_review.validate_existing(
                            existing, run, evaluated
                        )
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-authorization-review",
                            "complete:integration-execution-authorization-review",
                            lambda: authorization_review.build_authorization_review(
                                run, evaluated
                            ),
                        )
                        authorization_review.finalize(artifact)
                    if self.integration_execution_authorization_decision_only:
                        authorization_decision = (
                            self._integration_execution_authorization_decision_pipeline()
                        )
                        evaluated = authorization_decision.prepare(run)
                        existing = self.store.load_artifact(
                            "production-integration-execution-authorization-decision"
                        )
                        authorization_decision.validate_existing(existing, run, evaluated)
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-authorization-decision",
                            "complete:integration-execution-authorization-decision",
                            lambda: authorization_decision.build_authorization_decision(
                                run, evaluated
                            ),
                        )
                        authorization_decision.finalize(artifact)
                    if self.integration_execution_authorization_package_only:
                        authorization_package = self._integration_execution_authorization_package_pipeline()
                        evaluated = authorization_package.prepare(run)
                        existing = self.store.load_artifact("production-integration-execution-authorization-package")
                        authorization_package.validate_existing(existing, run, evaluated)
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-authorization-package",
                            "complete:integration-execution-authorization-package",
                            lambda: authorization_package.build_authorization_package(run, evaluated),
                        )
                        authorization_package.finalize(artifact)
                    if self.integration_execution_authority_readiness_only:
                        authority_readiness = self._integration_execution_authority_readiness_pipeline()
                        evaluated = authority_readiness.prepare(run)
                        existing = self.store.load_artifact("production-integration-execution-authority-readiness")
                        authority_readiness.validate_existing(existing, run, evaluated)
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-authority-readiness",
                            "complete:integration-execution-authority-readiness",
                            lambda: authority_readiness.build_authority_readiness(run, evaluated),
                        )
                        authority_readiness.finalize(artifact)
                    if self.integration_execution_executor_binding_readiness_only:
                        executor_binding_readiness = (
                            self._integration_execution_executor_binding_readiness_pipeline()
                        )
                        evaluated = executor_binding_readiness.prepare(run)
                        existing = self.store.load_artifact(
                            "production-integration-execution-executor-binding-readiness"
                        )
                        executor_binding_readiness.validate_existing(existing, run, evaluated)
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-executor-binding-readiness",
                            "complete:integration-execution-executor-binding-readiness",
                            lambda: executor_binding_readiness.build_executor_binding_readiness(
                                run, evaluated
                            ),
                        )
                        executor_binding_readiness.finalize(artifact)
                    if self.integration_execution_executor_binding_preflight_only:
                        executor_binding_preflight = (
                            self._integration_execution_executor_binding_preflight_pipeline()
                        )
                        evaluated = executor_binding_preflight.prepare(run)
                        existing = self.store.load_artifact(
                            "production-integration-execution-executor-binding-preflight"
                        )
                        executor_binding_preflight.validate_existing(existing, run, evaluated)
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-executor-binding-preflight",
                            "complete:integration-execution-executor-binding-preflight",
                            lambda: executor_binding_preflight.build_executor_binding_preflight(
                                run, evaluated
                            ),
                        )
                        executor_binding_preflight.finalize(artifact)
                    if self.integration_execution_executor_binding_rehearsal_only:
                        executor_binding_rehearsal = (
                            self._integration_execution_executor_binding_rehearsal_pipeline()
                        )
                        evaluated = executor_binding_rehearsal.prepare(run)
                        existing = self.store.load_artifact(
                            "production-integration-execution-executor-binding-rehearsal"
                        )
                        executor_binding_rehearsal.validate_existing(existing, run, evaluated)
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-executor-binding-rehearsal",
                            "complete:integration-execution-executor-binding-rehearsal",
                            lambda: executor_binding_rehearsal.build_executor_binding_rehearsal(
                                run, evaluated
                            ),
                        )
                        executor_binding_rehearsal.finalize(artifact)
                    if self.integration_execution_executor_binding_authorization_review_only:
                        executor_binding_authorization_review = (
                            self._integration_execution_executor_binding_authorization_review_pipeline()
                        )
                        evaluated = executor_binding_authorization_review.prepare(run)
                        existing = self.store.load_artifact(
                            "production-integration-execution-executor-binding-authorization-review"
                        )
                        executor_binding_authorization_review.validate_existing(existing, run, evaluated)
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-executor-binding-authorization-review",
                            "complete:integration-execution-executor-binding-authorization-review",
                            lambda: executor_binding_authorization_review.build_executor_binding_authorization_review(
                                run, evaluated
                            ),
                        )
                        executor_binding_authorization_review.finalize(artifact)
                    if self.integration_execution_executor_binding_authorization_decision_only:
                        executor_binding_authorization_decision = (
                            self._integration_execution_executor_binding_authorization_decision_pipeline()
                        )
                        evaluated = executor_binding_authorization_decision.prepare(run)
                        existing = self.store.load_artifact(
                            "production-integration-execution-executor-binding-authorization-decision"
                        )
                        executor_binding_authorization_decision.validate_existing(existing, run, evaluated)
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-executor-binding-authorization-decision",
                            "complete:integration-execution-executor-binding-authorization-decision",
                            lambda: executor_binding_authorization_decision.build_executor_binding_authorization_decision(
                                run, evaluated
                            ),
                        )
                        executor_binding_authorization_decision.finalize(artifact)
                    if self.integration_execution_executor_binding_authorization_package_only:
                        executor_binding_authorization_package = (
                            self._integration_execution_executor_binding_authorization_package_pipeline()
                        )
                        evaluated = executor_binding_authorization_package.prepare(run)
                        existing = self.store.load_artifact(
                            "production-integration-execution-executor-binding-authorization-package"
                        )
                        executor_binding_authorization_package.validate_existing(existing, run, evaluated)
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-executor-binding-authorization-package",
                            "complete:integration-execution-executor-binding-authorization-package",
                            lambda: executor_binding_authorization_package.build_executor_binding_authorization_package(
                                run, evaluated
                            ),
                        )
                        executor_binding_authorization_package.finalize(artifact)
                    if self.integration_execution_executor_binding_authorization_package_readiness_only:
                        executor_binding_authorization_package_readiness = (
                            self._integration_execution_executor_binding_authorization_package_readiness_pipeline()
                        )
                        evaluated = executor_binding_authorization_package_readiness.prepare(run)
                        existing = self.store.load_artifact(
                            "production-integration-execution-executor-binding-authorization-package-readiness"
                        )
                        executor_binding_authorization_package_readiness.validate_existing(
                            existing, run, evaluated
                        )
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-executor-binding-authorization-package-readiness",
                            "complete:integration-execution-executor-binding-authorization-package-readiness",
                            lambda: executor_binding_authorization_package_readiness.build_executor_binding_authorization_package_readiness(
                                run, evaluated
                            ),
                        )
                        executor_binding_authorization_package_readiness.finalize(artifact)
                    if self.integration_execution_executor_binding_authorization_package_readiness_preflight_only:
                        executor_binding_authorization_package_readiness_preflight = (
                            self._integration_execution_executor_binding_authorization_package_readiness_preflight_pipeline()
                        )
                        evaluated = executor_binding_authorization_package_readiness_preflight.prepare(run)
                        existing = self.store.load_artifact(
                            "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
                        )
                        executor_binding_authorization_package_readiness_preflight.validate_existing(
                            existing, run, evaluated
                        )
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-executor-binding-authorization-package-readiness-preflight",
                            "complete:integration-execution-executor-binding-authorization-package-readiness-preflight",
                            lambda: executor_binding_authorization_package_readiness_preflight.build_executor_binding_authorization_package_readiness_preflight(
                                run, evaluated
                            ),
                        )
                        executor_binding_authorization_package_readiness_preflight.finalize(artifact)
                    if self.integration_execution_executor_binding_authorization_package_readiness_rehearsal_only:
                        executor_binding_authorization_package_readiness_rehearsal = (
                            self._integration_execution_executor_binding_authorization_package_readiness_rehearsal_pipeline()
                        )
                        evaluated = executor_binding_authorization_package_readiness_rehearsal.prepare(run)
                        existing = self.store.load_artifact(
                            "production-integration-execution-executor-binding-authorization-package-readiness-rehearsal"
                        )
                        executor_binding_authorization_package_readiness_rehearsal.validate_existing(
                            existing, run, evaluated
                        )
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-executor-binding-authorization-package-readiness-rehearsal",
                            "complete:integration-execution-executor-binding-authorization-package-readiness-rehearsal",
                            lambda: executor_binding_authorization_package_readiness_rehearsal.build_executor_binding_authorization_package_readiness_rehearsal(
                                run, evaluated
                            ),
                        )
                        executor_binding_authorization_package_readiness_rehearsal.finalize(artifact)
                    if self.integration_execution_executor_binding_authorization_package_readiness_authorization_review_only:
                        executor_binding_authorization_package_readiness_authorization_review = (
                            self._integration_execution_executor_binding_authorization_package_readiness_authorization_review_pipeline()
                        )
                        evaluated = executor_binding_authorization_package_readiness_authorization_review.prepare(run)
                        existing = self.store.load_artifact(
                            "production-integration-execution-executor-binding-authorization-package-readiness-authorization-review"
                        )
                        executor_binding_authorization_package_readiness_authorization_review.validate_existing(
                            existing, run, evaluated
                        )
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-executor-binding-authorization-package-readiness-authorization-review",
                            "complete:integration-execution-executor-binding-authorization-package-readiness-authorization-review",
                            lambda: executor_binding_authorization_package_readiness_authorization_review.build_executor_binding_authorization_package_readiness_authorization_review(
                                run, evaluated
                            ),
                        )
                        executor_binding_authorization_package_readiness_authorization_review.finalize(artifact)
                    if self.integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only:
                        executor_binding_authorization_package_readiness_authorization_decision = (
                            self._integration_execution_executor_binding_authorization_package_readiness_authorization_decision_pipeline()
                        )
                        evaluated = executor_binding_authorization_package_readiness_authorization_decision.prepare(run)
                        existing = self.store.load_artifact(
                            "production-integration-execution-executor-binding-authorization-package-readiness-authorization-decision"
                        )
                        executor_binding_authorization_package_readiness_authorization_decision.validate_existing(
                            existing, run, evaluated
                        )
                        artifact = self._ensure_artifact(
                            run,
                            "production-integration-execution-executor-binding-authorization-package-readiness-authorization-decision",
                            "complete:integration-execution-executor-binding-authorization-package-readiness-authorization-decision",
                            lambda: executor_binding_authorization_package_readiness_authorization_decision.build_executor_binding_authorization_package_readiness_authorization_decision(
                                run, evaluated
                            ),
                        )
                        executor_binding_authorization_package_readiness_authorization_decision.finalize(artifact)
                finally:
                    self.store.release_lease(self.owner)
            return run
        if self.integration_admission_only:
            raise ContractError(
                "integration_admission_only requires an existing locked Iteration 12 plan "
                "and a run at Complete / complete_locked"
            )
        if self.integration_execution_preflight_only:
            raise ContractError(
                "integration_execution_preflight_only requires an existing locked Iteration 13 admission "
                "and a run at Complete / complete_locked"
            )
        if self.integration_execution_rehearsal_only:
            raise ContractError(
                "integration_execution_rehearsal_only requires an existing locked Iteration 14 execution preflight "
                "and a run at Complete / complete_locked"
            )
        if self.integration_execution_authorization_review_only:
            raise ContractError(
                "integration_execution_authorization_review_only requires an existing "
                "locked Iteration 15 execution rehearsal and a run at "
                "Complete / complete_locked"
            )
        if self.integration_execution_authorization_decision_only:
            raise ContractError(
                "integration_execution_authorization_decision_only requires an existing "
                "locked Iteration 16 authorization review and a run at "
                "Complete / complete_locked"
            )
        if self.integration_execution_authorization_package_only:
            raise ContractError(
                "integration_execution_authorization_package_only requires an existing "
                "locked Iteration 17 authorization decision and a run at "
                "Complete / complete_locked"
            )
        if self.integration_execution_authority_readiness_only:
            raise ContractError(
                "integration_execution_authority_readiness_only requires an existing "
                "locked Iteration 18 authorization package and a run at "
                "Complete / complete_locked"
            )
        if self.integration_execution_executor_binding_readiness_only:
            raise ContractError(
                "integration_execution_executor_binding_readiness_only requires an existing "
                "locked Iteration 19 execution-authority-readiness artifact and a run at "
                "Complete / complete_locked"
            )
        if self.integration_execution_executor_binding_preflight_only:
            raise ContractError(
                "integration_execution_executor_binding_preflight_only requires an existing "
                "locked Iteration 20 executor-binding-readiness artifact and a run at "
                "Complete / complete_locked"
            )
        if self.integration_execution_executor_binding_rehearsal_only:
            raise ContractError(
                "integration_execution_executor_binding_rehearsal_only requires an existing "
                "locked Iteration 21 executor-binding-preflight artifact and a run at "
                "Complete / complete_locked"
            )
        if self.integration_execution_executor_binding_authorization_review_only:
            raise ContractError(
                "integration_execution_executor_binding_authorization_review_only requires "
                "locked Iteration 22 executor-binding-rehearsal and Complete / complete_locked"
            )
        if self.integration_execution_executor_binding_authorization_decision_only:
            raise ContractError(
                "integration_execution_executor_binding_authorization_decision_only requires "
                "locked Iteration 23 executor-binding-authorization-review and Complete / complete_locked"
            )
        if self.integration_execution_executor_binding_authorization_package_only:
            raise ContractError(
                "integration_execution_executor_binding_authorization_package_only requires "
                "locked Iteration 24 executor-binding-authorization-decision and Complete / complete_locked"
            )
        if self.integration_execution_executor_binding_authorization_package_readiness_only:
            raise ContractError(
                "integration_execution_executor_binding_authorization_package_readiness_only requires "
                "locked Iteration 25 executor-binding-authorization-package and Complete / complete_locked"
            )
        if self.integration_execution_executor_binding_authorization_package_readiness_preflight_only:
            raise ContractError(
                "integration_execution_executor_binding_authorization_package_readiness_preflight_only requires "
                "locked Iteration 26 executor-binding-authorization-package-readiness and Complete / complete_locked"
            )
        if self.integration_execution_executor_binding_authorization_package_readiness_rehearsal_only:
            raise ContractError(
                "integration_execution_executor_binding_authorization_package_readiness_rehearsal_only requires "
                "locked Iteration 27 executor-binding-authorization-package-readiness-preflight and Complete / complete_locked"
            )
        if self.integration_execution_executor_binding_authorization_package_readiness_authorization_review_only:
            raise ContractError(
                "integration_execution_executor_binding_authorization_package_readiness_authorization_review_only requires "
                "locked Iteration 28 executor-binding-authorization-package-readiness-rehearsal and Complete / complete_locked"
            )
        if self.integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only:
            raise ContractError(
                "integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only requires "
                "locked Iteration 29 executor-binding-authorization-package-readiness-authorization-review and Complete / complete_locked"
            )

        if self.render_only and run["current_state"] not in {"Validating", "Recovering"}:
            raise ContractError(
                "render_only requires an existing locked Iteration 4 publication bundle "
                "and a run stopped at the Validating boundary"
            )
        if self.release_only and run["current_state"] not in {
            "Validating", "Releasing", "Deployed", "LiveVerified", "Recovering"
        }:
            raise ContractError(
                "release_only requires an existing locked Iteration 5 route manifest "
                "and a run stopped at or after the Validating boundary"
            )
        if self.evaluation_only and run["current_state"] not in {
            "LiveVerified", "PostPublicationEvaluation", "Recovering"
        }:
            raise ContractError(
                "evaluation_only requires an existing locked Iteration 6 LiveVerified release chain "
                "and a run stopped at or after the LiveVerified boundary"
            )
        if self.reconcile_only and run["current_state"] not in {
            "PostPublicationEvaluation", "OperationsReconciled", "Recovering"
        }:
            raise ContractError(
                "reconcile_only requires an existing locked Iteration 7 PostPublicationEvaluation chain"
            )
        if self.completion_only and run["current_state"] not in {
            "OperationsReconciled", "Recovering"
        }:
            raise ContractError(
                "completion_only requires an existing locked Iteration 8 OperationsReconciled chain"
            )
        self.store.acquire_lease(self.run_id, self.owner)
        try:
            self._recover_if_needed(run)
            while run["current_state"] != "Complete":
                if self.editorial_only and run["current_state"] == "Building":
                    run["completion_status"] = "editorial_locked"
                    self.store.write_run(run)
                    return run
                state = run["current_state"]
                try:
                    if state == "Ready":
                        self.transition(run, "Acquiring")
                    elif state == "Acquiring":
                        pipeline = self._editorial_pipeline()
                        self._ensure_artifact(run, "discovery", "acquiring", pipeline.discover)
                        self.transition(run, "Deciding")
                    elif state == "Deciding":
                        pipeline = self._editorial_pipeline()
                        self._ensure_artifact(run, "edition", "deciding", pipeline.build_edition)
                        self._ensure_artifact(run, "rating-contract", "deciding", self._rating_contract)
                        self.transition(run, "Building")
                    elif state == "Building":
                        build = self._build_pipeline()
                        self._ensure_artifact(run, "media", "building:media", build.build_media)
                        self._ensure_artifact(run, "watchlist", "building:watchlist", build.build_watchlist)
                        self._ensure_artifact(
                            run, "book-bridges", "building:book-bridges", build.build_book_bridges
                        )
                        if self.build_only:
                            run["completion_status"] = "build_locked"
                            self.store.write_run(run)
                            return run
                        pre_release = self._pre_release_pipeline()
                        self._ensure_artifact(run, "images", "building:images", pre_release.build_images)
                        self.transition(run, "Validating")
                    elif state == "Validating":
                        if self.render_only:
                            bundle = self.store.load_artifact("publication-bundle")
                            if not bundle or bundle.get("status") != "locked":
                                raise RenderBoundaryFailure(
                                    "render_validation",
                                    "publication-bundle",
                                    "render_only requires the existing locked Iteration 4 publication bundle",
                                )
                            renderer = self._render_pipeline()
                            renderer.validate_existing_render_set()
                            self._ensure_artifact(
                                run,
                                "reader-render",
                                "validating:reader-render",
                                renderer.build_reader_render,
                            )
                            self._ensure_artifact(
                                run,
                                "route-manifest",
                                "validating:route-manifest",
                                renderer.build_route_manifest,
                            )
                            run["completion_status"] = "render_locked"
                            self.store.write_run(run)
                            return run
                        if self.release_only:
                            release = self._release_pipeline()
                            release.validate_existing_release_set()
                            self.transition(run, "Releasing")
                            continue
                        self._maybe_inject("Validating")
                        pre_release = self._pre_release_pipeline()
                        self._ensure_artifact(
                            run,
                            "publication-bundle",
                            "validating",
                            pre_release.build_validation_bundle,
                        )
                        if self.validation_only:
                            run["completion_status"] = "validation_locked"
                            self.store.write_run(run)
                            return run
                        self.transition(run, "Releasing")
                    elif state == "Releasing":
                        if self.release_only:
                            release = self._release_pipeline()
                            release.validate_existing_release_set()
                            package = self._ensure_artifact(
                                run,
                                "release-package",
                                "releasing:release-package",
                                release.build_release_package,
                            )
                            deployment = self._ensure_artifact(
                                run,
                                "shadow-deployment",
                                "releasing:shadow-deployment",
                                release.build_shadow_deployment,
                            )
                            run["stage_receipts"]["release"] = {
                                "release_package_digest": package["content_digest"],
                                "route_manifest_digest": self.store.load_artifact("route-manifest")["content_digest"],
                                "released_at": utc_now(),
                                "scope": "shadow_only",
                            }
                            run["stage_receipts"]["deployment_identity"] = deployment["data"]["deployment_identity"]
                            self.store.write_run(run)
                            self.transition(run, "Deployed")
                        else:
                            bundle = self.store.load_artifact("publication-bundle")
                            self._count_stage(run, "releasing")
                            run["stage_receipts"]["release"] = {
                                "bundle_digest": bundle["content_digest"],
                                "released_at": utc_now(),
                            }
                            run["stage_receipts"]["deployment_identity"] = (
                                f"synthetic-deploy:{bundle['content_digest']}"
                            )
                            self.store.write_run(run)
                            self.transition(run, "Deployed")
                    elif state == "Deployed":
                        if self.release_only:
                            release = self._release_pipeline()
                            verification = self._ensure_artifact(
                                run,
                                "live-verification",
                                "deployed:shadow-verification",
                                release.build_live_verification,
                            )
                            run["stage_receipts"]["live_verification"] = {
                                "release_package_digest": verification["data"]["release_package_digest"],
                                "deployment_identity": verification["data"]["deployment_identity"],
                                "verification_receipt_digest": verification["content_digest"],
                                "verification_scope": verification["data"]["verification_scope"],
                                "verified_at": utc_now(),
                                "result": verification["data"]["result"],
                            }
                            self.store.write_run(run)
                            self.transition(run, "LiveVerified")
                        else:
                            self._count_stage(run, "deployed")
                            run["stage_receipts"]["live_verification"] = {
                                "bundle_digest": self.store.load_artifact("publication-bundle")["content_digest"],
                                "verified_at": utc_now(),
                                "result": "passed",
                            }
                            self.store.write_run(run)
                            self.transition(run, "LiveVerified")
                    elif state == "LiveVerified":
                        if self.release_only:
                            self._release_pipeline().validate_existing_release_set()
                            run["completion_status"] = "shadow_live_verified"
                            self.store.write_run(run)
                            return run
                        self.transition(run, "PostPublicationEvaluation")
                    elif state == "PostPublicationEvaluation":
                        if self.reconcile_only:
                            evaluation_pipeline = self._evaluation_pipeline()
                            evaluation_pipeline.validate_existing_evaluation_set()
                            evaluation = self.store.load_artifact("book-change-evaluation")
                            if not evaluation or evaluation.get("status") != "locked":
                                raise EvaluationBoundaryFailure(
                                    "evaluation_validation",
                                    "book-change-evaluation",
                                    "reconcile_only requires the locked Iteration 7 evaluation artifact",
                                )
                            self.transition(run, "OperationsReconciled")
                            continue
                        if self.evaluation_only:
                            evaluation_pipeline = self._evaluation_pipeline()
                            evaluation_pipeline.validate_existing_evaluation_set()
                            evaluation = self._ensure_artifact(
                                run,
                                "book-change-evaluation",
                                "post_publication_evaluation",
                                evaluation_pipeline.build_evaluation,
                            )
                            run["stage_receipts"]["post_publication_evaluation"] = {
                                "evaluation_digest": evaluation["content_digest"],
                                "proposal_count": evaluation["data"]["proposal_count"],
                                "all_items_evaluated": evaluation["data"]["all_items_evaluated"],
                                "live_verification_digest": evaluation["data"]["bound_release"][
                                    "live_verification_digest"
                                ],
                                "evaluated_at": utc_now(),
                                "scope": "shadow_only",
                            }
                            run["completion_status"] = "post_publication_evaluation_locked"
                            self.store.write_run(run)
                            return run
                        self._ensure_artifact(
                            run,
                            "book-change-evaluation",
                            "post_publication_evaluation",
                            self._book_evaluation,
                        )
                        self.transition(run, "OperationsReconciled")
                    elif state == "OperationsReconciled":
                        if self.completion_only:
                            completion_pipeline = self._completion_pipeline()
                            completion_pipeline.validate_existing_completion_set(run)
                            completion = self._ensure_artifact(
                                run,
                                "completion",
                                "operations_reconciled:completion",
                                lambda: completion_pipeline.build_completion(run),
                            )
                            completion_receipt = completion_pipeline.finalize_completion(
                                run, completion
                            )
                            run["stage_receipts"]["final_completion"] = deepcopy(
                                completion_receipt
                            )
                            run["completion_status"] = "complete_locked"
                            self.store.write_run(run)
                            self.transition(run, "Complete")
                            continue
                        if self.reconcile_only:
                            operations = self._operations_pipeline()
                            operations.validate_existing_projection_set()
                            projection = self._ensure_artifact(
                                run,
                                "command-center-projection",
                                "operations_reconciled:projection-payload",
                                operations.build_projection,
                            )
                            receipt = operations.materialize_shadow_projection(projection)
                            watermark = self._ensure_artifact(
                                run,
                                "projection-watermark",
                                "operations_reconciled:watermark",
                                lambda: operations.build_watermark(projection, receipt),
                            )
                            operations.validate_complete_reconciliation(projection, receipt, watermark)
                            run["stage_receipts"]["operations_reconciliation"] = {
                                "projection_digest": projection["content_digest"],
                                "shadow_projection_receipt_digest": watermark["data"][
                                    "shadow_projection_receipt_digest"
                                ],
                                "projection_watermark_digest": watermark["content_digest"],
                                "reconciliation_identity": watermark["data"]["reconciliation_identity"],
                                "scope": "shadow_only",
                            }
                            run["completion_status"] = "operations_reconciled_locked"
                            self.store.write_run(run)
                            return run
                        self._ensure_artifact(
                            run,
                            "projection-watermark",
                            "operations_reconciled:projection",
                            self._projection_watermark,
                        )
                        self._ensure_artifact(
                            run,
                            "completion",
                            "operations_reconciled:completion",
                            lambda: self._completion(run),
                        )
                        run["completion_status"] = "complete"
                        self.store.write_run(run)
                        self.transition(run, "Complete")
                    elif state == "Recovering":
                        self._recover_if_needed(run)
                    else:
                        raise ContractError(f"unhandled state: {state}")
                except (
                    SyntheticFailure,
                    EditorialCandidateFailure,
                    BuildBoundaryFailure,
                    ImageBoundaryFailure,
                    ValidationBoundaryFailure,
                    RenderBoundaryFailure,
                    ReleaseBoundaryFailure,
                    EvaluationBoundaryFailure,
                    OperationsBoundaryFailure,
                    CompletionBoundaryFailure,
                ) as exc:
                    self._record_failure(run, state, exc)
                    raise
            return run
        finally:
            self.store.release_lease(self.owner)


def projection_freshness(watermark: dict[str, Any] | None, final_production_identity: str) -> dict[str, str]:
    """Deterministically classify Command Center projection freshness."""
    if not watermark:
        return {"status": "degraded", "reason": "watermark_missing"}
    represented = watermark.get("data", watermark).get("final_production_identity")
    if represented != final_production_identity:
        return {"status": "degraded", "reason": "final_production_identity_mismatch"}
    return {"status": "current", "reason": "identity_match"}


def start_daily_brief(
    edition_date: str,
    mode: str = "synthetic",
    state_root: Path | str = ".state",
    owner: str = "orchestrator",
    failure_injection: FailureInjection | None = None,
    *,
    editorial_fixture_root: Path | str | None = None,
    editorial_only: bool = False,
    build_fixture_root: Path | str | None = None,
    build_only: bool = False,
    pre_release_fixture_root: Path | str | None = None,
    validation_only: bool = False,
    render_fixture_root: Path | str | None = None,
    render_only: bool = False,
    release_fixture_root: Path | str | None = None,
    release_only: bool = False,
    evaluation_fixture_root: Path | str | None = None,
    evaluation_only: bool = False,
    operations_fixture_root: Path | str | None = None,
    reconcile_only: bool = False,
    completion_fixture_root: Path | str | None = None,
    completion_only: bool = False,
    readiness_fixture_root: Path | str | None = None,
    readiness_only: bool = False,
    integration_preflight_fixture_root: Path | str | None = None,
    integration_preflight_only: bool = False,
    integration_plan_fixture_root: Path | str | None = None,
    integration_plan_only: bool = False,
    integration_admission_fixture_root: Path | str | None = None,
    integration_admission_only: bool = False,
    integration_execution_preflight_fixture_root: Path | str | None = None,
    integration_execution_preflight_only: bool = False,
    integration_execution_rehearsal_fixture_root: Path | str | None = None,
    integration_execution_rehearsal_only: bool = False,
    integration_execution_authorization_review_fixture_root: Path | str | None = None,
    integration_execution_authorization_review_only: bool = False,
    integration_execution_authorization_decision_fixture_root: Path | str | None = None,
    integration_execution_authorization_decision_only: bool = False,
    integration_execution_authorization_package_fixture_root: Path | str | None = None,
    integration_execution_authorization_package_only: bool = False,
    integration_execution_authority_readiness_fixture_root: Path | str | None = None,
    integration_execution_authority_readiness_only: bool = False,
    integration_execution_executor_binding_readiness_fixture_root: Path | str | None = None,
    integration_execution_executor_binding_readiness_only: bool = False,
    integration_execution_executor_binding_preflight_fixture_root: Path | str | None = None,
    integration_execution_executor_binding_preflight_only: bool = False,
    integration_execution_executor_binding_rehearsal_fixture_root: Path | str | None = None,
    integration_execution_executor_binding_rehearsal_only: bool = False,
    integration_execution_executor_binding_authorization_review_fixture_root: Path | str | None = None,
    integration_execution_executor_binding_authorization_review_only: bool = False,
    integration_execution_executor_binding_authorization_decision_fixture_root: Path | str | None = None,
    integration_execution_executor_binding_authorization_decision_only: bool = False,
    integration_execution_executor_binding_authorization_package_fixture_root: Path | str | None = None,
    integration_execution_executor_binding_authorization_package_only: bool = False,
    integration_execution_executor_binding_authorization_package_readiness_fixture_root: Path | str | None = None,
    integration_execution_executor_binding_authorization_package_readiness_only: bool = False,
    integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root: Path | str | None = None,
    integration_execution_executor_binding_authorization_package_readiness_preflight_only: bool = False,
    integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root: Path | str | None = None,
    integration_execution_executor_binding_authorization_package_readiness_rehearsal_only: bool = False,
    integration_execution_executor_binding_authorization_package_readiness_authorization_review_fixture_root: Path | str | None = None,
    integration_execution_executor_binding_authorization_package_readiness_authorization_review_only: bool = False,
    integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root: Path | str | None = None,
    integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only: bool = False,
) -> dict[str, Any]:
    """Canonical manual/future-schedule entry point."""
    return RunEngine(
        state_root=state_root,
        edition_date=edition_date,
        mode=mode,
        owner=owner,
        failure_injection=failure_injection,
        editorial_fixture_root=editorial_fixture_root,
        editorial_only=editorial_only,
        build_fixture_root=build_fixture_root,
        build_only=build_only,
        pre_release_fixture_root=pre_release_fixture_root,
        validation_only=validation_only,
        render_fixture_root=render_fixture_root,
        render_only=render_only,
        release_fixture_root=release_fixture_root,
        release_only=release_only,
        evaluation_fixture_root=evaluation_fixture_root,
        evaluation_only=evaluation_only,
        operations_fixture_root=operations_fixture_root,
        reconcile_only=reconcile_only,
        completion_fixture_root=completion_fixture_root,
        completion_only=completion_only,
        readiness_fixture_root=readiness_fixture_root,
        readiness_only=readiness_only,
        integration_preflight_fixture_root=integration_preflight_fixture_root,
        integration_preflight_only=integration_preflight_only,
        integration_plan_fixture_root=integration_plan_fixture_root,
        integration_plan_only=integration_plan_only,
        integration_admission_fixture_root=integration_admission_fixture_root,
        integration_admission_only=integration_admission_only,
        integration_execution_preflight_fixture_root=integration_execution_preflight_fixture_root,
        integration_execution_preflight_only=integration_execution_preflight_only,
        integration_execution_rehearsal_fixture_root=integration_execution_rehearsal_fixture_root,
        integration_execution_rehearsal_only=integration_execution_rehearsal_only,
        integration_execution_authorization_review_fixture_root=(
            integration_execution_authorization_review_fixture_root
        ),
        integration_execution_authorization_review_only=(
            integration_execution_authorization_review_only
        ),
        integration_execution_authorization_decision_fixture_root=(
            integration_execution_authorization_decision_fixture_root
        ),
        integration_execution_authorization_decision_only=(
            integration_execution_authorization_decision_only
        ),
        integration_execution_authorization_package_fixture_root=(
            integration_execution_authorization_package_fixture_root
        ),
        integration_execution_authorization_package_only=(
            integration_execution_authorization_package_only
        ),
        integration_execution_authority_readiness_fixture_root=(
            integration_execution_authority_readiness_fixture_root
        ),
        integration_execution_authority_readiness_only=(
            integration_execution_authority_readiness_only
        ),
        integration_execution_executor_binding_readiness_fixture_root=(
            integration_execution_executor_binding_readiness_fixture_root
        ),
        integration_execution_executor_binding_readiness_only=(
            integration_execution_executor_binding_readiness_only
        ),
        integration_execution_executor_binding_preflight_fixture_root=(
            integration_execution_executor_binding_preflight_fixture_root
        ),
        integration_execution_executor_binding_preflight_only=(
            integration_execution_executor_binding_preflight_only
        ),
        integration_execution_executor_binding_rehearsal_fixture_root=(
            integration_execution_executor_binding_rehearsal_fixture_root
        ),
        integration_execution_executor_binding_rehearsal_only=(
            integration_execution_executor_binding_rehearsal_only
        ),
        integration_execution_executor_binding_authorization_review_fixture_root=(
            integration_execution_executor_binding_authorization_review_fixture_root
        ),
        integration_execution_executor_binding_authorization_review_only=(
            integration_execution_executor_binding_authorization_review_only
        ),
        integration_execution_executor_binding_authorization_decision_fixture_root=(
            integration_execution_executor_binding_authorization_decision_fixture_root
        ),
        integration_execution_executor_binding_authorization_decision_only=(
            integration_execution_executor_binding_authorization_decision_only
        ),
        integration_execution_executor_binding_authorization_package_fixture_root=(
            integration_execution_executor_binding_authorization_package_fixture_root
        ),
        integration_execution_executor_binding_authorization_package_only=(
            integration_execution_executor_binding_authorization_package_only
        ),
        integration_execution_executor_binding_authorization_package_readiness_fixture_root=(
            integration_execution_executor_binding_authorization_package_readiness_fixture_root
        ),
        integration_execution_executor_binding_authorization_package_readiness_only=(
            integration_execution_executor_binding_authorization_package_readiness_only
        ),
        integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root=(
            integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root
        ),
        integration_execution_executor_binding_authorization_package_readiness_preflight_only=(
            integration_execution_executor_binding_authorization_package_readiness_preflight_only
        ),
        integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root=(
            integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root
        ),
        integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=(
            integration_execution_executor_binding_authorization_package_readiness_rehearsal_only
        ),
        integration_execution_executor_binding_authorization_package_readiness_authorization_review_fixture_root=(
            integration_execution_executor_binding_authorization_package_readiness_authorization_review_fixture_root
        ),
        integration_execution_executor_binding_authorization_package_readiness_authorization_review_only=(
            integration_execution_executor_binding_authorization_package_readiness_authorization_review_only
        ),
        integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=(
            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root
        ),
        integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=(
            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only
        ),
    ).run()


def scheduled_start(
    edition_date: str,
    mode: str = "production",
    state_root: Path | str = ".state",
    owner: str = "scheduled-orchestrator",
) -> dict[str, Any]:
    """Future schedule adapter. Intentionally delegates to the exact same entry point."""
    return start_daily_brief(edition_date, mode, state_root, owner)
