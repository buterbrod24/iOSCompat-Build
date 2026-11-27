import SwiftUI

@available(iOS 17.0, *)
public func stockCombine<A:Transition,B:Transition>(_ a:A,_ b:B) -> some Transition {
    a.combined(with:b)
}
@available(iOS 17.0, *)
public func stockAnimate<T:Transition>(_ t:T,_ a:Animation?) -> some Transition {
    t.animation(a)
}
@available(iOS 17.0, *)
public func stockErase<T:Transition>(_ t:T) -> AnyTransition { AnyTransition(t) }
@available(iOS 17.0, *)
public func stockPrimitives(_ edge:Edge,_ offset:CGSize) -> (IdentityTransition,OpacityTransition,MoveTransition,OffsetTransition) {
    (IdentityTransition(),OpacityTransition(),MoveTransition(edge:edge),OffsetTransition(offset))
}
