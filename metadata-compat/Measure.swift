import Foundation
import Dispatch

private struct Box<T> { let value: T }
@main struct Measure {
    static func main() {
        let r = MetadataRegistry()
        var rows: [(String, Bool)] = []
        rows.append(("register", r.register("int", type: Int.self)))
        rows.append(("idempotent", r.register("int", type: Int.self)))
        rows.append(("reject collision", !r.register("int", type: String.self)))
        rows.append(("preserve original", r.resolve("int", as: Int.self) != nil))
        rows.append(("reject wrong type", r.resolve("int", as: String.self) == nil))
        rows.append(("unknown", r.resolve("missing") == nil))
        rows.append(("empty key", !r.register("", type: Int.self)))
        rows.append(("generic type", r.register("box", type: Box<Int>.self) && r.resolve("box", as: Box<Int>.self) != nil))
        DispatchQueue.concurrentPerform(iterations: 256) { i in
            _ = r.register("slot-\(i)", type: Box<String>.self)
        }
        rows.append(("concurrent insert", (0..<256).allSatisfy { r.resolve("slot-\($0)", as: Box<String>.self) != nil }))
        rows.append(("generic mismatch", r.resolve("box", as: Box<String>.self) == nil))
        for (name, ok) in rows { print("\(ok ? "PASS" : "FAIL") \(name)") }
        print("TOTAL \(rows.filter { $0.1 }.count)/\(rows.count)")
        if rows.count != 10 || rows.contains(where: { !$0.1 }) { exit(1) }
    }
}
