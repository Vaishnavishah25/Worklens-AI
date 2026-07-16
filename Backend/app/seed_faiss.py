"""
Backend/app/seed_faiss.py
Run once to populate FAISS with test data so the AI endpoints work.
Usage: cd Backend/app && python seed_faiss.py
"""
import asyncio
from datetime import date, timedelta
from vectorstore.indexer import index_update, index_blocker, index_feedback
from vectorstore.faiss_store import faiss_store

# ── Use proper UUIDs so Swagger accepts them without validation errors ─────
TEAM_ID = "550e8400-e29b-41d4-a716-446655440000"
EMP_1   = "660e8400-e29b-41d4-a716-446655440001"   # Priya Sharma
EMP_2   = "660e8400-e29b-41d4-a716-446655440002"   # Ravi Kumar
EMP_3   = "660e8400-e29b-41d4-a716-446655440003"   # Ankit Mehta

TEST_UPDATES = [
    {
        "id": "u001", "employee_id": EMP_1, "team_id": TEAM_ID,
        "full_name": "Priya Sharma",
        "date": str(date.today() - timedelta(days=1)),
        "work_done": "Fixed OAuth callback bug and wrote 14 unit tests for login flow.",
        "next_steps": "Finish refresh token flow and review Ravi's PR.",
        "confidence_score": 5, "mood": 3,
        "blocker_description": "Staging environment not provisioned by DevOps team.",
    },
    {
        "id": "u002", "employee_id": EMP_1, "team_id": TEAM_ID,
        "full_name": "Priya Sharma",
        "date": str(date.today() - timedelta(days=2)),
        "work_done": "Minor code cleanup while waiting for DevOps to provision staging.",
        "next_steps": "Wait for staging env, then complete auth flow.",
        "confidence_score": 5, "mood": 2,
        "blocker_description": "Staging environment still not ready.",
    },
    {
        "id": "u003", "employee_id": EMP_2, "team_id": TEAM_ID,
        "full_name": "Ravi Kumar",
        "date": str(date.today()),
        "work_done": "Merged PR #47. Resolved merge conflict on auth branch.",
        "next_steps": "Rebase and resubmit CI pipeline.",
        "confidence_score": 7, "mood": 4,
        "blocker_description": None,
    },
    {
        "id": "u004", "employee_id": EMP_3, "team_id": TEAM_ID,
        "full_name": "Ankit Mehta",
        "date": str(date.today()),
        "work_done": "Completed OAuth integration end to end. All tests passing.",
        "next_steps": "Start on the dashboard analytics module.",
        "confidence_score": 9, "mood": 5,
        "blocker_description": None,
    },
    {
        "id": "u005", "employee_id": EMP_2, "team_id": TEAM_ID,
        "full_name": "Ravi Kumar",
        "date": str(date.today() - timedelta(days=1)),
        "work_done": "Reviewed 3 PRs. Wrote integration tests for auth module.",
        "next_steps": "Complete CI pipeline fix.",
        "confidence_score": 6, "mood": 3,
        "blocker_description": "Merge conflict on auth branch blocking CI.",
    },
]

TEST_BLOCKERS = [
    {
        "id": "b001", "employee_id": EMP_1, "team_id": TEAM_ID,
        "full_name": "Priya Sharma",
        "date": str(date.today() - timedelta(days=3)),
        "description": "Staging environment not provisioned by DevOps team. Waiting 3 days.",
        "severity": 2, "status": "open",
    },
    {
        "id": "b002", "employee_id": EMP_2, "team_id": TEAM_ID,
        "full_name": "Ravi Kumar",
        "date": str(date.today() - timedelta(days=1)),
        "description": "Merge conflict on auth branch blocking CI pipeline.",
        "severity": 1, "status": "open",
    },
]

TEST_FEEDBACK = [
    {
        "id": "f001", "to_employee_id": EMP_3, "team_id": TEAM_ID,
        "from_name": "Kavitha R.", "to_name": "Ankit Mehta",
        "type": "praise",
        "content": "Strong PR review quality this week. Comments are constructive and specific.",
        "date": str(date.today() - timedelta(days=1)),
    },
    {
        "id": "f002", "to_employee_id": EMP_1, "team_id": TEAM_ID,
        "from_name": "Kavitha R.", "to_name": "Priya Sharma",
        "type": "guidance",
        "content": "The staging env blocker should be escalated to Amit earlier. Don't hold it 3 days.",
        "date": str(date.today() - timedelta(days=2)),
    },
]

async def main():
    print("Seeding FAISS with test data...")
    print(f"Before: {faiss_store.total_vectors} vectors")

    for u in TEST_UPDATES:
        doc_id = await index_update(u)
        print(f"  Indexed update  : {doc_id}")

    for b in TEST_BLOCKERS:
        doc_id = await index_blocker(b)
        print(f"  Indexed blocker : {doc_id}")

    for f in TEST_FEEDBACK:
        doc_id = await index_feedback(f)
        print(f"  Indexed feedback: {doc_id}")

    faiss_store.save()
    print(f"\nDone! FAISS now has {faiss_store.total_vectors} vectors")
    print("\n── Copy this team_id into every Swagger request ──")
    print(f"  team_id : {TEAM_ID}")
    print(f"  emp_1   : {EMP_1}  (Priya Sharma)")
    print(f"  emp_2   : {EMP_2}  (Ravi Kumar)")
    print(f"  emp_3   : {EMP_3}  (Ankit Mehta)")
    print("\n── Questions to test ──")
    print("  Why is Priya delayed?")
    print("  Who is blocked on the team and what are the blockers?")
    print("  What is Ravi working on?")
    print("  Who is performing well this week?")
    print("  Prepare me for a 1 on 1 with Priya today")
    print("  Who needs my attention most urgently right now?")

asyncio.run(main())