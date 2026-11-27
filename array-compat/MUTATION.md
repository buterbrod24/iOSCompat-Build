# Reference-array source adapters

Two typed public-API adapters provide append and combined reserve/append semantics for ContiguousArray<AnyObject>. Six controls cover capacity, ordering, COW, growth, retention and release. CI compares optimized and unoptimized native execution and checks the iOS 16.2 build for newer specialized imports. This is not a replacement for _appendElementAssumeUniqueAndCapacity or other private mutation contracts. No aliases, binary rewriting, or private buffer assumptions are introduced. Physical iOS execution and CI results are pending.
