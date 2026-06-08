from typing import Dict, Any

class CriticalityScorer:
    WEIGHTS = {
        "revenue_impact": 0.30,
        "business_process": 0.25,
        "production_risk": 0.20,
        "user_impact": 0.15,
        "security_sensitivity": 0.10,
    }

    @classmethod
    def score_test_case(cls, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute criticality score based on input features (scale 0-10 for each).
        The features dict should have keys matching WEIGHTS.
        """
        total_score = 0.0
        for factor, weight in cls.WEIGHTS.items():
            value = features.get(factor, 0.0)
            # Ensure value is bounded between 0 and 10
            value = max(0.0, min(10.0, float(value)))
            total_score += value * weight

        category = cls.get_category(total_score)
        
        return {
            "score": round(total_score, 2),
            "category": category,
            "breakdown": {
                factor: features.get(factor, 0.0)
                for factor in cls.WEIGHTS
            }
        }

    @classmethod
    def get_category(cls, score: float) -> str:
        if score >= 8.5:
            return "Critical"
        elif score >= 6.5:
            return "High"
        elif score >= 4.0:
            return "Medium"
        else:
            return "Low"

    @classmethod
    def extract_features_from_text(cls, title: str, description: str, steps: str) -> Dict[str, float]:
        """
        A rule-based heuristic to extract scores from text contents of a test case.
        In a real application, this would use NLP / ML, but this is a heuristic rule engine.
        """
        text = f"{title or ''} {description or ''} {steps or ''}".lower()
        features = {
            "revenue_impact": 0.0,
            "business_process": 0.0,
            "production_risk": 0.0,
            "user_impact": 0.0,
            "security_sensitivity": 0.0,
        }
        
        # Revenue Impact Heuristics
        if any(w in text for w in ["billing", "payment", "revenue", "checkout", "transaction", "invoice"]):
            features["revenue_impact"] = 9.0
        elif any(w in text for w in ["order", "cart", "pricing", "quote"]):
            features["revenue_impact"] = 7.0
        else:
            features["revenue_impact"] = 3.0
            
        # Business Process Criticality
        if any(w in text for w in ["incident", "change request", "cab", "problem"]):
            features["business_process"] = 8.5
        elif any(w in text for w in ["hrsd", "facilities", "knowledge"]):
            features["business_process"] = 4.0
        else:
            features["business_process"] = 5.0

        # Production Risk
        if any(w in text for w in ["outage", "p1", "critical", "sev1", "downtime"]):
            features["production_risk"] = 9.5
        elif any(w in text for w in ["integration", "api", "sync"]):
            features["production_risk"] = 7.0
        else:
            features["production_risk"] = 4.0

        # User/Customer Impact
        if any(w in text for w in ["external", "portal", "customer", "public", "tenant"]):
            features["user_impact"] = 8.0
        else:
            features["user_impact"] = 3.0

        # Security Sensitivity
        if any(w in text for w in ["auth", "login", "password", "oauth", "sso", "acl", "permission"]):
            features["security_sensitivity"] = 9.0
        elif any(w in text for w in ["pii", "gdpr", "hipaa", "audit"]):
            features["security_sensitivity"] = 10.0
        else:
            features["security_sensitivity"] = 2.0

        return features

def calculate_criticality(title: str, description: str, steps: str) -> Dict[str, Any]:
    features = CriticalityScorer.extract_features_from_text(title, description, steps)
    return CriticalityScorer.score_test_case(features)
