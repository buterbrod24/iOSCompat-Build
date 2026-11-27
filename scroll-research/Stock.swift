import SwiftUI
@available(iOS 17.0, *)
@MainActor
public func stockScroll(_ selection:Binding<Int?>)->some View {
    ScrollView(.horizontal) {
        LazyHStack {
            ForEach(0..<5) { id in
                Text(String(id)).frame(width:100).id(id)
            }
        }.scrollTargetLayout()
    }
    .scrollTargetBehavior(ViewAlignedScrollTargetBehavior(limitBehavior:.automatic))
    .scrollPosition(id:selection,anchor:.leading)
}
