import Foundation
import SwiftCoreMutationCompat

private final class Token {}
private final class WeakSlot {
    weak var value: Token?
    init(_ value: Token) { self.value = value }
}

enum MutationChecks {
    static func run() -> [(String, Bool)] {
        let original = Token()
        let added = Token()
        var a: ContiguousArray<AnyObject> = [original]
        let shared = a
        a.ioscompatPrepareAndAppend(added, minimumCapacity: 128)
        var rows = [
            ("capacity", a.capacity >= 128),
            ("order", a.count == 2 && a[0] === original && a[1] === added),
            ("COW", shared.count == 1 && shared[0] === original)
        ]
        for _ in 0..<512 { a.ioscompatAppendReference(added) }
        rows.append(("growth", a.count == 514 && a.dropFirst().allSatisfy { $0 === added }))
        var lifetime = ContiguousArray<AnyObject>()
        var slots = [WeakSlot]()
        for _ in 0..<128 {
            let t = Token()
            slots.append(WeakSlot(t))
            lifetime.ioscompatAppendReference(t)
        }
        rows.append(("retention", slots.allSatisfy { $0.value != nil }))
        lifetime.removeAll()
        rows.append(("release", slots.allSatisfy { $0.value == nil }))
        return rows
    }
}
