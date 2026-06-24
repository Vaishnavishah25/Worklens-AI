from app.services.risk_engine import RiskEngine

result = RiskEngine.calculate(
    confidence_score=5,
    open_blockers=2
)

print(result)