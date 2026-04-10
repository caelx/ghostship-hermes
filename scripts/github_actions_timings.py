#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from typing import Any


def run_json(cmd: list[str]) -> Any:
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)


def duration_minutes(started_at: str | None, updated_at: str | None) -> float | None:
    start = parse_ts(started_at)
    end = parse_ts(updated_at)
    if start is None or end is None:
        return None
    return round((end - start).total_seconds() / 60, 2)


def workflow_summary(workflow: str, limit: int) -> dict[str, Any]:
    runs = run_json([
        'gh', 'run', 'list', '--workflow', workflow, '--limit', str(limit),
        '--json', 'databaseId,startedAt,updatedAt,conclusion,headBranch,event,url'
    ])
    successful = [run for run in runs if run.get('conclusion') == 'success']
    durations = [
        duration_minutes(run.get('startedAt'), run.get('updatedAt'))
        for run in successful
    ]
    durations = [value for value in durations if value is not None]
    summary: dict[str, Any] = {
        'workflow': workflow,
        'successful_runs': len(successful),
        'latest_run_id': successful[0]['databaseId'] if successful else None,
        'latest_run_url': successful[0]['url'] if successful else None,
    }
    if durations:
        summary.update(
            {
                'avg_minutes': round(sum(durations) / len(durations), 2),
                'min_minutes': min(durations),
                'max_minutes': max(durations),
            }
        )
    else:
        summary.update(
            {
                'avg_minutes': None,
                'min_minutes': None,
                'max_minutes': None,
            }
        )
    return summary


def latest_job_breakdown(run_id: int) -> list[dict[str, Any]]:
    payload = run_json(['gh', 'run', 'view', str(run_id), '--json', 'jobs'])
    jobs = payload.get('jobs', [])
    return [
        {
            'name': job['name'],
            'minutes': duration_minutes(job.get('startedAt'), job.get('completedAt')),
            'conclusion': job.get('conclusion'),
        }
        for job in jobs
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Summarize GitHub Actions workflow timings as JSON.'
    )
    parser.add_argument(
        '--workflow',
        action='append',
        dest='workflows',
        help='Workflow filename to summarize. Repeat for multiple workflows.',
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Number of recent runs to inspect per workflow (default: 10).',
    )
    parser.add_argument(
        '--include-latest-jobs',
        action='store_true',
        help='Include a job-level breakdown for the latest successful run of each workflow.',
    )
    args = parser.parse_args()

    workflows = args.workflows or ['ci.yml', 'publish-image.yml']
    output = {'workflows': []}
    for workflow in workflows:
        summary = workflow_summary(workflow, args.limit)
        if args.include_latest_jobs and summary['latest_run_id'] is not None:
            summary['latest_jobs'] = latest_job_breakdown(summary['latest_run_id'])
        output['workflows'].append(summary)

    print(json.dumps(output, indent=2, sort_keys=False))


if __name__ == '__main__':
    main()
