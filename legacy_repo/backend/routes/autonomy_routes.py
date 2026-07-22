"""Rotas de Autonomia JARVIS v4.2 — Self-test e Status"""
import pytest, sys, os, time
from io import StringIO

def register_routes(app, orchestrator_instance):
    @app.get("/autonomy/status")
    async def autonomy_status():
        status = orchestrator_instance.status.copy() if hasattr(orchestrator_instance, 'status') else {"online": False, "summary": "Orquestrador nao inicializado"}
        svc_online = sum(1 for s in status.get("services", {}).values() if s.get("online"))
        svc_total = len(status.get("services", {}))
        status["services_online"] = svc_online
        status["services_total"] = svc_total
        status["health_pct"] = round((svc_online / max(svc_total, 1)) * 100, 1) if svc_total > 0 else 0
        return status

    @app.get("/api/jarvis/self-test")
    async def self_test():
        tests_dir = os.path.join(os.path.dirname(__file__), "..", "tests")
        if not os.path.exists(tests_dir):
            tests_dir = os.path.join(os.path.dirname(__file__), "..", "..", "tests")
        start = time.time()
        captured = StringIO()
        old_stdout, sys.stdout = sys.stdout, captured
        exit_code = pytest.main([tests_dir, "-v", "--tb=short", "--no-header", "-q"], plugins=[])
        sys.stdout = old_stdout
        output, duration_ms = captured.getvalue(), round((time.time() - start) * 1000, 1)
        lines = output.strip().split("\n")
        passed = sum(1 for l in lines if "PASSED" in l)
        failed = sum(1 for l in lines if "FAILED" in l)
        errors = sum(1 for l in lines if "ERROR" in l)
        results = []
        for line in lines:
            line = line.strip()
            if line and "::" in line:
                outcome = "passed"
                if "FAILED" in line: outcome = "failed"
                elif "ERROR" in line: outcome = "error"
                results.append({"test": line.split()[0], "outcome": outcome})
        return {"status": "passed" if exit_code == 0 else "failed", "exit_code": exit_code, "total": passed+failed+errors, "passed": passed, "failed": failed, "errors": errors, "duration_ms": duration_ms, "output": output[:2000], "results": results[:50], "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}

    return app
