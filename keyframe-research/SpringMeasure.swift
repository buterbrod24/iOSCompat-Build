import Foundation

@main struct SpringMeasure {
    static func main() {
        var rows:[(String,Bool)]=[]
        func near(_ a:Double?,_ b:Double,_ tolerance:Double=1e-7)->Bool {
            a.map { abs($0-b)<tolerance } ?? false
        }
        let undamped=CompatSpring(mass:1,stiffness:4,damping:0)!
        let critical=CompatSpring(mass:1,stiffness:4,damping:4)!
        let under=CompatSpring(mass:1,stiffness:4,damping:1)!
        let over=CompatSpring(mass:1,stiffness:4,damping:8)!
        rows.append(("initial displacement and velocity",near(under.sample(from:3,to:9,velocity:2,time:0)?.value,3) && near(under.sample(from:3,to:9,velocity:2,time:0)?.velocity,2)))
        rows.append(("undamped quarter and half period",near(undamped.sample(from:0,to:1,velocity:0,time:.pi/4)?.value,1) && near(undamped.sample(from:0,to:1,velocity:0,time:.pi/2)?.value,2)))
        rows.append(("critical closed form",near(critical.sample(from:0,to:1,velocity:0,time:0.5)?.value,1-2/exp(1))))
        rows.append(("critical velocity",near(critical.sample(from:0,to:1,velocity:0,time:0.5)?.velocity,2/exp(1))))
        rows.append(("underdamped overshoot",(under.sample(from:0,to:1,velocity:0,time:1.6)?.value ?? 0)>1))
        rows.append(("overdamped no overshoot",(over.sample(from:0,to:1,velocity:0,time:3)?.value ?? 2)<1))
        rows.append(("damped long time convergence",[under,critical,over].allSatisfy{near($0.sample(from:0,to:1,velocity:0,time:100)?.value,1)}))
        rows.append(("equilibrium unchanged",near(critical.sample(from:5,to:5,velocity:0,time:1)?.value,5)))
        let t=0.7,h=0.00001
        let valid=[under,critical,over].allSatisfy { s in
            guard let l=s.sample(from:0,to:1,velocity:0.3,time:t-h),
                  let r=s.sample(from:0,to:1,velocity:0.3,time:t+h),
                  let m=s.sample(from:0,to:1,velocity:0.3,time:t) else { return false }
            return abs((r.value-l.value)/(2*h)-m.velocity)<1e-5
        }
        rows.append(("analytical velocity agrees with derivative",valid))
        rows.append(("invalid coefficients and time rejected",CompatSpring(mass:0,stiffness:4,damping:1)==nil && CompatSpring(mass:1,stiffness:4,damping:-1)==nil && under.sample(from:0,to:1,velocity:0,time:-1)==nil))
        for (n,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(n)") }
        print("SPRING TOTAL \(rows.filter{$0.1}.count)/10")
        if rows.count != 10 || rows.contains(where:{!$0.1}) { exit(1) }
    }
}
