# Contextual reference compiler fixture

Original generic types and conditional conformance generate compiler-owned symbolic references. Six host controls check public language semantics. The same source is compiled for iOS 16.2 and 17.0; bounded typeref framing and import inventories are retained for comparison. Deployment targets are not compiler versions: this experiment does not isolate Swift 5.7 versus 5.9 code generation. No reference payload is dereferenced, no private runtime is called, and no ABI replacement is claimed. CI pending.
