"""Reproducible, process-isolated trial runner for SMAA 1.2.1.

This module is a research harness, not a security boundary. Run untrusted agents
inside externally hardened containers/VMs with network disabled.
"""
from __future__ import annotations

import hashlib
import json
import multiprocessing as mp
import os
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

ARCHITECTURES = ("log_only", "fixed_self_report", "state_tracker", "active_smaa")


@dataclass(frozen=True)
class TrialSpec:
    trial_id: str
    seed: int
    architecture: str
    environment_id: str
    intervention_seed: int
    budget_seconds: float = 10.0
    budget_memory_mb: int = 256

    def __post_init__(self) -> None:
        if self.architecture not in ARCHITECTURES:
            raise ValueError(f"unknown architecture: {self.architecture}")
        if self.budget_seconds <= 0 or self.budget_memory_mb <= 0:
            raise ValueError("resource budgets must be positive")


@dataclass(frozen=True)
class TrialResult:
    trial_id: str
    architecture: str
    seed: int
    status: str
    prediction: float | None
    outcome: float | None
    confidence: float | None
    elapsed_seconds: float
    peak_memory_bytes: int | None
    error: str | None = None


def balanced_assignments(
    trial_count: int, seed: int, architectures: Sequence[str] = ARCHITECTURES
) -> list[tuple[int, str]]:
    """Randomized, near-balanced assignment; deterministic for a fixed seed."""
    if trial_count < 1:
        raise ValueError("trial_count must be >= 1")
    if not architectures or len(set(architectures)) != len(architectures):
        raise ValueError("architectures must be nonempty and unique")
    if any(a not in ARCHITECTURES for a in architectures):
        raise ValueError("unsupported architecture")
    labels = [architectures[i % len(architectures)] for i in range(trial_count)]
    random.Random(seed).shuffle(labels)
    return list(enumerate(labels))


def make_trial_specs(
    trial_count: int, seed: int, environment_ids: Sequence[str]
) -> list[TrialSpec]:
    if not environment_ids:
        raise ValueError("environment_ids must be nonempty")
    assignments = balanced_assignments(trial_count, seed)
    rng = random.Random(seed ^ 0x5A17)
    specs = []
    for index, architecture in assignments:
        specs.append(TrialSpec(
            trial_id=f"trial-{index:06d}",
            seed=rng.randrange(0, 2**32),
            architecture=architecture,
            environment_id=environment_ids[index % len(environment_ids)],
            intervention_seed=rng.randrange(0, 2**32),
        ))
    return specs


def _worker_entry(
    spec: TrialSpec,
    agent_factory: Callable[[str], Any],
    environment_factory: Callable[[str, int], Any],
    output: Any,
) -> None:
    """Child-process boundary: agent receives observations, not evaluator state."""
    started = time.perf_counter()
    try:
        import tracemalloc
        tracemalloc.start()
        rng = random.Random(spec.seed)
        agent = agent_factory(spec.architecture)
        env = environment_factory(spec.environment_id, spec.intervention_seed)
        observation = env.initial_observation()
        decision = agent.decide(observation, rng=rng)
        # Commit prediction before outcome is revealed.
        prediction = float(decision["prediction"])
        confidence = float(decision["confidence"])
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        env_result = env.evaluate_action(decision.get("action"))
        outcome = float(env_result["outcome"])
        _, peak = tracemalloc.get_traced_memory()
        output.put(asdict(TrialResult(
            trial_id=spec.trial_id,
            architecture=spec.architecture,
            seed=spec.seed,
            status="ok",
            prediction=prediction,
            outcome=outcome,
            confidence=confidence,
            elapsed_seconds=time.perf_counter() - started,
            peak_memory_bytes=peak,
        )))
    except BaseException as exc:
        output.put(asdict(TrialResult(
            trial_id=spec.trial_id,
            architecture=spec.architecture,
            seed=spec.seed,
            status="error",
            prediction=None,
            outcome=None,
            confidence=None,
            elapsed_seconds=time.perf_counter() - started,
            peak_memory_bytes=None,
            error=f"{type(exc).__name__}: {exc}",
        )))


def run_trial(
    spec: TrialSpec,
    agent_factory: Callable[[str], Any],
    environment_factory: Callable[[str, int], Any],
) -> TrialResult:
    """Run one trial in a spawned child; timeout terminates the child."""
    ctx = mp.get_context("spawn")
    queue = ctx.Queue(maxsize=1)
    process = ctx.Process(
        target=_worker_entry,
        args=(spec, agent_factory, environment_factory, queue),
        daemon=True,
    )
    process.start()
    process.join(spec.budget_seconds)
    if process.is_alive():
        process.terminate()
        process.join()
        return TrialResult(spec.trial_id, spec.architecture, spec.seed, "timeout",
                           None, None, None, spec.budget_seconds, None, "time budget exceeded")
    if queue.empty():
        return TrialResult(spec.trial_id, spec.architecture, spec.seed, "error",
                           None, None, None, 0.0, None, f"worker exit code {process.exitcode}; no result")
    payload = queue.get()
    return TrialResult(**payload)


def write_manifest(path: str | Path, specs: Sequence[TrialSpec], metadata: Mapping[str, Any]) -> str:
    """Write immutable pre-outcome manifest; return SHA-256 of canonical bytes."""
    document = {
        "schema_version": "smaa-blind-manifest-1",
        "metadata": dict(metadata),
        "trials": [asdict(spec) for spec in specs],
    }
    canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    digest = hashlib.sha256(canonical).hexdigest()
    envelope = {"sha256": digest, "manifest": document}
    Path(path).write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return digest


def append_result(path: str | Path, result: TrialResult) -> None:
    """Append one JSONL record; caller must protect file permissions/ownership."""
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(asdict(result), sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
