from docx import Document
from pathlib import Path
import hashlib
p=Path(r"D:\Learning for jobs\Resume-CV\Sirapop_Remote_AI_Data_Cover_Letter_Master.docx")
d=Document(p)
print("SHA256",hashlib.sha256(p.read_bytes()).hexdigest())
for i,x in enumerate(d.paragraphs):
 print(f"P{i} [{x.style.name}]: {x.text!r}")
for ti,t in enumerate(d.tables):
 print("TABLE",ti)
 for ri,row in enumerate(t.rows):
  print("ROW",ri,[c.text for c in row.cells])
for i,s in enumerate(d.sections):
 print("SECTION",i,"page",s.page_width,s.page_height,"margins",s.top_margin,s.bottom_margin,s.left_margin,s.right_margin)

