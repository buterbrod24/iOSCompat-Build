# Independent opaque metadata client

The existing ten source-level tests now run against an independently compiled resilient module rather than a single compilation unit. Host optimized and unoptimized execution is configured. ARM64 clients and libraries targeting iOS 16.2 and 17.0 are compiled separately; runtime imports are inventoried and compared. The deployment target comparison does not isolate different Swift compiler releases. No private runtime call or ABI alias is introduced. CI and physical device execution remain unverified.
