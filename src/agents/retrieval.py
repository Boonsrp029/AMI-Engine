class RetrievalQueryInput(BaseModel):
    sector: str = Field(description="Target market sector for analysis.")
    search_keywords: List[str] = Field(description="Extracted target search keywords.")

class RetrievalOutput(BaseModel):
    retrieved_chunks: List[str] = Field(description="List of relevant raw text context chunks.")
    source_count: int = Field(description="Total distinct sources retrieved.")