"""The three experimental arms.

  A0 : single model, one shot.
  A1 : single model, self-retry up to N (sees its own failing test output).
  B  : worker model generates -> SEPARATE evaluator emits a reflexion -> retry, up to N.

Read-off:  (A1 - A0) = value of retries.   (B - A1) = value of a separate evaluator.
The thesis lives in (B - A1).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import prompts
from openrouter_client import LLMCall, OpenRouterClient
from sandbox import Task, run_attempt
from schemas import parse_verdict, parse_worker


@dataclass
class Trajectory:
    arm: str
    task: str
    trial: int
    solved: bool = False
    attempts_used: int = 0
    calls: List[LLMCall] = field(default_factory=list)
    error: str = ""

    @property
    def cost_usd(self) -> float: return sum(c.cost_usd for c in self.calls)
    @property
    def input_tokens(self) -> int: return sum(c.input_tokens for c in self.calls)
    @property
    def output_tokens(self) -> int: return sum(c.output_tokens for c in self.calls)
    @property
    def cached_tokens(self) -> int: return sum(c.cached_tokens for c in self.calls)
    @property
    def latency_s(self) -> float: return sum(c.latency_s for c in self.calls)


def _generate(client: OpenRouterClient, cfg: dict, model: str, task: Task,
              reflexions: List[str], last_stdout: str, session_id: str) -> LLMCall:
    return client.chat(
        model,
        [
            {"role": "system", "content": prompts.WORKER_SYSTEM.format(allowed=", ".join(task.allowed_edit))},
            {"role": "user", "content": prompts.worker_user(task, reflexions, last_stdout)},
        ],
        session_id=session_id,
        temperature=cfg.get("temperature", 0.0),
        json_mode=cfg.get("json_mode", True),
    )


def arm_a0(client, cfg, task, trial) -> Trajectory:
    traj = Trajectory(arm="A0", task=task.name, trial=trial, attempts_used=1)
    sid = f"A0-{task.name}-{trial}"
    try:
        call = _generate(client, cfg, cfg["single_model"], task, [], "", sid)
        traj.calls.append(call)
        res = run_attempt(task, parse_worker(call.content).files)
        traj.solved = res.passed
    except Exception as e:  # noqa: BLE001
        traj.error = f"{type(e).__name__}: {e}"
    return traj


def arm_a1(client, cfg, task, trial) -> Trajectory:
    traj = Trajectory(arm="A1", task=task.name, trial=trial)
    sid = f"A1-{task.name}-{trial}"
    last_stdout = ""
    try:
        for i in range(int(cfg["attempts"])):
            traj.attempts_used = i + 1
            call = _generate(client, cfg, cfg["single_model"], task, [], last_stdout, sid)
            traj.calls.append(call)
            res = run_attempt(task, parse_worker(call.content).files)
            if res.passed:
                traj.solved = True
                break
            last_stdout = res.stdout  # self-reflexion: same model sees its own failure
    except Exception as e:  # noqa: BLE001
        traj.error = f"{type(e).__name__}: {e}"
    return traj


def arm_b(client, cfg, task, trial) -> Trajectory:
    traj = Trajectory(arm="B", task=task.name, trial=trial)
    sid = f"B-{task.name}-{trial}"
    reflexions: List[str] = []
    last_stdout = ""
    try:
        for i in range(int(cfg["attempts"])):
            traj.attempts_used = i + 1
            call = _generate(client, cfg, cfg["worker_model"], task, reflexions, last_stdout, sid)
            traj.calls.append(call)
            files: Dict[str, str] = parse_worker(call.content).files
            res = run_attempt(task, files)
            if res.passed:
                traj.solved = True
                break
            last_stdout = res.stdout
            # Separate evaluator turns the failure into a compact constraint.
            ev = client.chat(
                cfg["evaluator_model"],
                [
                    {"role": "system", "content": prompts.EVALUATOR_SYSTEM},
                    {"role": "user", "content": prompts.evaluator_user(task, files, res.stdout)},
                ],
                session_id=sid + "-eval",
                temperature=cfg.get("temperature", 0.0),
                json_mode=cfg.get("json_mode", True),
            )
            traj.calls.append(ev)
            try:
                verdict = parse_verdict(ev.content)
                if verdict.reflexion:
                    reflexions.append(verdict.reflexion)
            except Exception:  # noqa: BLE001 - bad verdict shouldn't kill the run
                pass
    except Exception as e:  # noqa: BLE001
        traj.error = f"{type(e).__name__}: {e}"
    return traj


ARMS = {"A0": arm_a0, "A1": arm_a1, "B": arm_b}
