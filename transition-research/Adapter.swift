import SwiftUI

// Explicit source-level subset built entirely on legacy AnyTransition.
// No claim of native Transition conformance, type layout or ABI identity.
public struct CompatTransition {
    public let legacy: AnyTransition
    private init(_ legacy: AnyTransition) { self.legacy=legacy }

    public static var identity: Self { .init(.identity) }
    public static var opacity: Self { .init(.opacity) }
    public static func move(edge:Edge) -> Self { .init(.move(edge:edge)) }
    public static func offset(_ offset:CGSize) -> Self { .init(.offset(offset)) }
    public func combined(with other:Self) -> Self { .init(legacy.combined(with:other.legacy)) }
    public func animation(_ animation:Animation?) -> Self { .init(legacy.animation(animation)) }
    public static func asymmetric(insertion:Self,removal:Self) -> Self {
        .init(.asymmetric(insertion:insertion.legacy,removal:removal.legacy))
    }
}
public extension View {
    func compatTransition(_ value:CompatTransition) -> some View {
        transition(value.legacy)
    }
}
