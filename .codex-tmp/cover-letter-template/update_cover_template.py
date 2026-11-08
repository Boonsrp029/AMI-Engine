from pathlib import Path
from docx import Document
src=Path(r"D:\Learning for jobs\Resume-CV\Sirapop_Remote_AI_Data_Cover_Letter_Master.docx")
out=Path(r"D:\Learning for jobs\Autonomous-Market-Intelligence-Engine-main\AMI-Engine\.codex-tmp\cover-letter-template\Sirapop_Remote_AI_Data_Cover_Letter_Master_Updated.docx")
d=Document(src)
updates={
 1:"[Professional Headline]",
 4:"[Date]\n[Hiring Manager or Hiring Team]\n[Company Name]\n[City, Country]",
 6:"Dear [Hiring Manager or Hiring Team],",
 8:("I am applying for the [Role Title] position at [Company Name]. I am a Computer Science graduate and Research Analyst based in Chiang Mai, Thailand, with experience maintaining and verifying structured data at scale. [Add one sentence linking a specific requirement in the role description to relevant experience.] I am particularly interested in [Company, team, product or business priority], where I could contribute through careful analysis, practical software and collaboration with product or engineering colleagues."),
 9:("In my portfolio project, the Autonomous Market Intelligence Engine (AMI Engine), I built a local market-research workflow that combines retrieval, evidence mapping, source-linked analysis, guardrails and human review. Recent development added an opt-in bounded-subtask path: tasks carry explicit limits and dependencies, progress is persisted, evidence stays tied to its source and subtask, and aggregation is deterministic with late results fenced after failure or cancellation. The sequential workflow remains available, and a draft cannot be exported without review and approval. Offline integration tests exercise these engineering contracts; answer quality, independent reviewer usefulness and production operations are still being qualified. This work has strengthened my ability to reason about traceability, failure handling, resource constraints and responsible deployment claims."),
 10:("In my remote Research Analyst role at Yamada Research, I have completed more than 6,500 TikTok civic-data updates, maintained structured datasets across eight countries, and verified voter information spanning more than 20 countries. This work strengthened my attention to data quality, source checking and clear documentation. [Add a concise example connecting these strengths to the role.]"),
 11:("I would welcome the opportunity to contribute to [Company Name] as a [Role Title], particularly on [team, product or business problem]. Thank you for considering my application. I would be glad to discuss how my research experience and software portfolio could support your priorities.")
}
for idx,text in updates.items():
 p=d.paragraphs[idx]
 # Keep paragraph and first run formatting; replace only text inside this intended slot.
 if p.runs:
  first=p.runs[0]
  for r in p.runs[1:]:
   r._element.getparent().remove(r._element)
  first.text=text
 else:
  p.add_run(text)
d.save(out)
print(out)

