class GlobalMarketState(TypedDict):
    """
    Global graph state passed between supervisor and sub-agent nodes.
    Sub-agents receive slices of this state to enforce strict scope boundary.
    """
    user_query: str
    target_sector: str
    retrieved_context: Optional[List[str]]
    analysis_findings: Optional[List[str]]
    confidence_score: Optional[float]
    iteration_count: int
    final_report: Optional[str]
    status: Literal["RUNNING", "NEEDS_RETRY", "COMPLETED", "FAILED"]