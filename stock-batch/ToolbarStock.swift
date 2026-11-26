import SwiftUI
import UIKit

@available(iOS 17.0, *)
@MainActor
@_cdecl("ioscompat_stock_toolbar_test")
public func toolbarTest() -> Int32 {
    let placement = ToolbarItemPlacement.topBarLeading
    let host = UIHostingController(rootView: NavigationStack {
        Text("Compatibility").toolbar { ToolbarItem(placement:placement) { Text("Leading") } }
    })
    host.loadViewIfNeeded()
    host.view.frame = CGRect(x:0,y:0,width:240,height:160)
    host.view.layoutIfNeeded()
    return host.view.bounds.width == 240 ? 1 : 0
}
