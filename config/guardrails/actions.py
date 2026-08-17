"""
Custom NeMo Guardrail Actions for Market Research Validation.
"""

from nemoguardrails.actions import action


@action(name="check_topic_safety")
async def check_topic_safety(context: dict = None) -> bool:
    """
    Validates if the generated report stays within market research bounds.
    
    Returns:
        True if the output is off-topic (triggers block flow).
        False if the output is valid market research.
    """
    if not context:
        return False
        
    report_text = context.get("response", "").lower()
    
    # Example domain boundary checks
    forbidden_topics = [
        "gambling recommendation",
        "medical diagnosis",
        "personal financial advice",
    ]
    
    # Check if report contains forbidden domain topics
    is_off_topic = any(topic in report_text for topic in forbidden_topics)
    return is_off_topic