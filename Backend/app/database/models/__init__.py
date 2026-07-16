try:
    from app.database.models.user import User
    from app.database.models.daily_update import DailyUpdate
    from app.database.models.blocker import Blocker
    from app.database.models.risk_score import RiskScore
except ModuleNotFoundError:
    from database.models.user import User
    from database.models.daily_update import DailyUpdate
    from database.models.blocker import Blocker
    from database.models.risk_score import RiskScore

__all__ = ["User", "DailyUpdate", "Blocker", "RiskScore"]
