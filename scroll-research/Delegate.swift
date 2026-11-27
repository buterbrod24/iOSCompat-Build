import UIKit

// Only for an explicitly owned scroll view. Does not replace another delegate.
@MainActor
final class CompatScrollSnapDelegate:NSObject,UIScrollViewDelegate {
    enum Axis { case horizontal, vertical }
    let axis:Axis
    var leadingOffsets:[CompatSnapTargets.Target]=[]
    var limit:Int?
    private(set) var lastTarget:Int?
    init(axis:Axis) { self.axis=axis }
    func scrollViewWillEndDragging(_ scrollView:UIScrollView,withVelocity velocity:CGPoint,targetContentOffset:UnsafeMutablePointer<CGPoint>) {
        let horizontal=axis == .horizontal
        let inset=scrollView.adjustedContentInset
        let minimum=Double(horizontal ? -inset.left : -inset.top)
        let maximum=max(minimum,Double(horizontal
            ? scrollView.contentSize.width-scrollView.bounds.width+inset.right
            : scrollView.contentSize.height-scrollView.bounds.height+inset.bottom))
        guard let targets=CompatSnapTargets(targets:leadingOffsets,minimum:minimum,maximum:maximum),
              let target=targets.snap(current:Double(horizontal ? scrollView.contentOffset.x : scrollView.contentOffset.y),
                                      proposed:Double(horizontal ? targetContentOffset.pointee.x : targetContentOffset.pointee.y),
                                      velocity:Double(horizontal ? velocity.x : velocity.y),limit:limit) else { lastTarget=nil;return }
        if horizontal { targetContentOffset.pointee.x=CGFloat(target.offset) }
        else { targetContentOffset.pointee.y=CGFloat(target.offset) }
        lastTarget=target.id
    }
}
