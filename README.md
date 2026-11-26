# iOSCompat-Build

Standalone experimental compatibility research for older iOS releases.
This repository builds original compatibility code against the installed Apple SDK.

## AppIntents callable candidate

Two experimental callable ABI adapters targeting arm64 iOS 16.2:
- AppShortcut initializer forwarding to the older public initializer.
- Default discoverability getter reproducing the measured default behavior.

The workflow checks Python syntax, compares compiler-generated LLVM IR signatures, links the candidate, verifies exact exported symbols and the deployment target, and applies an ad hoc signature.

No protocol descriptor aliases are implemented. A successful build is not proof of runtime compatibility. Device tests are required before integration.

No third-party application binaries, extracted frameworks, device reports, private project files, or credentials are included. No system libraries are modified.
