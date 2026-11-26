import SwiftUI
import UIKit

@main struct Measure {
    @MainActor static func main() {
        let oldLeading=ToolbarItemPlacement.ioscompatTopBarLeading
        let oldTrailing=ToolbarItemPlacement.ioscompatTopBarTrailing
        let newLeading=ToolbarItemPlacement.topBarLeading
        let newTrailing=ToolbarItemPlacement.topBarTrailing
        func host(_ left:ToolbarItemPlacement,_ right:ToolbarItemPlacement)->UIViewController {
            UIHostingController(rootView:NavigationStack {
                Text("Compatibility").toolbar {
                    ToolbarItem(placement:left) { Button("Leading") {} }
                    ToolbarItem(placement:right) { Button("Trailing") {} }
                }
            })
        }
        let hosts=[host(oldLeading,oldTrailing),host(newLeading,newTrailing),
                   host(oldLeading,newTrailing),host(newLeading,oldTrailing)]
        for (i,h) in hosts.enumerated() {
            h.loadViewIfNeeded()
            h.view.frame=CGRect(x:0,y:0,width:390,height:844)
            h.view.setNeedsLayout()
            h.view.layoutIfNeeded()
            guard h.view.bounds.width==390 && h.view.bounds.height==844 else { exit(1) }
            print("PASS toolbar construction \(i+1)")
        }
        print("TOTAL 4/4")
        print("Construction/layout only, not visual equivalence")
    }
}
