from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "Frontend"
if str(FRONTEND) not in sys.path:
    sys.path.insert(0, str(FRONTEND))


def test_frontend_pages_are_importable():
    from auth.login import show_login
    from pages.employee.dashboard import show_employee_dashboard
    from pages.manager.dashboard import show_manager_dashboard
    from pages.mentor.dashboard import show_mentor_dashboard

    assert callable(show_login)
    assert callable(show_employee_dashboard)
    assert callable(show_manager_dashboard)
    assert callable(show_mentor_dashboard)
