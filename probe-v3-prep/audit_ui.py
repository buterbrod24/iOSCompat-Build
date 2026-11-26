#!/usr/bin/env python3
"""Inspect declarations in public SwiftUI and SwiftUICore SDK interfaces."""
import json,pathlib,re,sys

sdk=pathlib.Path(sys.argv[1])
targets={
"Text.monospaced":("Text",r'\bfunc monospaced\b'),
"Text.bold":("Text",r'\bfunc bold\b'),
"Text.italic":("Text",r'\bfunc italic\b'),
"Text.foregroundStyle":("Text",r'\bfunc foregroundStyle\b'),
"Font.monospaced":("Font",r'\bfunc monospaced\b'),
"ContentTransition.numericText":("ContentTransition",r'\bfunc numericText\b'),
"AccessibilityTraits.isToggle":("AccessibilityTraits",r'\b(?:let|var) isToggle\b'),
"ToolbarItemPlacement.topBarTrailing":("ToolbarItemPlacement",r'\b(?:let|var) topBarTrailing\b'),
"View.onChange":("View",r'\bfunc onChange\b'),
}
result={k:[] for k in targets}
for module in ("SwiftUI","SwiftUICore"):
    files=list(sdk.glob(f"System/Library/Frameworks/{module}.framework/Modules/{module}.swiftmodule/arm64-apple-ios.swiftinterface"))
    print(module,"public interface files",len(files))
    for f in files:
        lines=f.read_text().splitlines()
        owner=None
        for i,line in enumerate(lines):
            # Top-level public SDK declarations have indented members.
            if line and not line[0].isspace():
                m=re.search(r'\b(?:extension|struct|class|enum|protocol)\s+(?:SwiftUI(?:Core)?\.)?([A-Za-z_]\w*)\b',line)
                if m:owner=m[1]
                elif line.startswith("}"):owner=None
            for key,(expected,pat) in targets.items():
                if owner!=expected or not re.search(pat,line):continue
                attrs=[]
                for prev in reversed(lines[max(0,i-10):i]):
                    if prev.strip().startswith("@"):attrs.append(prev.strip())
                    elif not prev.strip() or prev.strip().startswith("//"):continue
                    else:break
                decl=line.strip().split("{")[0]
                result[key].append({"module":module,"line":i+1,"declaration":decl,
                    "availability":[a for a in reversed(attrs) if a.startswith(("@available","@backDeployed","@_backDeploy"))]})
for name,rows in result.items():
    print(name,len(rows),"matching declarations")
    for row in rows:
        print(" ",row["module"],row["declaration"]," ".join(row["availability"]))
pathlib.Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+"\n")
if not result["ToolbarItemPlacement.topBarTrailing"]:raise SystemExit("positive control missing")
