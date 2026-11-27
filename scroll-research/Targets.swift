import Foundation

// Independent single-axis snap policy, not Apple's ScrollTargetBehavior ABI.
// Inputs are explicit leading offsets in the owner's content coordinate space.
struct CompatSnapTargets {
    struct Target:Equatable {
        let id:Int
        let offset:Double
    }
    let targets:[Target]
    let minimum:Double
    let maximum:Double
    init?(targets:[Target],minimum:Double,maximum:Double) {
        guard minimum.isFinite,maximum.isFinite,minimum<=maximum,
              !targets.isEmpty,targets.count<=10000,
              targets.allSatisfy({$0.offset.isFinite}),
              Set(targets.map{$0.id}).count==targets.count else { return nil }
        self.minimum=minimum;self.maximum=maximum
        self.targets=targets.map{Target(id:$0.id,offset:max(minimum,min(maximum,$0.offset)))}
            .sorted { $0.offset == $1.offset ? $0.id<$1.id : $0.offset<$1.offset }
    }
    // Nearest proposed target; ties prefer the direction of travel.
    // An optional explicit index limit constrains travel from the current target.
    func snap(current:Double,proposed:Double,velocity:Double,limit:Int?=nil)->Target? {
        guard current.isFinite,proposed.isFinite,velocity.isFinite,
              limit.map({$0>=0}) ?? true else { return nil }
        let p=max(minimum,min(maximum,proposed))
        let c=max(minimum,min(maximum,current))
        func nearest(_ offset:Double)->Int {
            var low=0,high=targets.count
            while low<high {
                let mid=low+(high-low)/2
                if targets[mid].offset<offset { low=mid+1 } else { high=mid }
            }
            if low==0 { return 0 }
            if low==targets.count { return low-1 }
            let left=offset-targets[low-1].offset,right=targets[low].offset-offset
            if left==right { return velocity>0 ? low : low-1 }
            return left<right ? low-1 : low
        }
        let dest=nearest(p)
        guard let limit else { return targets[dest] }
        let origin=nearest(c)
        let bound=min(limit,targets.count-1)
        return targets[max(max(0,origin-bound),min(min(targets.count-1,origin+bound),dest))]
    }
}
