import CoreGraphics

// Ordered, axis-aligned affine operations on an explicitly supplied layout size.
// No native VisualEffect conformance or internal layout observation.
public struct CompatVisualTransform {
    public private(set) var matrix=CGAffineTransform.identity
    public private(set) var opacity:Double=1

    public init() {}
    public func offset(x:CGFloat,y:CGFloat)->Self? {
        guard x.isFinite,y.isFinite else { return nil }
        var result=self
        result.matrix.tx += x
        result.matrix.ty += y
        return result.valid ? result : nil
    }
    public func scale(_ factor:CGFloat,anchor:CGPoint,size:CGSize)->Self? {
        guard factor.isFinite,anchor.x.isFinite,anchor.y.isFinite,
              size.width.isFinite,size.height.isFinite,size.width>=0,size.height>=0 else { return nil }
        let x=anchor.x*size.width,y=anchor.y*size.height
        var result=self
        result.matrix.a *= factor
        result.matrix.d *= factor
        result.matrix.tx = matrix.tx*factor+x*(1-factor)
        result.matrix.ty = matrix.ty*factor+y*(1-factor)
        return result.valid ? result : nil
    }
    public func faded(_ factor:Double)->Self? {
        guard factor.isFinite,(0...1).contains(factor) else { return nil }
        var result=self
        result.opacity *= factor
        return result
    }
    private var valid:Bool {
        [matrix.a,matrix.d,matrix.tx,matrix.ty].allSatisfy{$0.isFinite}
    }
}
enum CompatScrollPhase:Equatable {
    case leading, identity, trailing
    var value:Double { self == .leading ? -1 : self == .trailing ? 1 : 0 }
}
struct CompatScrollSample {
    let phase:CompatScrollPhase
    let visibleFraction:Double
    // Independent continuous fraction, not Apple's discrete phase.value.
    var progress:Double { phase.value*(1-visibleFraction) }
    static func sample(item:ClosedRange<Double>,viewport:ClosedRange<Double>,reversed:Bool=false)->Self? {
        let a=item.lowerBound,b=item.upperBound,c=viewport.lowerBound,d=viewport.upperBound
        guard [a,b,c,d].allSatisfy({$0.isFinite}),b>a,d>c,
              (b-a).isFinite,(d-c).isFinite else { return nil }
        let overlap=max(0,min(b,d)-max(a,c))
        let visible=min(1,overlap/min(b-a,d-c))
        if visible==1 { return Self(phase:.identity,visibleFraction:1) }
        let before=(a+(b-a)/2)<(c+(d-c)/2)
        return Self(phase: before != reversed ? .leading : .trailing,visibleFraction:visible)
    }
}
