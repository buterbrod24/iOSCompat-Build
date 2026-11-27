# Explicit type registry

An opt-in source-level registry resolves only explicitly registered application types, preserves type identity, rejects conflicting registration and uses a lock for concurrent access. Ten controls exercise registration, type checks, generic identity and concurrent insertion. This is not a mangled-name resolver, runtime metadata constructor, conformance witness adapter, or replacement for any of the five unresolved Swift runtime entrypoints. No binary aliases or system changes. CI and device execution remain unverified.
