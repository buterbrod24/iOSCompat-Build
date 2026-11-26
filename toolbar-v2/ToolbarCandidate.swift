import SwiftUI

@available(iOS 16.0, *)
public extension ToolbarItemPlacement {
    @inline(never)
    static var ioscompatTopBarLeading: ToolbarItemPlacement { .navigationBarLeading }
    @inline(never)
    static var ioscompatTopBarTrailing: ToolbarItemPlacement { .navigationBarTrailing }
}
