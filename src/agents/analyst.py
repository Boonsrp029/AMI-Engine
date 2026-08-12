class AnalysisInput(BaseModel):
    sector: str
    contexts: List[str]

class AnalysisOutput(BaseModel):
    key_findings: List[str] = Field(description="Synthesized market growth drivers.")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence score of analysis.")
    hallucination_flag: bool = Field(description="True if context lacks sufficient backing.")