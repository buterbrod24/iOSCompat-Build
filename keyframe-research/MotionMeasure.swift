import Foundation

@main struct MotionMeasure {
    static func main() {
        let spring=CompatSpring(mass:1,stiffness:4,damping:1)!
        let a=CompatMotionTimeline(initial:0,velocity:0.3,frames:[
            .spring(target:1,duration:0.7,model:spring),
            .cubic(target:2,duration:1,endVelocity:0)])!
        func near(_ x:Double,_ y:Double,_ e:Double=1e-6)->Bool { abs(x-y)<e }
        let left=a.sample(at:0.7-1e-8)!,join=a.sample(at:0.7)!,right=a.sample(at:0.7+1e-8)!
        let physical=spring.sample(from:0,to:1,velocity:0.3,time:0.7)!
        let b=CompatMotionTimeline(initial:0,frames:[.cubic(target:1,duration:1,endVelocity:2),
            .spring(target:3,duration:0.6,model:spring)])!
        let c=CompatMotionTimeline(initial:0,frames:[.cubic(target:1,duration:1,endVelocity:2),
            .move(5),.cubic(target:6,duration:1,endVelocity:0)])!
        let rows:[(String,Bool)]=[
            ("spring endpoint not forcibly snapped",near(join.value,physical.value)),
            ("spring velocity passed to cubic",near(join.velocity,physical.velocity)),
            ("position continuous across spring cubic boundary",near(left.value,right.value)),
            ("velocity continuous across spring cubic boundary",near(left.velocity,right.velocity)),
            ("cubic velocity passed to spring",near(b.sample(at:1)!.velocity,2)),
            ("cubic ends at requested value",near(a.sample(at:1.7)!.value,2)),
            ("cubic end velocity",near(a.sample(at:1.7)!.velocity,0)),
            ("move resets velocity",near(c.sample(at:1)!.value,5) && near(c.sample(at:1)!.velocity,0)),
            ("clamped times",near(a.sample(at:-1)!.value,0) && near(a.sample(at:99)!.value,2)),
            ("invalid durations rejected",CompatMotionTimeline(initial:0,frames:[.spring(target:1,duration:0,model:spring)])==nil)
        ]
        for (name,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(name)") }
        print("MOTION TOTAL \(rows.filter{$0.1}.count)/10")
        if rows.contains(where:{!$0.1}) { exit(1) }
    }
}
