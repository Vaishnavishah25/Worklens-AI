class RiskEngine:

    @staticmethod
    def calculate(
        confidence_score: float,
        open_blockers: int,
        days_no_update: int = 0,
        overdue_tasks: int = 0,
        total_tasks: int = 1
    ):

        d_norm = min(days_no_update / 7, 1.0)

        b_norm = min(open_blockers / 3, 1.0)

        c_norm = (10 - confidence_score) / 9

        t_norm = (
            min(overdue_tasks / total_tasks, 1.0)
            if total_tasks > 0
            else 0
        )

        score = (
            0.35 * d_norm +
            0.25 * b_norm +
            0.25 * c_norm +
            0.15 * t_norm
        )

        if score < 0.3:
            label = "LOW"
        elif score < 0.6:
            label = "MEDIUM"
        else:
            label = "HIGH"

        return {
            "score": round(score, 2),
            "label": label
        }