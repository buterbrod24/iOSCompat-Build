import Foundation
@main struct Measure {
    static func main() {
        typealias T=CompatSnapTargets.Target
        let t=CompatSnapTargets(targets:[T(id:3,offset:200),T(id:0,offset:0),T(id:1,offset:70),T(id:2,offset:130)],minimum:0,maximum:180)!
        let rows:[(String,Bool)]=[
            ("sort explicit targets",t.targets.map{$0.id} == [0,1,2,3]),
            ("clamp endpoint",t.targets.last?.offset==180),
            ("nearest projected offset",t.snap(current:0,proposed:122,velocity:1)?.id==2),
            ("variable target spacing",t.snap(current:130,proposed:80,velocity:-1)?.id==1),
            ("positive tie",t.snap(current:0,proposed:100,velocity:1)?.id==2),
            ("negative tie",t.snap(current:130,proposed:100,velocity:-1)?.id==1),
            ("forward limit",t.snap(current:0,proposed:180,velocity:1,limit:1)?.id==1),
            ("backward limit",t.snap(current:180,proposed:0,velocity:-1,limit:1)?.id==2),
            ("zero limit",t.snap(current:70,proposed:180,velocity:1,limit:0)?.id==1),
            ("large limit no overflow",t.snap(current:0,proposed:180,velocity:1,limit:Int.max)?.id==3),
            ("out of bounds proposal",t.snap(current:0,proposed:999,velocity:1)?.offset==180),
            ("duplicate IDs rejected",CompatSnapTargets(targets:[T(id:1,offset:0),T(id:1,offset:10)],minimum:0,maximum:20)==nil),
            ("invalid values rejected",t.snap(current:.nan,proposed:0,velocity:0)==nil && t.snap(current:0,proposed:0,velocity:0,limit:-1)==nil),
            ("empty targets rejected",CompatSnapTargets(targets:[],minimum:0,maximum:1)==nil)
        ]
        for (n,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(n)") }
        print("TOTAL \(rows.filter{$0.1}.count)/14")
        if rows.contains(where:{!$0.1}) { exit(1) }
    }
}
