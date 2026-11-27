import Foundation

// Independent scalar timeline; not the SwiftUI Keyframes ABI.
public enum CompatScalarFrame {
    case move(Double)
    case linear(Double, duration:Double)
    case cubic(Double, duration:Double, startVelocity:Double, endVelocity:Double)
}

public struct CompatScalarTimeline {
    public let initial:Double
    public let frames:[CompatScalarFrame]
    public let duration:Double

    public init?(initial:Double, frames:[CompatScalarFrame]) {
        guard initial.isFinite, frames.count<=10000 else { return nil }
        var total=0.0
        for frame in frames {
            switch frame {
            case .move(let v):
                guard v.isFinite else { return nil }
            case .linear(let v,let d):
                guard v.isFinite,d.isFinite,d>0 else { return nil }
                total+=d
            case .cubic(let v,let d,let a,let b):
                guard v.isFinite,d.isFinite,d>0,a.isFinite,b.isFinite,
                      (a*d).isFinite,(b*d).isFinite else { return nil }
                total+=d
            }
            guard total.isFinite else { return nil }
        }
        self.initial=initial;self.frames=frames;self.duration=total
    }

    public func value(at time:Double) -> Double? {
        guard time.isFinite else { return nil }
        var t=max(0,min(time,duration))
        var previous=initial
        for frame in frames {
            switch frame {
            case .move(let next): previous=next
            case .linear(let next,let d):
                if t<d {
                    let u=t/d
                    let v=(1-u)*previous+u*next
                    return v.isFinite ? v : nil
                }
                t-=d;previous=next
            case .cubic(let next,let d,let a,let b):
                if t<d {
                    let u=t/d, u2=u*u, u3=u2*u
                    let p0=(2*u3-3*u2+1)*previous
                    let p1=(u3-2*u2+u)*d*a
                    let p2=(-2*u3+3*u2)*next
                    let p3=(u3-u2)*d*b
                    let v=p0+p1+p2+p3
                    return v.isFinite ? v : nil
                }
                t-=d;previous=next
            }
        }
        return previous
    }
}

// Multiple explicit writable-key-path tracks evaluated at the same time.
public struct CompatTimeline<Value> {
    private let initial:Value
    private var tracks:[(duration:Double,apply:(inout Value,Double)->Bool)]=[]
    private var keys=Set<AnyKeyPath>()
    public init(initial:Value) { self.initial=initial }
    public var duration:Double { tracks.map{$0.duration}.max() ?? 0 }
    @discardableResult
    public mutating func add(_ path:WritableKeyPath<Value,Double>, frames:[CompatScalarFrame]) -> Bool {
        guard !keys.contains(path), tracks.count<128,
              let track=CompatScalarTimeline(initial:initial[keyPath:path],frames:frames) else { return false }
        keys.insert(path)
        tracks.append((track.duration,{ value,time in
            guard let sample=track.value(at:time) else { return false }
            value[keyPath:path]=sample
            return true
        }))
        return true
    }
    public func value(at time:Double) -> Value? {
        guard time.isFinite else { return nil }
        var result=initial
        for track in tracks { if !track.apply(&result,time) { return nil } }
        return result
    }
}
