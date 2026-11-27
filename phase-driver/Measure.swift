import Foundation

@main struct Measure {
    @MainActor static func main() {
        var rows:[(String,Bool)]=[]
        func near(_ a:Double,_ b:Double)->Bool { abs(a-b)<1e-7 }
        let d=CompatPhaseDriver(phases:[0,1,2],mode:.once,duration:1,initialTrigger:0)!
        rows.append(("initial",!d.running && d.state.value==0))
        d.trigger(0,now:0)
        rows.append(("duplicate trigger does not start",!d.running))
        d.trigger(1,now:1)
        rows.append(("new trigger starts",d.running && d.requestedPhase==1))
        d.tick(now:1.5)
        rows.append(("intermediate sample",near(d.state.value,0.5) && near(d.state.velocity,1.5)))
        d.tick(now:1.25)
        rows.append(("backward tick ignored",near(d.state.value,0.5)))
        d.trigger(2,now:1.5)
        rows.append(("retrigger preserves value and velocity",near(d.state.value,0.5) && near(d.state.velocity,1.5)))
        d.tick(now:2.5)
        rows.append(("one completion advances next phase",d.completedSteps==1 && d.requestedPhase==2 && near(d.state.value,1)))
        d.tick(now:20)
        rows.append(("late tick advances only one step",d.completedSteps==2 && d.requestedPhase==0 && d.running))
        d.tick(now:21)
        rows.append(("one shot returns and stops",d.completedSteps==3 && !d.running && near(d.state.value,0)))
        d.trigger(3,now:22)
        d.cancel(now:22.5)
        let frozen=d.state.value
        d.tick(now:25)
        rows.append(("cancel freezes and clears velocity",!d.running && near(d.state.value,frozen) && d.state.velocity==0))
        d.reset(now:26)
        rows.append(("reset restores phase and count",d.state.value==0 && d.completedSteps==0))
        let loop=CompatPhaseDriver(phases:[0,1],mode:.repeating,duration:1)!
        loop.start(now:0);loop.tick(now:1);loop.tick(now:2)
        rows.append(("repeat continues",loop.running && loop.requestedPhase==1 && loop.completedSteps==2))
        rows.append(("invalid input rejected",CompatPhaseDriver(phases:[0,.nan],mode:.once,duration:1)==nil && CompatPhaseDriver(phases:[0,1],mode:.once,duration:0)==nil))
        for (n,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(n)") }
        print("TOTAL \(rows.filter{$0.1}.count)/13")
        if rows.count != 13 || rows.contains(where:{!$0.1}) { exit(1) }
    }
}
