#!/usr/bin/env python3
"""Report availability and back-deployment attributes, not SDK source bodies."""
import json,pathlib,re,sys
sdk=pathlib.Path(sys.argv[1])
files=list(sdk.glob("System/Library/Frameworks/SwiftUI.framework/Modules/SwiftUI.swiftmodule/arm64-apple-ios.swiftinterface"))
if len(files)!=1: raise SystemExit("Expected one public SwiftUI interface")
lines=files[0].read_text().splitlines()
targets={
"Text.monospaced":r'\bfunc monospaced\(',
"Text.foregroundStyle":r'\bfunc foregroundStyle\b',
"ContentTransition.numericText":r'\bfunc numericText\(',
"ToolbarItemPlacement.topBarLeading":r'\b(?:let|var) topBarLeading\b',
"PresentationAdaptation":r'\bstruct PresentationAdaptation\b',
"ScrollBounceBehavior":r'\bstruct ScrollBounceBehavior\b',
"View.presentationCompactAdaptation":r'\bfunc presentationCompactAdaptation\b',
"View.presentationBackground":r'\bfunc presentationBackground\b',
"View.onChange":r'\bfunc onChange\b',
"UIHostingController.safeAreaRegions":r'\bvar safeAreaRegions\b',
"View.scrollBounceBehavior":r'\bfunc scrollBounceBehavior\b',
"View.scrollClipDisabled":r'\bfunc scrollClipDisabled\b',
"View.defaultScrollAnchor":r'\bfunc defaultScrollAnchor\b',
"AccessibilityTraits.isToggle":r'\b(?:let|var) isToggle\b',
}
results={}
for name,pattern in targets.items():
    matches=[]
    for i,line in enumerate(lines):
        if not re.search(pattern,line):continue
        attrs=[]
        for j in range(i-1,max(-1,i-12),-1):
            t=lines[j].strip()
            if t.startswith("@"):
                attrs.append(t)
            elif t.startswith("//") or not t:continue
            else:break
        attrs.reverse()
        decl=line.strip().split("{")[0]
        # Only the declaration and compiler attributes are evidence, not implementation.
        matches.append({"line":i+1,"declaration":decl,
            "availability":[x for x in attrs if x.startswith(("@available","@backDeployed","@_backDeploy"))]})
    results[name]=matches
    print(name,len(matches),"declarations",sum(any("backDeploy" in a for a in m["availability"]) for m in matches),"back-deployed")
pathlib.Path(sys.argv[2]).write_text(json.dumps(results,indent=2)+"\n")
if not results["ToolbarItemPlacement.topBarLeading"]:raise SystemExit("Positive-control SDK declaration missing")
