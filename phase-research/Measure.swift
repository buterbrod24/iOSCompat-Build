import Foundation

@main struct Measure {
    static func main() {
        typealias Seq=CompatPhaseSequence<Int,Int>
        var rows:[(String,Bool)]=[]
        rows.append(("empty input rejected",Seq(phases:[],mode:.once)==nil))
        var single=Seq(phases:[5],mode:.repeating)!
        rows.append(("single phase inert",single.start()==nil && single.phase==5 && !single.running))
        var p=Seq(phases:[0,1,2],mode:.once,initialTrigger:0)!
        rows.append(("initial phase",p.phase==0 && p.pending==nil))
        rows.append(("equal trigger ignored",p.trigger(0)==nil && !p.running))
        let a=p.trigger(1)!
        rows.append(("distinct trigger requests second phase",a.from==0 && a.to==1 && p.running))
        rows.append(("start while running ignored",p.start()==nil))
        rows.append(("unrelated completion ignored",p.complete(UUID())==nil && p.pending?.token==a.token))
        let b=p.complete(a.token)!
        rows.append(("acknowledgment advances",b.from==1 && b.to==2))
        rows.append(("duplicate completion ignored",p.complete(a.token)==nil && p.pending?.token==b.token))
        let c=p.complete(b.token)!
        rows.append(("final phase returns to initial",c.from==2 && c.to==0))
        rows.append(("one shot stops after return acknowledgment",p.complete(c.token)==nil && !p.running))
        let d=p.trigger(2)!
        let e=p.trigger(3)!
        rows.append(("restart invalidates outstanding token",d.token != e.token && p.complete(d.token)==nil && p.pending?.token==e.token))
        p.cancel()
        rows.append(("cancel rejects late completion",p.complete(e.token)==nil && !p.running))
        p.reset()
        rows.append(("reset restores initial",p.phase==0 && p.pending==nil))
        var loop=Seq(phases:[0,1],mode:.repeating)!
        let x=loop.start()!,y=loop.complete(x.token)!,z=loop.complete(y.token)!
        rows.append(("repeat continues after initial phase",z.to==1 && loop.running))
        for (n,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(n)") }
        print("TOTAL \(rows.filter{$0.1}.count)/15")
        if rows.count != 15 || rows.contains(where:{!$0.1}) { exit(1) }
    }
}
