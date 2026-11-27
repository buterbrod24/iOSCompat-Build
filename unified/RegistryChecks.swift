import Foundation
import Dispatch

private struct UnifiedRegistryBox<T> { let value: T }
enum UnifiedRegistryChecks {
    static func run() -> [(String, Bool)] {
        let r = MetadataRegistry()
        var rows: [(String, Bool)] = []
        rows.append(("register", r.register("int", type: Int.self)))
        rows.append(("idempotent", r.register("int", type: Int.self)))
        rows.append(("reject collision", !r.register("int", type: String.self)))
        rows.append(("preserve original", r.resolve("int", as: Int.self) != nil))
        rows.append(("reject wrong type", r.resolve("int", as: String.self) == nil))
        rows.append(("unknown", r.resolve("missing") == nil))
        rows.append(("empty key", !r.register("", type: Int.self)))
        rows.append(("generic type", r.register("box", type: UnifiedRegistryBox<Int>.self) && r.resolve("box", as: UnifiedRegistryBox<Int>.self) != nil))
        DispatchQueue.concurrentPerform(iterations: 256) { i in
            _ = r.register("slot-\(i)", type: UnifiedRegistryBox<String>.self)
        }
        rows.append(("concurrent insert", (0..<256).allSatisfy { r.resolve("slot-\($0)", as: UnifiedRegistryBox<String>.self) != nil }))
        rows.append(("generic mismatch", r.resolve("box", as: UnifiedRegistryBox<String>.self) == nil))
        return rows
    }
}
