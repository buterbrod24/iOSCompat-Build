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

## Unified Probe 0.2.0
Device report on iOS 16.2: 24/24 completed, 20 PASS, four read-only evidence groups, zero failed or interrupted. Six independent SDK stream subchecks passed; the rebound toolbar getter constructed a hosting controller and completed layout. Ten source-level change-state subchecks passed. This does not establish SwiftUI visual equivalence, opaque modifier ABI compatibility or runtime descriptor compatibility. No raw device report is published.

## Independent Activity Probe 0.1.0
User-reported physical iOS 16.2 device test of build `b4f30fe`: all six local protocol checks passed (6/6), including inherited generic dispatch, native SystemIntent dispatch, positive and negative casts, native SystemIntent conformance and perform(). Earlier simulator comparison passed 10/10; independent descriptor exports passed the ABI build gate. The local protocol has a distinct nominal identity: these results do not establish native LiveActivityIntent substitution, third-party application compatibility or system registration. No raw device report or screenshot is published.

## Unified Probe 0.4.0
User-reported physical iOS 16.2 test of build `ae12468`: 35/35 completed, 31 PASS, four read-only evidence groups, zero failures or interruptions. Independent reserve (12/12), stream (6/6), source-level change state (10/10), paired toolbar construction and local activity protocol (6/6) passed. Native LiveActivityIntent and five newer Swift runtime entry points remain absent. No native protocol substitution, visual equivalence, or third-party application compatibility is established. No raw device report is published.


### Unified Probe 0.6.0 physical device validation

User-supplied device report: iOS 16.2 (20C65), completed 42/42, PASS 38, EVIDENCE 4, FAIL 0, INTERRUPTED 0. All four executor source-level controls and three native runtime baseline controls passed. Previously tested callable, stream, reserve, toolbar and independent activity controls also passed. Five newer Swift runtime exports remain absent. No claim of native newer executor ABI, protocol identity, or third-party application compatibility. Only aggregate results are published; raw device report is not included.
