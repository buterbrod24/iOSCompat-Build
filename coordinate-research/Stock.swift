import SwiftUI

@available(iOS 17.0, *)
public func stockFrame<S: CoordinateSpaceProtocol>(_ proxy: GeometryProxy, _ space:S) -> CGRect {
    proxy.frame(in: space)
}
@available(iOS 17.0, *)
public func stockLocal() -> LocalCoordinateSpace { .local }
@available(iOS 17.0, *)
public func stockGlobal() -> GlobalCoordinateSpace { .global }
@available(iOS 17.0, *)
public func stockNamed(_ name:String) -> NamedCoordinateSpace { .named(name) }
@available(iOS 17.0, *)
public func stockScroll() -> NamedCoordinateSpace { .scrollView }
@available(iOS 17.0, *)
public func stockAssign<V:View>(_ view:V,_ space:NamedCoordinateSpace) -> some View {
    view.coordinateSpace(space)
}
@available(iOS 17.0, *)
public func stockTap<V:View,S:CoordinateSpaceProtocol>(_ view:V,_ space:S,
                                                        _ action:@escaping (CGPoint)->Void) -> some View {
    view.onTapGesture(count:1,coordinateSpace:space,perform:action)
}
