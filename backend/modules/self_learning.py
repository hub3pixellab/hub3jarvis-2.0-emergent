"""
Self-Learning Engine — logs consensus interactions and user feedback.
Absorbed from hub3pixellab/hub3jarvis (legacy), rewritten to use string UUIDs
instead of ObjectId to match the rest of the v4.2 codebase.

Collections used:
- learning_logs : { id, user_id, question, answer, model, confidence, cost, feedback, feedback_comment, created_at, feedback_at }
"""
import uuid
from datetime import datetime, timezone

VALID_FEEDBACK = {"positive", "negative", "neutral"}


class SelfLearningEngine:
    def __init__(self, db):
        self.db = db
        self.logs = db.learning_logs

    async def log_interaction(self, user_id: str, question: str, answer: str, model: str, confidence: float, cost: float):
        entry = {
            "id": f"log_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "question": question,
            "answer": answer,
            "model": model,
            "confidence": confidence,
            "cost": cost,
            "feedback": None,
            "feedback_comment": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "feedback_at": None,
        }
        await self.logs.insert_one(entry)
        return entry["id"]

    async def add_feedback(self, log_id: str, feedback: str, comment: str = ""):
        if feedback not in VALID_FEEDBACK:
            return {"error": f"Invalid feedback. Use: {list(VALID_FEEDBACK)}"}
        r = await self.logs.update_one(
            {"id": log_id},
            {"$set": {"feedback": feedback, "feedback_comment": comment,
                       "feedback_at": datetime.now(timezone.utc).isoformat()}},
        )
        if r.matched_count == 0:
            return {"error": "log not found"}
        return {"status": "recorded", "feedback": feedback}

    async def get_user_patterns(self, user_id: str, limit: int = 50):
        rows = await self.logs.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        if not rows:
            return {"total_interactions": 0, "model_usage": {}, "positive_feedback": 0,
                    "negative_feedback": 0, "total_cost": 0, "satisfaction_rate": 0}
        model_counts, pos, neg, total_cost = {}, 0, 0, 0
        for r in rows:
            m = r.get("model", "unknown")
            model_counts[m] = model_counts.get(m, 0) + 1
            fb = r.get("feedback")
            if fb == "positive": pos += 1
            elif fb == "negative": neg += 1
            total_cost += r.get("cost", 0) or 0
        return {
            "total_interactions": len(rows),
            "model_usage": model_counts,
            "positive_feedback": pos,
            "negative_feedback": neg,
            "total_cost": round(total_cost, 6),
            "satisfaction_rate": round(pos / max(len(rows), 1) * 100, 1),
        }

    async def recent(self, user_id: str, limit: int = 10):
        return await self.logs.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)


def make_learning_engine(db):
    return SelfLearningEngine(db)
