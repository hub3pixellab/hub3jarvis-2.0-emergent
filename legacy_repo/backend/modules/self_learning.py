from datetime import datetime, timezone
from modules.database import db_manager
from bson import ObjectId

class SelfLearningEngine:
    def __init__(self):
        self.feedback_weights = {"positive": 1.1, "negative": 0.9, "neutral": 1.0}

    async def log_interaction(self, user_id, question, answer, model, confidence, cost):
        entry = {
            "user_id": user_id,
            "question": question,
            "answer": answer,
            "model": model,
            "confidence": confidence,
            "cost": cost,
            "feedback": None,
            "created_at": datetime.now(timezone.utc)
        }
        result = await db_manager.learning_logs.insert_one(entry)
        return str(result.inserted_id)

    async def add_feedback(self, log_id, feedback, comment=""):
        valid = ["positive", "negative", "neutral"]
        if feedback not in valid:
            return {"error": f"Feedback invalido. Use: {valid}"}
        await db_manager.learning_logs.update_one(
            {"_id": ObjectId(log_id)},
            {"$set": {
                "feedback": feedback,
                "feedback_comment": comment,
                "feedback_at": datetime.now(timezone.utc)
            }}
        )
        return {"status": "recorded", "feedback": feedback}

    async def get_user_patterns(self, user_id, limit=50):
        logs = await db_manager.learning_logs.find(
            {"user_id": user_id}
        ).sort("created_at", -1).to_list(length=limit)

        if not logs:
            return {"patterns": {}, "total": 0}

        model_counts = {}
        positive_count = 0
        negative_count = 0
        total_cost = 0

        for log in logs:
            model = log.get("model", "unknown")
            model_counts[model] = model_counts.get(model, 0) + 1
            fb = log.get("feedback")
            if fb == "positive":
                positive_count += 1
            elif fb == "negative":
                negative_count += 1
            total_cost += log.get("cost", 0)

        return {
            "total_interactions": len(logs),
            "model_usage": model_counts,
            "positive_feedback": positive_count,
            "negative_feedback": negative_count,
            "total_cost": round(total_cost, 6),
            "satisfaction_rate": round(positive_count / max(len(logs), 1) * 100, 1)
        }

learning_engine = SelfLearningEngine()
