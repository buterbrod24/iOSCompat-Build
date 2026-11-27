import Foundation
@main struct Measure {
    @MainActor static func main() {
        typealias Group=CompatCompletionGroup
        var rows:[(String,Bool)]=[]
        var events:[Group.Result]=[]
        let g=Group(.logical){events.append($0)}
        let a=g.register()!,b=g.register()!
        g.logical(a)
        rows.append(("no callback before seal",events.isEmpty))
        g.seal()
        rows.append(("waits for all tracks",events.isEmpty))
        rows.append(("registration after seal denied",g.register()==nil))
        g.logical(b)
        rows.append(("logical completes group",events==[.completed]))
        g.logical(b);g.removed(a);g.cancel();g.seal()
        rows.append(("terminal callback exactly once",events==[.completed]))
        events=[]
        let h=Group(.removed){events.append($0)}
        let c=h.register()!
        h.seal();h.logical(c)
        rows.append(("logical not sufficient for removed criterion",events.isEmpty))
        h.removed(c)
        rows.append(("removal completes",events==[.completed]))
        events=[]
        let empty=Group(.logical){events.append($0)}
        empty.seal()
        rows.append(("empty sealed group completes immediately",events==[.completed]))
        events=[]
        let cancelled=Group(.removed){events.append($0)}
        let d=cancelled.register()!
        cancelled.seal();cancelled.cancel();cancelled.removed(d)
        rows.append(("cancel once and ignore late signals",events==[.cancelled]))
        events=[]
        let foreign=Group(.logical){events.append($0)}
        let e=foreign.register()!
        foreign.seal();foreign.removed(d)
        rows.append(("foreign token ignored",events.isEmpty))
        foreign.removed(e)
        rows.append(("removal implies logical completion",events==[.completed]))
        var reentrant:Group?
        var count=0
        reentrant=Group(.logical){_ in count+=1;reentrant?.cancel()}
        reentrant?.seal()
        rows.append(("reentrant callback protected",count==1))
        reentrant=nil
        for (n,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(n)") }
        print("TOTAL \(rows.filter{$0.1}.count)/12")
        if rows.count != 12 || rows.contains(where:{!$0.1}) { exit(1) }
    }
}
