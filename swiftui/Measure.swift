import SwiftUI
import UIKit

@main struct Measure {
    @MainActor static func main() {
        let old = ToolbarItemPlacement.ioscompatTopBarLeading
        let modern = ToolbarItemPlacement.topBarLeading
        // Build and lay out both real toolbars, not a bytewise comparison
        // of a resilient SwiftUI type.
        let a = UIHostingController(rootView: NavigationStack {
            Text("Compatibility").toolbar { ToolbarItem(placement:old) { Text("Leading") } }
        })
        let b = UIHostingController(rootView: NavigationStack {
            Text("Compatibility").toolbar { ToolbarItem(placement:modern) { Text("Leading") } }
        })
        for host in [a as UIViewController,b as UIViewController] {
            host.loadViewIfNeeded()
            host.view.frame = CGRect(x:0,y:0,width:390,height:844)
            host.view.setNeedsLayout()
            host.view.layoutIfNeeded()
            guard host.view.bounds.width == 390 else { exit(1) }
        }
        print("PASS candidate and native toolbar construction/layout")
        print("No rendered visual equivalence or device behavior claim")
    }
}
