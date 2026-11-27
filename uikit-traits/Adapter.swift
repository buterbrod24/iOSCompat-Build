import UIKit

// Original source-level adapter. The owner explicitly forwards UIKit's
// legacy traitCollectionDidChange callback. No global method replacement.
struct CompatTraitSet: OptionSet {
    let rawValue: UInt8
    static let style = Self(rawValue: 1 << 0)
    static let horizontal = Self(rawValue: 1 << 1)
    static let vertical = Self(rawValue: 1 << 2)
    static let contentSize = Self(rawValue: 1 << 3)
    static let scale = Self(rawValue: 1 << 4)
    static let all: Self = [.style,.horizontal,.vertical,.contentSize,.scale]

    static func changed(_ previous: UITraitCollection, _ current: UITraitCollection) -> Self {
        var result: Self = []
        if previous.userInterfaceStyle != current.userInterfaceStyle { result.insert(.style) }
        if previous.horizontalSizeClass != current.horizontalSizeClass { result.insert(.horizontal) }
        if previous.verticalSizeClass != current.verticalSizeClass { result.insert(.vertical) }
        if previous.preferredContentSizeCategory != current.preferredContentSizeCategory { result.insert(.contentSize) }
        if previous.displayScale != current.displayScale { result.insert(.scale) }
        return result
    }
}

@MainActor
final class CompatTraitObserver {
    struct Token: Hashable { fileprivate let id: UUID }
    private struct Entry {
        let interests: CompatTraitSet
        let handler: (UITraitCollection,UITraitCollection) -> Void
    }
    private var entries: [Token:Entry] = [:]
    private var order: [Token] = []
    private var pending: [(UITraitCollection,UITraitCollection)] = []
    private var delivering = false

    func register(_ interests: CompatTraitSet, handler: @escaping (UITraitCollection,UITraitCollection) -> Void) -> Token {
        let token = Token(id: UUID())
        entries[token] = Entry(interests: interests, handler: handler)
        order.append(token)
        return token
    }
    func unregister(_ token: Token) {
        entries.removeValue(forKey: token)
        order.removeAll { $0 == token }
    }
    func receive(previous: UITraitCollection?, current: UITraitCollection) {
        guard let previous else { return }
        pending.append((previous,current))
        guard !delivering else { return }
        delivering = true
        defer { delivering = false }
        while !pending.isEmpty {
            let (old,new) = pending.removeFirst()
            let changed = CompatTraitSet.changed(old,new)
            let snapshot = order
            for token in snapshot {
                guard let entry=entries[token], !entry.interests.intersection(changed).isEmpty else { continue }
                entry.handler(old,new)
            }
        }
    }
}

// Explicit opt-in view for clients whose source we control.
@MainActor
class CompatTraitView: UIView {
    let compatTraits = CompatTraitObserver()
    override func traitCollectionDidChange(_ previousTraitCollection: UITraitCollection?) {
        super.traitCollectionDidChange(previousTraitCollection)
        compatTraits.receive(previous: previousTraitCollection, current: traitCollection)
    }
}
