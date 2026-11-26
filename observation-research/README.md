# Observation back-deployment research

Pinned upstream Swift 5.9 release commit ea95594ae137f288bf29a0b489b8689680a0086a. Source headers and upstream license are retained in the temporary build directory; no upstream source is vendored in the repository. The upstream registrar and tracking code are compiled with adjusted availability and an independently implemented platform lock and thread-local storage. The macro declarations are excluded, since runtime behavior rather than macro expansion is under investigation.

The module is named Observation for compiler-generated symbol comparison, but uses an isolated install name libObservationResearch.dylib. The gate checks eight public ABI names, deployment target and absence of a dependency on the native Observation dylib. This is a build experiment only: matching exports cannot establish layout, protocol identity or behavioral compatibility, and the original Swift 5.9 implementation requires separate concurrency and lifetime validation. No system libraries, app binaries, or security mechanisms are modified. The device probe is built only after the simulator gate; it loads the isolated candidate explicitly and reports eight functional controls. The app includes the upstream license and modification notice.

Related source-level backport: https://github.com/pointfreeco/swift-perception (not incorporated).

Recorded simulator result: 8/8 PASS; full device probe packaging and archive check succeeded in run 45904429563, commit e168802cefe5b0f47047288fa02c444a461b6978. Artifact 15158036218. Physical iOS 16.2 report is still required. Separate callable IR audit compares five lowered function signatures against the original SDK; no client or system binary is patched, and no raw SDK IR is distributed.
