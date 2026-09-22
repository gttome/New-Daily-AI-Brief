from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import RATING_CONTRACT_VERSION, SCHEMA_VERSION
from .store import CanonicalStore, ContractError, digest, semantic_digest, utc_now


class ShadowReleaseError(ContractError):
    pass


class ReleaseBoundaryFailure(ShadowReleaseError):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id
        self.candidate_id = f"release:{boundary_id}"


class ShadowReleasePipeline:
    RELEASE_PACKAGE_CONTRACT_VERSION = "1.0.0"
    DEPLOYMENT_ADAPTER_VERSION = "shadow-filesystem-v1"
    VERIFICATION_CONTRACT_VERSION = "1.0.0"
    VERIFICATION_SCOPE = "shadow_offline"

    def __init__(
        self,
        store: CanonicalStore,
        edition_date: str,
        mode: str,
        fixture_root: Path | str | None,
        *,
        failure_boundary_id: str | None = None,
        failure_class: str = "synthetic_release_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = Path(fixture_root) if fixture_root is not None else None
        self.failure_boundary_id = (failure_boundary_id or "").removeprefix("release:")
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = self.store.run_dir / "shadow-deployment-state.json"
        self.metrics_path = self.store.run_dir / "iteration6-metrics.json"
        self.output_dir = self.store.run_dir / "shadow-deployment-outputs"

    def _fail(self, boundary_type: str, boundary_id: str, message: str) -> None:
        raise ReleaseBoundaryFailure(boundary_type, boundary_id, message)

    def _contract(self) -> dict[str, Any]:
        if self.mode == "production" or self.fixture_root is None:
            raise ShadowReleaseError(
                "production deployment is intentionally fail-closed: no approved "
                "zero-incremental-cost production deployment adapter is configured"
            )
        path = self.fixture_root / "release-contract.json"
        if not path.exists():
            raise ShadowReleaseError(f"missing Iteration 6 release contract fixture: {path}")
        contract = json.loads(path.read_text(encoding="utf-8"))
        checks = {
            "schema_version": contract.get("schema_version") == SCHEMA_VERSION,
            "release_contract": contract.get("release_package_contract_version")
            == self.RELEASE_PACKAGE_CONTRACT_VERSION,
            "deployment_adapter": contract.get("deployment_adapter_version")
            == self.DEPLOYMENT_ADAPTER_VERSION,
            "verification_contract": contract.get("live_verification_contract_version")
            == self.VERIFICATION_CONTRACT_VERSION,
            "verification_scope": contract.get("verification_scope") == self.VERIFICATION_SCOPE,
            "required_output_count": contract.get("required_output_count") == 11,
            "shadow_only": contract.get("shadow_only") is True,
            "production_authorized": contract.get("production_authorized") is False,
        }
        if not all(checks.values()):
            raise ShadowReleaseError("unsupported or unsafe Iteration 6 release contract")
        return contract

    def _write_metrics(self, section: str, values: dict[str, Any]) -> None:
        current = self.store.read_json(self.metrics_path) or {
            "schema_version": SCHEMA_VERSION,
            "edition_date": self.edition_date,
        }
        current[section] = deepcopy(values)
        current[section]["recorded_at"] = utc_now()
        self.store._atomic_write(self.metrics_path, current)

    def _read_metrics(self, section: str, defaults: dict[str, Any]) -> dict[str, Any]:
        current = self.store.read_json(self.metrics_path) or {}
        values = deepcopy(defaults)
        values.update(deepcopy(current.get(section, {})))
        values.pop("recorded_at", None)
        return values

    def _require_locked(self, artifact_type: str) -> dict[str, Any]:
        record = self.store.load_artifact(artifact_type)
        if not record:
            self._fail("release_validation", artifact_type, f"locked {artifact_type} is missing")
        if record.get("status") != "locked":
            self._fail("release_validation", artifact_type, f"{artifact_type} is not locked")
        if record.get("schema_version") != SCHEMA_VERSION:
            self._fail("release_validation", artifact_type, f"{artifact_type} schema is incompatible")
        if record.get("edition_date") != self.edition_date:
            self._fail("release_validation", artifact_type, f"{artifact_type} is stale or wrong-date")
        if record.get("content_digest") != semantic_digest(record):
            self._fail("release_validation", artifact_type, f"{artifact_type} semantic digest mismatch")
        return record

    def _require_inputs(
        self,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]]:
        contract = self._contract()
        manifest = self._require_locked("route-manifest")
        reader = self._require_locked("reader-render")
        bundle = self._require_locked("publication-bundle")

        if manifest.get("input_digests") != [reader["content_digest"]]:
            self._fail("release_validation", "route-manifest", "route manifest reader input binding mismatch")
        if reader.get("input_digests") != [bundle["content_digest"]]:
            self._fail("release_validation", "reader-render", "reader-render bundle input binding mismatch")

        manifest_data = manifest.get("data", {})
        reader_data = reader.get("data", {})
        if manifest_data.get("reader_render_digest") != reader["content_digest"]:
            self._fail("release_validation", "route-manifest", "route manifest reader digest mismatch")
        if manifest_data.get("publication_bundle_digest") != bundle["content_digest"]:
            self._fail("release_validation", "route-manifest", "route manifest publication binding mismatch")
        if reader_data.get("publication_bundle_digest") != bundle["content_digest"]:
            self._fail("release_validation", "reader-render", "reader-render publication binding mismatch")
        if manifest_data.get("validation_result") != "passed":
            self._fail("release_validation", "route-manifest", "route manifest is not passing")
        if manifest_data.get("accessibility_structural_result") != "passed":
            self._fail("release_validation", "route-manifest", "route manifest accessibility result is not passing")
        if manifest_data.get("release_authorized") is not False or reader_data.get("release_authorized") is not False:
            self._fail("release_validation", "release-authorization", "upstream release authorization must remain false")

        reader_routes = reader_data.get("routes", [])
        manifest_routes = manifest_data.get("routes", [])
        expected_manifest_routes = [
            {
                "route_id": item.get("route_id"),
                "route": item.get("route"),
                "kind": item.get("kind"),
                "content_type": item.get("content_type"),
                "output_digest": item.get("output_digest"),
                "structural_checks": deepcopy(item.get("structural_checks")),
            }
            for item in reader_routes
        ]
        if manifest_routes != expected_manifest_routes:
            self._fail("release_validation", "route-manifest", "manifest routes differ from locked reader outputs")
        if len(reader_routes) != 11 or len(manifest_routes) != 11:
            self._fail("release_validation", "route-count", "exactly eleven locked outputs are required")
        if len({item.get("route") for item in manifest_routes}) != 11:
            self._fail("release_validation", "route-uniqueness", "route manifest contains duplicate routes")

        story_order = reader_data.get("story_order", [])
        expected_route_ids = [
            "current",
            "latest",
            "dated",
            *[f"story:{story_id}" for story_id in story_order],
            "archive",
            "feed",
        ]
        if len(story_order) != 6 or [item.get("route_id") for item in manifest_routes] != expected_route_ids:
            self._fail("release_validation", "route-order", "locked route order is incomplete or reordered")

        for item in reader_routes:
            expected_digest = digest(
                {
                    "route": item.get("route"),
                    "content_type": item.get("content_type"),
                    "content": item.get("content"),
                    "semantic": item.get("semantic"),
                }
            )
            if expected_digest != item.get("output_digest"):
                self._fail("release_validation", item.get("route_id", "unknown-route"), "reader output digest mismatch")
            checks = item.get("structural_checks", {})
            if not checks or not all(checks.values()):
                self._fail("release_validation", item.get("route_id", "unknown-route"), "structural/accessibility checks are not passing")

        records = {
            name: self._require_locked(name)
            for name in (
                "edition",
                "media",
                "watchlist",
                "book-bridges",
                "images",
                "rating-contract",
            )
        }
        ordered_inputs = bundle.get("data", {}).get("ordered_input_digests", {})
        for name, record in records.items():
            if ordered_inputs.get(name) != record["content_digest"]:
                self._fail("release_validation", name, f"{name} no longer matches the locked publication bundle")

        edition_stories = sorted(
            records["edition"]["data"].get("stories", []),
            key=lambda item: int(item.get("presentation_position", 0)),
        )
        locked_story_ids = [item.get("story_id") for item in edition_stories]
        media = records["media"]["data"]
        watchlist = records["watchlist"]["data"]
        bridges = records["book-bridges"]["data"].get("decisions", [])
        images = records["images"]["data"].get("images", [])
        rating = records["rating-contract"]["data"]

        semantic_checks = {
            "story_order": story_order == locked_story_ids and len(locked_story_ids) == 6,
            "media_videos": reader_data.get("media", {}).get("video_ids")
            == [item.get("media_id") for item in media.get("videos", [])]
            and len(media.get("videos", [])) == 2
            and all(item.get("verified") for item in media.get("videos", [])),
            "media_podcasts": reader_data.get("media", {}).get("podcast_ids")
            == [item.get("media_id") for item in media.get("podcasts", [])]
            and len(media.get("podcasts", [])) == 2
            and all(item.get("verified") for item in media.get("podcasts", [])),
            "watchlist": reader_data.get("watchlist_counts") == watchlist.get("counts"),
            "bridges": reader_data.get("bridge_decisions") == bridges
            and [item.get("story_id") for item in bridges] == locked_story_ids,
            "images": reader_data.get("image_bindings")
            == [
                {
                    "story_id": item.get("story_id"),
                    "image_id": item.get("image_id"),
                    "binary_digest": item.get("binary_digest"),
                }
                for item in images
            ]
            and [item.get("story_id") for item in images] == locked_story_ids
            and all(item.get("accepted") is True for item in images),
            "rating": reader_data.get("rating_contract", {}).get("contract_version")
            == rating.get("contract_version")
            == RATING_CONTRACT_VERSION
            and reader_data.get("rating_contract", {}).get("stored_rating_values") is None
            and reader_data.get("rating_contract", {}).get("fabricated_rating_values") is False,
            "archive": reader_data.get("archive_membership") == [self.edition_date]
            == manifest_data.get("archive_membership"),
            "feed": reader_data.get("feed_membership") == [self.edition_date]
            == manifest_data.get("feed_membership"),
        }
        failed = [name for name, passed in semantic_checks.items() if not passed]
        if failed:
            self._fail("release_validation", "semantic-parity", "semantic parity failures: " + ",".join(sorted(failed)))

        return contract, manifest, reader, records

    def validate_release_inputs(self) -> None:
        self._require_inputs()

    def _release_payload(
        self,
        contract: dict[str, Any],
        manifest: dict[str, Any],
        reader: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "release_package_contract_version": self.RELEASE_PACKAGE_CONTRACT_VERSION,
            "edition_date": self.edition_date,
            "route_manifest_digest": manifest["content_digest"],
            "reader_render_digest": reader["content_digest"],
            "routes": [
                {
                    "route_id": item["route_id"],
                    "route": item["route"],
                    "kind": item["kind"],
                    "content_type": item["content_type"],
                    "output_digest": item["output_digest"],
                }
                for item in manifest["data"]["routes"]
            ],
            "archive_membership": deepcopy(manifest["data"]["archive_membership"]),
            "feed_membership": deepcopy(manifest["data"]["feed_membership"]),
            "required_output_count": contract["required_output_count"],
            "production_authorized": False,
            "shadow_only": True,
        }

    def build_release_package(self) -> dict[str, Any]:
        started = time.monotonic()
        metrics = self._read_metrics(
            "release_package",
            {"attempts": 0, "reuses": 0, "failures": 0, "elapsed_ms": 0},
        )
        metrics["attempts"] += 1
        contract, manifest, reader, _ = self._require_inputs()
        if self.failure_boundary_id == "package" and not self._failure_fired:
            self._failure_fired = True
            metrics["failures"] += 1
            metrics["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
            self._write_metrics("release_package", metrics)
            raise ReleaseBoundaryFailure("release_package", "package", self.failure_class)
        metrics["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._write_metrics("release_package", metrics)
        return self._release_payload(contract, manifest, reader)

    def _load_deployment_state(self, package_digest: str) -> dict[str, Any]:
        state = self.store.read_json(self.state_path)
        if state:
            if state.get("schema_version") != SCHEMA_VERSION:
                self._fail("shadow_deployment", "state", "shadow deployment state schema is incompatible")
            if state.get("edition_date") != self.edition_date:
                self._fail("shadow_deployment", "state", "shadow deployment state is stale")
            if state.get("release_package_digest") != package_digest:
                self._fail("shadow_deployment", "state", "shadow deployment state binds a different release package")
            return state
        return {
            "schema_version": SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "release_package_digest": package_digest,
            "attempts": {},
            "outputs": {},
            "metrics": {
                "output_attempts": 0,
                "output_retries": 0,
                "output_completions": 0,
                "output_cache_reuse": 0,
                "injected_failures": 0,
                "unrelated_output_rewrites": 0,
            },
        }

    def _safe_name(self, route_id: str) -> str:
        return route_id.replace(":", "__") + ".json"

    def _materialized_record(
        self,
        contract: dict[str, Any],
        package_digest: str,
        source: dict[str, Any],
    ) -> dict[str, Any]:
        body = {
            "schema_version": SCHEMA_VERSION,
            "deployment_adapter_version": self.DEPLOYMENT_ADAPTER_VERSION,
            "edition_date": self.edition_date,
            "release_package_digest": package_digest,
            "route_id": source["route_id"],
            "route": source["route"],
            "content_type": source["content_type"],
            "content": source["content"],
            "source_output_digest": source["output_digest"],
            "structural_checks": deepcopy(source["structural_checks"]),
            "shadow_only": contract["shadow_only"],
            "production_authorized": contract["production_authorized"],
        }
        body["materialization_digest"] = digest(body)
        return body

    def _validated_package(
        self,
        contract: dict[str, Any],
        manifest: dict[str, Any],
        reader: dict[str, Any],
    ) -> dict[str, Any]:
        package = self._require_locked("release-package")
        if package.get("input_digests") != [manifest["content_digest"]]:
            self._fail("release_validation", "release-package", "release package route-manifest input mismatch")
        if package.get("data") != self._release_payload(contract, manifest, reader):
            self._fail("release_validation", "release-package", "release package payload is stale or corrupted")
        return package

    def build_shadow_deployment(self) -> dict[str, Any]:
        started = time.monotonic()
        contract, manifest, reader, _ = self._require_inputs()
        package = self._validated_package(contract, manifest, reader)
        package_digest = package["content_digest"]
        state = self._load_deployment_state(package_digest)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        source_by_id = {item["route_id"]: item for item in reader["data"]["routes"]}
        package_routes = package["data"]["routes"]
        expected_files = {self._safe_name(item["route_id"]) for item in package_routes}
        existing_files = {path.name for path in self.output_dir.glob("*.json")}
        extras = existing_files - expected_files
        if extras:
            self._fail("shadow_deployment", "extra-output", "unexpected shadow outputs exist: " + ",".join(sorted(extras)))

        for package_route in package_routes:
            route_id = package_route["route_id"]
            source = source_by_id.get(route_id)
            if not source or source.get("output_digest") != package_route.get("output_digest"):
                self._fail("shadow_deployment", route_id, "release package output is missing from reader-render")
            expected = self._materialized_record(contract, package_digest, source)
            path = self.output_dir / self._safe_name(route_id)
            cached = state["outputs"].get(route_id)
            if cached:
                if not path.exists():
                    self._fail("shadow_deployment", route_id, "cached shadow output file is missing")
                disk = self.store.read_json(path)
                expected_summary = {
                    "route_id": route_id,
                    "route": source["route"],
                    "source_output_digest": source["output_digest"],
                    "materialization_digest": expected["materialization_digest"],
                    "file": path.name,
                    "release_package_digest": package_digest,
                }
                if disk != expected or cached != expected_summary:
                    self._fail("shadow_deployment", route_id, "cached shadow output is corrupted")
                state["metrics"]["output_cache_reuse"] += 1
                self.store._atomic_write(self.state_path, state)
                continue
            if path.exists():
                self._fail("shadow_deployment", route_id, "orphan shadow output exists without durable state")

            attempt = int(state["attempts"].get(route_id, 0)) + 1
            state["attempts"][route_id] = attempt
            state["metrics"]["output_attempts"] += 1
            if attempt > 1:
                state["metrics"]["output_retries"] += 1
            self.store._atomic_write(self.state_path, state)

            if self.failure_boundary_id == f"output:{route_id}" and not self._failure_fired:
                self._failure_fired = True
                state["metrics"]["injected_failures"] += 1
                self.store._atomic_write(self.state_path, state)
                metrics = deepcopy(state["metrics"])
                metrics["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
                self._write_metrics("shadow_deployment", metrics)
                raise ReleaseBoundaryFailure("shadow_output", f"output:{route_id}", self.failure_class)

            self.store._atomic_write(path, expected)
            summary = {
                "route_id": route_id,
                "route": source["route"],
                "source_output_digest": source["output_digest"],
                "materialization_digest": expected["materialization_digest"],
                "file": path.name,
                "release_package_digest": package_digest,
            }
            state["outputs"][route_id] = summary
            state["metrics"]["output_completions"] += 1
            self.store._atomic_write(self.state_path, state)

        actual_files = {path.name for path in self.output_dir.glob("*.json")}
        if actual_files != expected_files or len(state["outputs"]) != 11:
            self._fail("shadow_deployment", "output-set", "shadow deployment output set is incomplete or contains extras")

        ordered_outputs = [deepcopy(state["outputs"][item["route_id"]]) for item in package_routes]
        deployment_identity = "shadow-deploy:" + digest(
            {
                "deployment_adapter_version": self.DEPLOYMENT_ADAPTER_VERSION,
                "release_package_digest": package_digest,
                "outputs": ordered_outputs,
            }
        ).removeprefix("sha256:")
        metrics = deepcopy(state["metrics"])
        metrics["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._write_metrics("shadow_deployment", metrics)
        return {
            "deployment_adapter_version": self.DEPLOYMENT_ADAPTER_VERSION,
            "edition_date": self.edition_date,
            "release_package_digest": package_digest,
            "deployment_identity": deployment_identity,
            "output_count": len(ordered_outputs),
            "outputs": ordered_outputs,
            "production_authorized": False,
            "shadow_only": True,
        }

    def _validated_deployment(
        self,
        contract: dict[str, Any],
        package: dict[str, Any],
        reader: dict[str, Any],
    ) -> dict[str, Any]:
        deployment = self._require_locked("shadow-deployment")
        if deployment.get("input_digests") != [package["content_digest"]]:
            self._fail("shadow_verification", "shadow-deployment", "deployment receipt package input mismatch")
        data = deployment.get("data", {})
        if data.get("release_package_digest") != package["content_digest"]:
            self._fail("shadow_verification", "shadow-deployment", "deployment receipt does not bind release package")
        if data.get("output_count") != 11 or len(data.get("outputs", [])) != 11:
            self._fail("shadow_verification", "shadow-deployment", "deployment receipt output count is invalid")
        if data.get("shadow_only") is not True or data.get("production_authorized") is not False:
            self._fail("shadow_verification", "shadow-deployment", "deployment receipt has unsafe scope")

        source_by_id = {item["route_id"]: item for item in reader["data"]["routes"]}
        expected_files = set()
        expected_outputs = []
        for package_route in package["data"]["routes"]:
            route_id = package_route["route_id"]
            source = source_by_id[route_id]
            expected = self._materialized_record(contract, package["content_digest"], source)
            file_name = self._safe_name(route_id)
            expected_files.add(file_name)
            path = self.output_dir / file_name
            if not path.exists() or self.store.read_json(path) != expected:
                self._fail("shadow_verification", route_id, "shadow output is missing or corrupted")
            expected_outputs.append(
                {
                    "route_id": route_id,
                    "route": source["route"],
                    "source_output_digest": source["output_digest"],
                    "materialization_digest": expected["materialization_digest"],
                    "file": file_name,
                    "release_package_digest": package["content_digest"],
                }
            )
        if {path.name for path in self.output_dir.glob("*.json")} != expected_files:
            self._fail("shadow_verification", "extra-output", "shadow deployment contains an unexpected output")

        identity = "shadow-deploy:" + digest(
            {
                "deployment_adapter_version": self.DEPLOYMENT_ADAPTER_VERSION,
                "release_package_digest": package["content_digest"],
                "outputs": expected_outputs,
            }
        ).removeprefix("sha256:")
        if data.get("outputs") != expected_outputs or data.get("deployment_identity") != identity:
            self._fail("shadow_verification", "shadow-deployment", "deployment identity or output receipt mismatch")
        return deployment

    def build_live_verification(self) -> dict[str, Any]:
        started = time.monotonic()
        metrics = self._read_metrics(
            "verification",
            {"attempts": 0, "checks": 0, "failures": 0, "injected_failures": 0, "elapsed_ms": 0},
        )
        metrics["attempts"] += 1
        contract, manifest, reader, records = self._require_inputs()
        package = self._validated_package(contract, manifest, reader)
        deployment = self._validated_deployment(contract, package, reader)

        reader_data = reader["data"]
        story_ids = reader_data["story_order"]
        routes = reader_data["routes"]
        edition_routes = [item for item in routes if item["route_id"] in {"current", "latest", "dated"}]
        story_routes = [item for item in routes if item["kind"] == "story"]
        media = records["media"]["data"]
        watchlist = records["watchlist"]["data"]
        bridges = records["book-bridges"]["data"]["decisions"]
        images = records["images"]["data"]["images"]
        rating = records["rating-contract"]["data"]

        checks = {
            "exact_output_count": len(routes) == len(package["data"]["routes"]) == 11,
            "route_output_parity": [
                (item["route_id"], item["route"], item["output_digest"]) for item in manifest["data"]["routes"]
            ]
            == [
                (item["route_id"], item["route"], item["output_digest"]) for item in package["data"]["routes"]
            ],
            "edition_story_order": all(item["semantic"]["story_ids"] == story_ids for item in edition_routes),
            "six_permanent_story_routes": len(story_routes) == 6
            and [item["semantic"]["story_id"] for item in story_routes] == story_ids
            and all(item["semantic"]["edition_story_order"] == story_ids for item in story_routes),
            "media": reader_data["media"]["video_ids"] == [item["media_id"] for item in media["videos"]]
            and reader_data["media"]["podcast_ids"] == [item["media_id"] for item in media["podcasts"]],
            "watchlist": reader_data["watchlist_counts"] == watchlist["counts"],
            "bridges": reader_data["bridge_decisions"] == bridges,
            "images": reader_data["image_bindings"]
            == [
                {
                    "story_id": item["story_id"],
                    "image_id": item["image_id"],
                    "binary_digest": item["binary_digest"],
                }
                for item in images
            ],
            "rating_contract": reader_data["rating_contract"]["contract_version"]
            == rating["contract_version"]
            == RATING_CONTRACT_VERSION
            and reader_data["rating_contract"]["stored_rating_values"] is None
            and reader_data["rating_contract"]["fabricated_rating_values"] is False,
            "archive_membership": package["data"]["archive_membership"] == [self.edition_date],
            "feed_membership": package["data"]["feed_membership"] == [self.edition_date],
            "structural_accessibility": all(
                bool(item["structural_checks"]) and all(item["structural_checks"].values())
                for item in manifest["data"]["routes"]
            ),
            "release_package_manifest_binding": package["data"]["route_manifest_digest"]
            == manifest["content_digest"],
            "deployment_release_binding": deployment["data"]["release_package_digest"]
            == package["content_digest"],
            "verification_scope": contract["verification_scope"] == self.VERIFICATION_SCOPE,
            "shadow_only": deployment["data"]["shadow_only"] is True,
            "production_not_authorized": deployment["data"]["production_authorized"] is False,
        }
        metrics["checks"] = len(checks)
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            metrics["failures"] += 1
            metrics["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
            self._write_metrics("verification", metrics)
            self._fail("shadow_verification", "verification", "offline verification failures: " + ",".join(sorted(failed)))

        if self.failure_boundary_id == "verification" and not self._failure_fired:
            self._failure_fired = True
            metrics["injected_failures"] += 1
            metrics["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
            self._write_metrics("verification", metrics)
            raise ReleaseBoundaryFailure("shadow_verification", "verification", self.failure_class)

        metrics["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._write_metrics("verification", metrics)
        return {
            "live_verification_contract_version": self.VERIFICATION_CONTRACT_VERSION,
            "verification_scope": self.VERIFICATION_SCOPE,
            "edition_date": self.edition_date,
            "route_manifest_digest": manifest["content_digest"],
            "release_package_digest": package["content_digest"],
            "deployment_identity": deployment["data"]["deployment_identity"],
            "checked_route_ids": [item["route_id"] for item in manifest["data"]["routes"]],
            "checks": checks,
            "result": "passed",
            "production_authorized": False,
            "shadow_only": True,
        }

    def validate_existing_release_set(self) -> None:
        contract, manifest, reader, _ = self._require_inputs()
        package = self.store.load_artifact("release-package")
        if not package:
            return
        package = self._validated_package(contract, manifest, reader)
        package_metrics = self._read_metrics(
            "release_package",
            {"attempts": 0, "reuses": 0, "failures": 0, "elapsed_ms": 0},
        )
        package_metrics["reuses"] += 1
        self._write_metrics("release_package", package_metrics)

        deployment = self.store.load_artifact("shadow-deployment")
        if not deployment:
            return
        deployment = self._validated_deployment(contract, package, reader)
        reuse = self._read_metrics(
            "receipt_reuse",
            {"deployment_receipt_reuse": 0, "verification_receipt_reuse": 0},
        )
        reuse["deployment_receipt_reuse"] += 1

        verification = self.store.load_artifact("live-verification")
        if verification:
            verification = self._require_locked("live-verification")
            if verification.get("input_digests") != [deployment["content_digest"]]:
                self._fail("shadow_verification", "live-verification", "verification receipt deployment input mismatch")
            data = verification.get("data", {})
            valid = (
                data.get("verification_scope") == self.VERIFICATION_SCOPE
                and data.get("route_manifest_digest") == manifest["content_digest"]
                and data.get("release_package_digest") == package["content_digest"]
                and data.get("deployment_identity") == deployment["data"]["deployment_identity"]
                and data.get("result") == "passed"
                and data.get("shadow_only") is True
                and data.get("production_authorized") is False
                and data.get("checks")
                and all(data["checks"].values())
            )
            if not valid:
                self._fail("shadow_verification", "live-verification", "verification receipt is stale or corrupted")
            reuse["verification_receipt_reuse"] += 1
        self._write_metrics("receipt_reuse", reuse)
