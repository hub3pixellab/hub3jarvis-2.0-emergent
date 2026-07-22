SENSITIVE_ACTIONS = [
    "financial_transaction", "legal_document", "third_party_communication",
    "device_control", "data_sharing", "delete_asset", "send_email", "send_whatsapp",
]
BLOCKED_SOURCES = ["onion", "tor", "darknet", "dark.web", ".onion"]
ALLOWED_SOURCES = [
    "arxiv.org", "pubmed", "semanticscholar.org", "web.archive.org",
    "scholar.google.com", "tavily.com", "perplexity.ai", "serper.dev",
]

class PolicyEngine:
    async def check_whitelist(self, phone, action, db):
        contact = await db.whitelist.find_one({"phone": phone})
        if not contact:
            return {"allowed": True}
        level = contact.get("level", "absolute")
        if level == "absolute":
            return {"allowed": False, "reason": f"Proteção absoluta: {contact.get('name', phone)}"}
        if level == "high" and action in ["whatsapp", "device_control", "send_email"]:
            return {"allowed": False, "reason": f"Proteção alta: {contact.get('name')}"}
        if level == "medium" and action == "data_sharing":
            return {"allowed": False, "reason": f"Proteção média: {contact.get('name')}"}
        return {"allowed": True}

    def requires_confirmation(self, action):
        if action in SENSITIVE_ACTIONS:
            return {"requires_confirmation": True, "message": f"Ação sensível: {action}. Confirma?"}
        return {"requires_confirmation": False}

    def validate_search(self, source):
        s = source.lower()
        for b in BLOCKED_SOURCES:
            if b in s:
                return {"valid": False, "reason": f"Fonte bloqueada (Lei 3): {source}"}
        return {"valid": True}

    async def evaluate(self, user_id, action, context, db):
        result = {"allowed": True, "warnings": []}
        if "phone" in context:
            wl = await self.check_whitelist(context["phone"], action, db)
            if not wl["allowed"]:
                result["allowed"] = False
                result["warnings"].append(wl["reason"])
        conf = self.requires_confirmation(action)
        if conf["requires_confirmation"]:
            result["warnings"].append(conf["message"])
        if "search_source" in context:
            src = self.validate_search(context["search_source"])
            if not src["valid"]:
                result["allowed"] = False
                result["warnings"].append(src["reason"])
        return result

policy_engine = PolicyEngine()
