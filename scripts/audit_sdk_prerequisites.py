#!/usr/bin/env python3
"""SDK-only evidence collection. No copied app data or runtime replacement."""
import pathlib,re,sys
sdk=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
patterns={
    "Swift":r'_makeUniqueAndReserveCapacityIfNotUnique|_createNewBuffer|_appendElementAssumeUniqueAndCapacity|_getElementSlowPath|_consumeAndCreateNew|_reserveCapacityAssumingUniqueBuffer|_reserveCapacityImpl|_endMutation',
    "_Concurrency":r'func makeStream|protocol (?:SerialExecutor|Executor)|isSameExclusiveExecutionContext|func enqueue',
    "SwiftUI":r'var topBarLeading|func monospaced\(|func onChange|protocol (?:ShapeStyle|Layout|UIViewRepresentable|UIViewControllerRepresentable)|func _layoutOptions',
}
for module,pattern in patterns.items():
    if module=="SwiftUI":
        root=sdk/"System/Library/Frameworks/SwiftUI.framework/Modules/SwiftUI.swiftmodule"
    else:
        root=sdk/"usr/lib/swift"/(module+".swiftmodule")
    candidates=sorted(root.glob("arm64-apple-ios.swiftinterface"))
    if not candidates:
        candidates=sorted(sdk.glob("**/"+module+".swiftmodule/arm64-apple-ios.swiftinterface"))
    if not candidates:
        print("SDK interface unavailable:",module);continue
    f=candidates[0];lines=f.read_text().splitlines();chosen=set()
    for i,line in enumerate(lines):
        if re.search(pattern,line): chosen.update(range(max(0,i-3),min(len(lines),i+13)))
    evidence="\n".join(f"{i+1}: {lines[i]}" for i in sorted(chosen))
    (out/(module+".txt")).write_text(evidence)
    print(module,"matched evidence lines:",len(chosen))
print("Runtime *2 functions need upstream ABI research; no alias to old versions.")
