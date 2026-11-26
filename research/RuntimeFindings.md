# Runtime findings

The upstream Swift 5.7 and 5.9 RuntimeFunctions.def macros have their exported symbol in argument 2 (one-based). The earlier parser assumed argument 3.

The five new entry points have matching declared argument and return types with their predecessors, but availability changes to SignedDescriptorAvailability or SignedConformsToProtocolAvailability. In Swift 5.9 MetadataLookup.cpp, the new context and opaque descriptor entry points authenticate the descriptor before passing it to the common implementation. The legacy entries have different input contracts.

Status: research only. No aliases, pointer authentication bypass, runtime replacement or system changes. A declaration match cannot establish compatibility.

Sources:
- https://github.com/swiftlang/swift/blob/swift-5.7-RELEASE/include/swift/Runtime/RuntimeFunctions.def
- https://github.com/swiftlang/swift/blob/swift-5.9-RELEASE/include/swift/Runtime/RuntimeFunctions.def
- https://github.com/swiftlang/swift/blob/swift-5.9-RELEASE/stdlib/public/runtime/MetadataLookup.cpp
