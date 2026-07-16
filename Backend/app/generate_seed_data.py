"""
generate_seed_data.py

Populates worklens.db with realistic, multi-day daily_updates / blockers /
risk_scores for the REAL employees already in the users table (not the
fictional Priya Sharma / Ravi Kumar / Ankit Mehta from seed_faiss.py).

Safe to re-run: it checks for a marker note and skips employees who
already have >= 5 seeded updates, so it won't keep duplicating data.

Usage:
    python3 generate_seed_data.py
"""
from __future__ import annotations

from datetime import datetime, timedelta

from database.session import SessionLocal
from database.models.user import User
from database.models.daily_update import DailyUpdate
from database.models.blocker import Blocker
from database.models.risk_score import RiskScore
from services.risk_engine import RiskEngine

NOW = datetime.utcnow()


def d(days_ago: int, hour: int = 10) -> datetime:
    """Datetime `days_ago` days before now, at a fixed hour (for readability/order)."""
    base = NOW - timedelta(days=days_ago)
    return base.replace(hour=hour, minute=0, second=0, microsecond=0)


# ---------------------------------------------------------------------------
# Per-employee scripted history: (days_ago, work_done, planned_work, confidence,
#                                 blocker=None | {"days_ago", "description", "severity", "status"})
# ---------------------------------------------------------------------------
SCRIPTS: dict[str, list[dict]] = {

    "employee@worklens.ai": [  # Priya Shah — Backend Engineer, trending HIGH risk
        dict(days_ago=9, work_done="Started OAuth callback implementation for the login flow.",
             planned_work="Continue OAuth callback work and begin unit tests.", confidence=8),
        dict(days_ago=8, work_done="Wrote 6 unit tests for the OAuth callback handler.",
             planned_work="Finish remaining test coverage, start refresh token flow.", confidence=8),
        dict(days_ago=7, work_done="Blocked most of the day — staging environment still not provisioned by DevOps.",
             planned_work="Waiting on DevOps; resume auth flow once environment is ready.", confidence=5,
             blocker=dict(days_ago=7, description="Staging environment not provisioned by DevOps team. Blocking OAuth integration testing.",
                           severity="High", status="open")),
        dict(days_ago=6, work_done="Minor code cleanup while still waiting on the staging environment.",
             planned_work="Escalate blocker to Amit if not resolved by tomorrow.", confidence=4,
             blocker=dict(days_ago=6, description="Refresh-token flow cannot be tested without the staging OAuth provider — same root cause as the staging env blocker.",
                           severity="Medium", status="open")),
        dict(days_ago=5, work_done="Still fully blocked on staging. Escalated to manager directly — no ETA from DevOps yet.",
             planned_work="Can't plan next steps until the environment is unblocked.", confidence=3,
             blocker=dict(days_ago=5, description="No DevOps response for 5 days on the staging provisioning ticket. Manager escalation requested.",
                           severity="High", status="open")),
    ],

    "anita@worklens.ai": [  # Anita Rao — Frontend Engineer, steady LOW risk
        dict(days_ago=9, work_done="Built the reusable Button and Card components for the design system.",
             planned_work="Start on the dashboard layout grid.", confidence=8),
        dict(days_ago=7, work_done="Implemented the dashboard layout grid and responsive breakpoints.",
             planned_work="Wire up the KPI strip to live data.", confidence=8),
        dict(days_ago=4, work_done="Connected KPI strip to the API. Found a minor CORS issue in dev.",
             planned_work="Fix CORS config, then start the risk table component.", confidence=7,
             blocker=dict(days_ago=4, description="CORS error when calling the API from the Vite dev server on port 5173.",
                           severity="Low", status="resolved")),
        dict(days_ago=2, work_done="Fixed the CORS issue (added dev origin to allow list). Shipped the risk table component.",
             planned_work="Add sorting and filtering to the risk table.", confidence=9),
        dict(days_ago=1, work_done="Added sort/filter controls to the risk table. Wrote component tests.",
             planned_work="Polish styling and get design review from Kavitha.", confidence=9),
    ],

    "jordan@worklens.ai": [  # Jordan Lee — Platform Engineer, MEDIUM risk
        dict(days_ago=8, work_done="Investigated flaky CI runs on the auth branch.",
             planned_work="Isolate the flaky test and fix or quarantine it.", confidence=6),
        dict(days_ago=6, work_done="Found the flaky test was a race condition in the token refresh test. Fixed it.",
             planned_work="Re-run CI a few times to confirm stability.", confidence=7),
        dict(days_ago=3, work_done="CI green again. Started work on the deploy pipeline for the new dashboard service.",
             planned_work="Finish pipeline YAML and test a staging deploy.", confidence=6,
             blocker=dict(days_ago=3, description="Merge conflict between the pipeline branch and main after Priya's OAuth changes landed.",
                           severity="Medium", status="open")),
        dict(days_ago=2, work_done="Rebasing is taking longer than expected — the conflict touches shared CI config used by three other pipelines.",
             planned_work="Pair with Anita tomorrow since her branch also touches the shared config.", confidence=5,
             blocker=dict(days_ago=2, description="Staging deploy for the dashboard service is blocked until the shared CI config conflict is resolved.",
                           severity="Medium", status="open")),
        dict(days_ago=1, work_done="Still resolving the merge conflict — touches shared CI config, being careful not to break anyone else's pipeline.",
             planned_work="Finish the rebase tomorrow morning and get it merged before standup.", confidence=5),
    ],

    "noah@worklens.ai": [  # Noah Williams — Data Engineer, gone quiet → HIGH via days-no-update
        dict(days_ago=9, work_done="Kicked off the data warehouse migration — schema diff against the old system.",
             planned_work="Start writing the migration scripts.", confidence=7),
        dict(days_ago=8, work_done="Wrote migration scripts for the users and updates tables.",
             planned_work="Test migration on a copy of prod data.", confidence=6),
        dict(days_ago=7, work_done="Migration test run hit a timezone bug in the timestamp columns.",
             planned_work="Debug the timezone handling before continuing.", confidence=4,
             blocker=dict(days_ago=7, description="Timestamp columns are being migrated as naive datetimes, causing off-by-one-day errors across timezones.",
                           severity="Medium", status="open")),
        dict(days_ago=7, work_done="Also flagged: no read access to the prod replica needed to validate the migration output.",
             planned_work="Requested prod-replica access from the platform team — waiting on approval.", confidence=4,
             blocker=dict(days_ago=7, description="No read access to the prod database replica — can't validate migration output against real data.",
                           severity="Medium", status="open")),
        # No updates in the last week — deliberately, to test the days_no_update / silence signal.
    ],

    "sara@worklens.ai": [  # Sara Ahmed — QA Engineer, LOW-MEDIUM
        dict(days_ago=7, work_done="Wrote end-to-end tests for the daily update submission flow.",
             planned_work="Add coverage for the blocker reporting flow.", confidence=7),
        dict(days_ago=5, work_done="Added blocker-flow E2E tests. One test is flaky on CI but passes locally.",
             planned_work="Investigate the flaky test before it blocks other people's PRs.", confidence=6,
             blocker=dict(days_ago=5, description="E2E test for blocker submission is flaky on CI — intermittent timeout waiting for the toast notification.",
                           severity="Low", status="open")),
        dict(days_ago=2, work_done="Root-caused the flaky test: toast animation timing. Increased the wait threshold and it's stable now.",
             planned_work="Move on to writing tests for the weekly summary view.", confidence=8,
             blocker=dict(days_ago=2, description="(resolution) Flaky toast-wait test — fixed by increasing the wait timeout in the E2E helper.",
                           severity="Low", status="resolved")),
    ],

    "employee2@worklens.ai": [  # Jai ram — AI Intern, continues his real submitted thread
        dict(days_ago=1, work_done="Kept working through the LangChain prompt-chaining issue from yesterday — narrowed it to a variable scoping bug in the prompt template.",
             planned_work="Fix the scoping bug and get the chain running end to end.", confidence=5),
        dict(days_ago=0, work_done="Fixed the prompt template scoping bug. Chain runs end to end now, output quality still inconsistent.",
             planned_work="Tune the prompt wording and add a few-shot example to stabilize output.", confidence=6),
    ],

    "hello345@gmail.com": [  # hello123 — Frontend Intern, continues his real submitted thread
        dict(days_ago=1, work_done="Read through Pydantic docs after yesterday's confusion — understand validators now, applied one to the update schema.",
             planned_work="Add validators to the remaining request schemas.", confidence=6,
             blocker=dict(days_ago=1, description="(resolution) Was confused about Pydantic validators — resolved after reading the docs and pairing with Jordan for 20 minutes.",
                           severity="Low", status="resolved")),
        dict(days_ago=0, work_done="Added validators to the blocker and login request schemas. Wrote two small unit tests.",
             planned_work="Ask for a PR review before end of day.", confidence=7),
    ],

    "test@test.com": [  # Test User — minimal, just enough to not be a total blank row
        dict(days_ago=3, work_done="Environment setup and onboarding checklist.",
             planned_work="Shadow Anita on a frontend ticket.", confidence=7),
    ],
}


def main() -> None:
    with SessionLocal() as session:
        users_by_email = {u.email: u for u in session.query(User).all()}

        created_updates = 0
        created_blockers = 0
        created_risk_rows = 0

        for email, entries in SCRIPTS.items():
            user = users_by_email.get(email)
            if not user:
                print(f"  ! No user found for {email} — skipping")
                continue

            existing = session.query(DailyUpdate).filter(DailyUpdate.user_id == user.id).count()
            if existing >= 5:
                print(f"  = {user.name}: already has {existing} updates, skipping re-seed")
                continue

            for entry in entries:
                update = DailyUpdate(
                    user_id=user.id,
                    work_done=entry["work_done"],
                    planned_work=entry["planned_work"],
                    confidence_score=float(entry["confidence"]),
                    created_at=d(entry["days_ago"]),
                )
                session.add(update)
                session.flush()  # get update.id for the FK below
                created_updates += 1

                b = entry.get("blocker")
                if b:
                    blocker = Blocker(
                        user_id=user.id,
                        update_id=update.id,
                        title="Submitted blocker",
                        description=b["description"],
                        severity=b["severity"],
                        status=b["status"],
                        created_at=d(b["days_ago"]),
                    )
                    session.add(blocker)
                    created_blockers += 1

            session.commit()
            print(f"  + {user.name}: added {len(entries)} updates")

        # ------------------------------------------------------------
        # Backfill risk_scores: one live snapshot per employee, computed
        # the same way api/v1/ai.py's _fetch_risk_json() does it.
        # ------------------------------------------------------------
        print("\nComputing risk snapshots...")
        employees = session.query(User).filter(User.role == "Employee").all()
        results = []
        for u in employees:
            last = (
                session.query(DailyUpdate)
                .filter(DailyUpdate.user_id == u.id)
                .order_by(DailyUpdate.created_at.desc())
                .first()
            )
            days_since = (NOW - last.created_at).days if last else 999

            open_blockers = (
                session.query(Blocker)
                .filter(Blocker.user_id == u.id, Blocker.status == "open")
                .count()
            )

            recent = (
                session.query(DailyUpdate.confidence_score)
                .filter(DailyUpdate.user_id == u.id)
                .order_by(DailyUpdate.created_at.desc())
                .limit(7)
                .all()
            )
            avg_conf = sum(r[0] for r in recent) / len(recent) if recent else 10

            risk = RiskEngine.calculate(
                confidence_score=avg_conf,
                open_blockers=open_blockers,
                days_no_update=days_since,
            )

            session.add(RiskScore(employee_id=u.id, score=risk["score"], label=risk["label"], created_at=NOW))
            created_risk_rows += 1
            results.append((u.name, days_since, open_blockers, round(avg_conf, 1), risk["score"], risk["label"]))

        session.commit()

        print(f"\nDone. +{created_updates} updates, +{created_blockers} blockers, +{created_risk_rows} risk_scores rows.\n")
        print(f"{'Employee':<16}{'days_no_upd':<13}{'open_blk':<10}{'avg_conf':<10}{'score':<8}{'label'}")
        for name, days_since, ob, avg_conf, score, label in results:
            print(f"{name:<16}{days_since:<13}{ob:<10}{avg_conf:<10}{score:<8}{label}")


if __name__ == "__main__":
    main()