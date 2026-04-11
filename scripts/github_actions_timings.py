#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize GitHub Actions workflow timings via gh."
    )
    parser.add_argument(
        "--workflow",
        default="publish-image.yml",
        help="Workflow file name or workflow display name.",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Branch to filter workflow runs by.",
    )
    parser.add_argument(
        "--event",
        help="Optional GitHub event filter, such as push or workflow_dispatch.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of recent runs to inspect before filtering.",
    )
    parser.add_argument(
        "--include-latest-jobs",
        action="store_true",
        help="Include job and step timings for the latest successful run.",
    )
    parser.add_argument(
        "--run-id",
        type=int,
        help="Inspect one specific run instead of listing recent runs.",
    )
    return parser.parse_args()


def run_gh(*args: str) -> Any:
    proc = subprocess.run(
        ["gh", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or "gh command failed"
        raise RuntimeError(message)
    return json.loads(proc.stdout)


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def duration_minutes(started_at: str, completed_at: str) -> float:
    delta = parse_timestamp(completed_at) - parse_timestamp(started_at)
    return round(delta.total_seconds() / 60, 2)


def summarize_step(step: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "name": step["name"],
        "status": step["status"],
        "conclusion": step.get("conclusion"),
        "number": step["number"],
    }
    started_at = step.get("startedAt")
    completed_at = step.get("completedAt")
    if started_at and completed_at:
        summary["durationMinutes"] = duration_minutes(started_at, completed_at)
    return summary


def summarize_job(job: dict[str, Any], include_steps: bool) -> dict[str, Any]:
    summary = {
        "name": job["name"],
        "status": job["status"],
        "conclusion": job.get("conclusion"),
        "databaseId": job["databaseId"],
        "url": job["url"],
    }
    started_at = job.get("startedAt")
    completed_at = job.get("completedAt")
    if started_at and completed_at:
        summary["durationMinutes"] = duration_minutes(started_at, completed_at)
    if include_steps:
        summary["steps"] = [
            summarize_step(step)
            for step in job.get("steps", [])
            if step.get("startedAt") and step.get("completedAt")
        ]
    return summary


def summarize_run(run: dict[str, Any]) -> dict[str, Any]:
    summary = {
        "databaseId": run["databaseId"],
        "displayTitle": run["displayTitle"],
        "event": run["event"],
        "headBranch": run["headBranch"],
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "createdAt": run["createdAt"],
        "updatedAt": run["updatedAt"],
        "url": run["url"],
    }
    if run.get("createdAt") and run.get("updatedAt"):
        summary["durationMinutes"] = duration_minutes(run["createdAt"], run["updatedAt"])
    return summary


def filter_runs(runs: list[dict[str, Any]], branch: str, event: str | None) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for run in runs:
        if run["status"] != "completed" or run.get("conclusion") != "success":
            continue
        if branch and run.get("headBranch") != branch:
            continue
        if event and run.get("event") != event:
            continue
        filtered.append(run)
    return filtered


def build_recent_summary(
    workflow: str,
    branch: str,
    event: str | None,
    limit: int,
    include_latest_jobs: bool,
) -> dict[str, Any]:
    runs = run_gh(
        "run",
        "list",
        "--workflow",
        workflow,
        "--limit",
        str(limit),
        "--json",
        "databaseId,displayTitle,headBranch,event,status,conclusion,createdAt,updatedAt,url",
    )
    filtered = filter_runs(runs, branch=branch, event=event)
    durations = [duration_minutes(run["createdAt"], run["updatedAt"]) for run in filtered]

    summary: dict[str, Any] = {
        "workflow": workflow,
        "branch": branch,
        "event": event,
        "requestedLimit": limit,
        "successfulRuns": len(filtered),
        "runs": [summarize_run(run) for run in filtered],
    }

    if durations:
        summary["stats"] = {
            "averageDurationMinutes": round(statistics.fmean(durations), 2),
            "medianDurationMinutes": round(statistics.median(durations), 2),
            "minDurationMinutes": round(min(durations), 2),
            "maxDurationMinutes": round(max(durations), 2),
        }

    if include_latest_jobs and filtered:
        latest = filtered[0]
        run_detail = run_gh(
            "run",
            "view",
            str(latest["databaseId"]),
            "--json",
            "databaseId,displayTitle,event,headBranch,conclusion,createdAt,updatedAt,jobs,url",
        )
        summary["latestSuccessfulRun"] = {
            **summarize_run(run_detail),
            "jobs": [
                summarize_job(job, include_steps=True)
                for job in run_detail.get("jobs", [])
            ],
        }

    return summary


def build_single_run_summary(run_id: int) -> dict[str, Any]:
    run_detail = run_gh(
        "run",
        "view",
        str(run_id),
        "--json",
        "databaseId,displayTitle,event,headBranch,conclusion,createdAt,updatedAt,jobs,url",
    )
    return {
        "run": {
            **summarize_run(run_detail),
            "jobs": [
                summarize_job(job, include_steps=True) for job in run_detail.get("jobs", [])
            ],
        }
    }


def main() -> int:
    args = parse_args()
    try:
        if args.run_id is not None:
            payload = build_single_run_summary(args.run_id)
        else:
            payload = build_recent_summary(
                workflow=args.workflow,
                branch=args.branch,
                event=args.event,
                limit=args.limit,
                include_latest_jobs=args.include_latest_jobs,
            )
    except RuntimeError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
