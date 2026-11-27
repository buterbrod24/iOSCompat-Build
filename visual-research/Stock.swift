import SwiftUI

@available(iOS 17.0, *)
@MainActor
public func stockVisual<V:View>(_ view:V)->some View {
    view.visualEffect { effect, proxy in
        effect.scaleEffect(0.9).offset(x:proxy.size.width*0.1,y:0)
    }
}
@available(iOS 17.0, *)
@MainActor
public func stockScroll<V:View>(_ view:V)->some View {
    view.scrollTransition(.interactive,axis:.vertical) { effect,phase in
        effect.scaleEffect(phase.isIdentity ? 1 : 0.8)
    }
}
