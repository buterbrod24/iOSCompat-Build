# Independent typed mutation library

The existing six ownership controls now have a separate-module build path. The native client must import both adapter symbols and pass all six checks in debug and optimized builds. The iOS arm64 library and client must link independently with minimum OS 16.2, no Ts5 imports, and valid ad hoc signatures. The iOS client is not executed by CI. This checks our own public Swift module interface, not ABI equivalence with private Swift runtime symbols. No alias or third-party binary modification is performed. CI and physical device validation remain pending.
