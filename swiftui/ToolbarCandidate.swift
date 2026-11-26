import SwiftUI

// Return the native legacy placement, not an invented opaque representation.
@available(iOS 16.0, *)
public extension ToolbarItemPlacement {
    @inline(never)
    static var ioscompatTopBarLeading: ToolbarItemPlacement {
        .navigationBarLeading
    }
}
