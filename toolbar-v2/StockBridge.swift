import SwiftUI
import UIKit

@available(iOS 17.0, *)
@MainActor
@_cdecl("ioscompat_stock_toolbar_pair_test")
public func toolbarPairTest()->Int32 {
    let a=ToolbarItemPlacement.topBarLeading
    let b=ToolbarItemPlacement.topBarTrailing
    let host=UIHostingController(rootView:NavigationStack {
        Text("Compatibility").toolbar {
            ToolbarItem(placement:a) { Button("Leading") {} }
            ToolbarItem(placement:b) { Button("Trailing") {} }
        }
    })
    host.loadViewIfNeeded()
    host.view.frame=CGRect(x:0,y:0,width:240,height:160)
    host.view.layoutIfNeeded()
    return host.view.bounds.width==240 && host.view.bounds.height==160 ? 1:0
}
