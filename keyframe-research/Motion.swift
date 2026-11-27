import Foundation

// An explicit independent velocity-continuous timeline. Springs end at their
// physically sampled state, not a forced target. No Apple ABI or timing claim.
public struct CompatMotionState {
    public let value:Double
    public let velocity:Double
}
public enum CompatMotionFrame {
    case move(Double)
    case spring(target:Double,duration:Double,model:CompatSpring)
    case cubic(target:Double,duration:Double,endVelocity:Double)
}
public struct CompatMotionTimeline {
    private struct Segment {
        let start:Double
        let duration:Double
        let sample:(Double)->CompatMotionState?
    }
    private let segments:[Segment]
    private let final:CompatMotionState
    public let duration:Double

    public init?(initial:Double,velocity:Double=0,frames:[CompatMotionFrame]) {
        guard initial.isFinite,velocity.isFinite,frames.count<=10000 else { return nil }
        var state=CompatMotionState(value:initial,velocity:velocity)
        var time=0.0
        var built:[Segment]=[]
        for frame in frames {
            let from=state
            let length:Double
            let evaluator:(Double)->CompatMotionState?
            switch frame {
            case .move(let next):
                guard next.isFinite else { return nil }
                state=CompatMotionState(value:next,velocity:0)
                continue
            case .spring(let target,let d,let model):
                guard target.isFinite,d.isFinite,d>0 else { return nil }
                length=d
                evaluator={ t in
                    guard let s=model.sample(from:from.value,to:target,velocity:from.velocity,time:t) else { return nil }
                    return CompatMotionState(value:s.value,velocity:s.velocity)
                }
            case .cubic(let target,let d,let end):
                guard target.isFinite,d.isFinite,d>0,end.isFinite else { return nil }
                length=d
                evaluator={ t in
                    let u=t/d,u2=u*u,u3=u2*u
                    let p0=(2*u3-3*u2+1)*from.value
                    let p1=(u3-2*u2+u)*d*from.velocity
                    let p2=(-2*u3+3*u2)*target
                    let p3=(u3-u2)*d*end
                    let v=p0+p1+p2+p3
                    let s0=(6*u2-6*u)*from.value/d
                    let s1=(3*u2-4*u+1)*from.velocity
                    let s2=(-6*u2+6*u)*target/d
                    let s3=(3*u2-2*u)*end
                    let speed=s0+s1+s2+s3
                    guard v.isFinite,speed.isFinite else { return nil }
                    return CompatMotionState(value:v,velocity:speed)
                }
            }
            guard (time+length).isFinite,time+length>time,let endpoint=evaluator(length) else { return nil }
            built.append(Segment(start:time,duration:length,sample:evaluator))
            time+=length
            state=endpoint
        }
        segments=built;final=state;duration=time
    }
    public func sample(at time:Double)->CompatMotionState? {
        guard time.isFinite else { return nil }
        let t=max(0,min(time,duration))
        // Right-continuous boundaries: immediate moves reset velocity.
        for segment in segments where t<segment.start+segment.duration {
            return segment.sample(t-segment.start)
        }
        return final
    }
}
