import SwiftUI

// Explicit local source-level protocol, never a native protocol replacement.
public protocol CompatCoordinateSpaceProtocol {
    var legacySpace: CoordinateSpace { get }
}
public struct CompatLocalSpace:CompatCoordinateSpaceProtocol {
    public init() {}
    public var legacySpace:CoordinateSpace { .local }
}
public struct CompatGlobalSpace:CompatCoordinateSpaceProtocol {
    public init() {}
    public var legacySpace:CoordinateSpace { .global }
}
public struct CompatNamedSpace:CompatCoordinateSpaceProtocol {
    public let name:AnyHashable
    public init<H:Hashable>(_ name:H) { self.name=AnyHashable(name) }
    public var legacySpace:CoordinateSpace { .named(name) }
}
public extension CompatCoordinateSpaceProtocol where Self == CompatLocalSpace {
    static var local:Self { .init() }
}
public extension CompatCoordinateSpaceProtocol where Self == CompatGlobalSpace {
    static var global:Self { .init() }
}
public extension CompatCoordinateSpaceProtocol where Self == CompatNamedSpace {
    static func named<H:Hashable>(_ name:H) -> Self { .init(name) }
}
public func compatFrame<S:CompatCoordinateSpaceProtocol>(_ proxy:GeometryProxy,_ space:S) -> CGRect {
    proxy.frame(in:space.legacySpace)
}
public func compatAssign<V:View>(_ view:V,_ space:CompatNamedSpace) -> some View {
    view.coordinateSpace(name:space.name)
}
public func compatTap<V:View,S:CompatCoordinateSpaceProtocol>(_ view:V,_ space:S,
                                                               _ action:@escaping(CGPoint)->Void) -> some View {
    view.onTapGesture(count:1,coordinateSpace:space.legacySpace,perform:action)
}
// Owner must supply a name for each scroll container; automatic ancestor lookup is not implemented.
