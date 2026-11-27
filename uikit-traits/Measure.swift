import UIKit
import Darwin

@main struct Measure {
    @MainActor static func main() {
        var rows: [(String,Bool)] = []
        func traits(_ style: UIUserInterfaceStyle = .light,
                    _ size: UIUserInterfaceSizeClass = .compact,
                    _ category: UIContentSizeCategory = .medium,
                    _ scale: CGFloat = 2) -> UITraitCollection {
            UITraitCollection(traitsFrom: [
                UITraitCollection(userInterfaceStyle:style),
                UITraitCollection(horizontalSizeClass:size),
                UITraitCollection(verticalSizeClass:.regular),
                UITraitCollection(preferredContentSizeCategory:category),
                UITraitCollection(displayScale:scale)
            ])
        }
        let a=traits(), b=traits(.dark), c=traits(.dark,.regular,.extraLarge,3)
        let observer=CompatTraitObserver()
        var style=0, size=0, any=0, previousCorrect=false
        let s=observer.register(.style) { old,new in
            style += 1
            previousCorrect = old.userInterfaceStyle == .light && new.userInterfaceStyle == .dark
        }
        _=observer.register(.horizontal) { _,_ in size += 1 }
        _=observer.register(.all) { _,_ in any += 1 }
        rows.append(("registration does not invoke callback",style==0 && size==0 && any==0))
        observer.receive(previous:nil,current:a)
        observer.receive(previous:a,current:a)
        rows.append(("initial and unchanged traits ignored",any==0))
        observer.receive(previous:a,current:b)
        rows.append(("style change filters unrelated registrations",style==1 && size==0 && any==1))
        rows.append(("previous and current values preserved",previousCorrect))
        observer.receive(previous:b,current:c)
        rows.append(("multiple selected changes trigger one callback",style==1 && size==1 && any==2))
        rows.append(("dynamic type and scale changes detected",CompatTraitSet.changed(b,c)==[.horizontal,.contentSize,.scale]))
        observer.unregister(s)
        observer.receive(previous:b,current:a)
        rows.append(("unregistered callback ignored",style==1 && any==3))
        let second=CompatTraitObserver()
        var independent=0
        _=second.register(.style){_,_ in independent+=1}
        observer.receive(previous:a,current:b)
        rows.append(("independent observer state",independent==0))
        let third=CompatTraitObserver()
        var events:[Int]=[]
        var later:CompatTraitObserver.Token?
        _=third.register(.style){ _,_ in
            events.append(1)
            if let later { third.unregister(later) }
            _=third.register(.horizontal){_,_ in events.append(3)}
            third.receive(previous:b,current:c)
        }
        later=third.register(.style){_,_ in events.append(2)}
        third.receive(previous:a,current:b)
        rows.append(("removal during callback and queued nested change",events==[1,3]))
        // The new observer only receives future events, not the current snapshot.
        let fourth=CompatTraitObserver()
        var registrations=0
        _=fourth.register(.style){_,_ in
            _=fourth.register(.style){_,_ in registrations += 1}
        }
        fourth.receive(previous:a,current:b)
        rows.append(("registration during callback waits for next event",registrations==0))
        for (name,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(name)") }
        print("TOTAL \(rows.filter{$0.1}.count)/\(rows.count)")
        if rows.count != 10 || rows.contains(where:{!$0.1}) { exit(1) }
    }
}
