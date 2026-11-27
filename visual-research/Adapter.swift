import SwiftUI

public extension View {
    // Caller owns geometry and supplies the layout size and viewport.
    func compatVisualTransform(_ effect:CompatVisualTransform)->some View {
        transformEffect(effect.matrix).opacity(effect.opacity)
    }
}
