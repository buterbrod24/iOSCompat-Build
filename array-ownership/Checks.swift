import Foundation

private final class Token: NSObject {
    let value: Int
    init(_ value: Int) { self.value = value }
}
private final class WeakSlot {
    weak var token: Token?
    init(_ token: Token) { self.token = token }
}

enum ArrayOwnershipChecks {
    static func run() -> [(String, Bool)] {
        var rows: [(String, Bool)] = []
        let tokens = (0..<256).map(Token.init)
        var a = [AnyObject]()
        var b = ContiguousArray<AnyObject>()
        for t in tokens { a.append(t); b.append(t) }
        rows.append(("Array growth and order", a.count == tokens.count && zip(a,tokens).allSatisfy { $0.0 === $0.1 }))
        rows.append(("ContiguousArray growth and order", b.count == tokens.count && zip(b,tokens).allSatisfy { $0.0 === $0.1 }))
        let originalA = a
        let originalB = b
        let replacement = Token(-1)
        a[0] = replacement
        b[0] = replacement
        a.append(replacement)
        b.append(replacement)
        rows.append(("Array copy-on-write", originalA.count == 256 && originalA[0] === tokens[0] && a.count == 257 && a[0] === replacement))
        rows.append(("ContiguousArray copy-on-write", originalB.count == 256 && originalB[0] === tokens[0] && b.count == 257 && b[0] === replacement))
        b.ioscompatReserveCapacity(4096)
        rows.append(("Validated reserve after shared mutation", b.capacity >= 4096 && b.count == 257 && b[256] === replacement))
        let bridged = NSArray(array: tokens)
        var bridge = bridged as [AnyObject]
        rows.append(("NSArray bridge preserves identities", bridge.count == 256 && zip(bridge,tokens).allSatisfy { $0.0 === $0.1 }))
        bridge[0] = replacement
        bridge.append(replacement)
        rows.append(("Bridged Array mutation isolates source", (bridged[0] as AnyObject) === tokens[0] && bridged.count == 256 && bridge.count == 257))
        let c = ContiguousArray(bridge)
        rows.append(("Contiguous copy from bridged Array", c.count == 257 && c[0] === replacement && c[256] === replacement))
        var slots = [WeakSlot]()
        var lifetime = ContiguousArray<AnyObject>()
        autoreleasepool {
            for i in 0..<512 {
                let t = Token(i)
                slots.append(WeakSlot(t))
                lifetime.append(t)
            }
        }
        lifetime.ioscompatReserveCapacity(8192)
        rows.append(("512 references survive capacity growth", slots.allSatisfy { $0.token != nil }))
        var shared = lifetime
        lifetime.removeAll(keepingCapacity: true)
        rows.append(("Shared storage retains objects", lifetime.isEmpty && shared.count == 512 && slots.allSatisfy { $0.token != nil }))
        shared.removeAll()
        rows.append(("All released after last owner", slots.allSatisfy { $0.token == nil }))
        var repeatedOK = true
        for round in 0..<128 {
            autoreleasepool {
                var x: ContiguousArray<AnyObject> = [tokens[round]]
                let y = x
                x.ioscompatReserveCapacity(64 + round)
                x.append(replacement)
                if y.count != 1 || y[0] !== tokens[round] || x.count != 2 || x[1] !== replacement {
                    repeatedOK = false
                }
            }
        }
        rows.append(("128 repeated reserve and COW cycles", repeatedOK))
        return rows
    }
}
