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

## Callable probe 0.2.0
The earlier independent probe completed all six checks on an iOS 16.2 device, including construction of a stock SDK AppShortcut. Default getter was only resolved. Version 0.2.0 adds concrete static calls to the default getter and an explicit false implementation, with an LLVM IR gate requiring the real original SDK default symbol. No generic protocol witness dispatch is claimed. No device report or identifying data is published.
