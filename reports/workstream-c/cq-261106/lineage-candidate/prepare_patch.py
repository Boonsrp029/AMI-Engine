"""Write a reviewable unapplied patch; never edit frozen runtime source."""
import difflib
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    candidate = (ROOT/"lineage_candidate.py").read_text(encoding="utf-8")
    helper = candidate.split("\n\nclass QualificationLedger(CurrentLedger):",1)[0]+"\n"
    helper = helper.replace('"""Isolated CQ1 admission candidate. Not imported by the application runtime."""',
                            '"""Verify exact development contract/start/result provenance before CQ1."""')
    helper = helper.replace("from src.pilot.subtasks.qualification_phase import QualificationLedger as CurrentLedger\n","")
    source = Path("src/pilot/subtasks/qualification_phase.py")
    original = source.read_text(encoding="utf-8")
    imports = "from .quality_review import SourceReview, summarize\n"
    assert original.count(imports)==1
    proposed = original.replace(imports,imports+"from ._development_lineage import verify_lineage\n")
    anchor = "\n    def _records(self, ids):"
    assert proposed.count(anchor)==1
    proposed = proposed.replace(anchor,"\n        verify_lineage(c)\n"+anchor)
    for name,text in (("proposed_development_lineage.py",helper),("proposed_qualification_phase.py",proposed)):
        with (ROOT/name).open("x",encoding="utf-8",newline="\n") as stream:
            stream.write(text)
    patch = "".join(difflib.unified_diff([],helper.splitlines(keepends=True),
        fromfile="/dev/null",tofile="b/src/pilot/subtasks/_development_lineage.py"))
    patch += "".join(difflib.unified_diff(original.splitlines(keepends=True),proposed.splitlines(keepends=True),
        fromfile="a/src/pilot/subtasks/qualification_phase.py",tofile="b/src/pilot/subtasks/qualification_phase.py"))
    with (ROOT/"integration.patch").open("x",encoding="utf-8",newline="\n") as stream:
        stream.write(patch)
    manifest = {"live_phase_unchanged_sha256":sha(source),"integration_state":"unapplied offline candidate",
        "sha256":{name:sha(ROOT/name) for name in ("lineage_candidate.py","proposed_development_lineage.py",
                    "proposed_qualification_phase.py","integration.patch")}}
    with (ROOT/"manifest.json").open("x",encoding="utf-8") as stream:
        json.dump(manifest,stream,indent=2);stream.write("\n")
    print(json.dumps(manifest))


if __name__=="__main__":
    main()
