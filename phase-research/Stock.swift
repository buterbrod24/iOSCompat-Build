import SwiftUI

@available(iOS 17.0, *)
public func stockPhase(_ trigger:Int) -> some View {
    PhaseAnimator([0,1,2],trigger:trigger) { phase in
        Text("Phase").opacity(phase==0 ? 1 : 0.5)
    } animation: { _ in .linear(duration:0.2) }
}
@available(iOS 17.0, *)
public func stockCompletion(_ body:()->Void,_ completion:@escaping()->Void) {
    withAnimation(.linear(duration:0.2),completionCriteria:.logicallyComplete,body,completion:completion)
}
@available(iOS 17.0, *)
public func stockTransaction(_ completion:@escaping()->Void) -> Transaction {
    var t=Transaction(animation:.default)
    t.addAnimationCompletion(criteria:.removed,completion)
    return t
}
