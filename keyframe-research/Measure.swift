import Foundation

@main struct Measure {
    static func main() {
        var rows:[(String,Bool)]=[]
        func close(_ a:Double?,_ b:Double)->Bool { a.map{abs($0-b)<1e-8} ?? false }
        let line=CompatScalarTimeline(initial:0,frames:[.linear(10,duration:2)])!
        rows.append(("linear midpoint",close(line.value(at:1),5)))
        rows.append(("clamped before and after",close(line.value(at:-1),0) && close(line.value(at:3),10)))
        let jump=CompatScalarTimeline(initial:0,frames:[.move(3),.linear(7,duration:2),.move(9)])!
        rows.append(("instant initial and terminal moves",close(jump.value(at:0),3) && close(jump.value(at:2),9)))
        rows.append(("linear following move",close(jump.value(at:1),5)))
        let hold=CompatScalarTimeline(initial:2,frames:[.linear(2,duration:1),.linear(6,duration:1)])!
        rows.append(("hold then advance",close(hold.value(at:0.5),2) && close(hold.value(at:1.5),4)))
        let cubic=CompatScalarTimeline(initial:0,frames:[.cubic(8,duration:2,startVelocity:0,endVelocity:0)])!
        rows.append(("cubic Hermite values",close(cubic.value(at:0.5),1.25) && close(cubic.value(at:1),4)))
        let slope=CompatScalarTimeline(initial:0,frames:[.cubic(4,duration:2,startVelocity:2,endVelocity:2)])!
        rows.append(("explicit velocity preserved",close(slope.value(at:0.5),1) && close(slope.value(at:1.5),3)))
        rows.append(("invalid inputs rejected",CompatScalarTimeline(initial:.nan,frames:[])==nil && CompatScalarTimeline(initial:0,frames:[.linear(1,duration:0)])==nil && line.value(at:.infinity)==nil))
        struct State { var x=0.0;var y=1.0 }
        var timeline=CompatTimeline(initial:State())
        let added=timeline.add(\.x,frames:[.linear(8,duration:2)])
        let added2=timeline.add(\.y,frames:[.linear(3,duration:1)])
        rows.append(("independent tracks sampled together",added && added2 && close(timeline.value(at:0.5)?.x,2) && close(timeline.value(at:0.5)?.y,2)))
        rows.append(("shorter track holds end value",close(timeline.duration,2) && close(timeline.value(at:1.5)?.x,6) && close(timeline.value(at:1.5)?.y,3)))
        rows.append(("duplicate track rejected",!timeline.add(\.x,frames:[.move(100)])))
        rows.append(("empty timeline returns initial",close(CompatScalarTimeline(initial:7,frames:[])?.value(at:2),7)))
        for (name,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(name)") }
        print("TOTAL \(rows.filter{$0.1}.count)/12")
        if rows.count != 12 || rows.contains(where:{!$0.1}) { exit(1) }
    }
}
