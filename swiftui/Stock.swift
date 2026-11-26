import SwiftUI

@available(iOS 17.0, *)
@inline(never)
public func stockLeading() -> ToolbarItemPlacement { .topBarLeading }

// Independent compiler-generated back-deployment evidence.
@available(iOS 16.0, *)
@inline(never)
public func backdeployLeading() -> ToolbarItemPlacement { .topBarLeading }
