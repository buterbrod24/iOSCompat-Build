import UIKit

// The legacy API keeps UIKit's ordinary image and state indicator separate.
// Custom selected-image rendering is explicitly unsupported.
@MainActor
struct CompatActionDescriptor {
    var title: String
    var subtitle: String? = nil
    var image: UIImage? = nil
    var selectedImage: UIImage? = nil
    var identifier: UIAction.Identifier? = nil
    var discoverabilityTitle: String? = nil
    var attributes: UIMenuElement.Attributes = []
    var state: UIMenuElement.State = .off
    var handler: UIActionHandler

    enum Limitation: String, Equatable {
        case customSelectionIndicatorUnavailable
    }

    struct Materialized {
        let action: UIAction
        let limitations: [Limitation]
    }

    func makeLegacyAction() -> Materialized {
        let action = UIAction(title:title,subtitle:subtitle,image:image,
                              identifier:identifier,discoverabilityTitle:discoverabilityTitle,
                              attributes:attributes,state:state,handler:handler)
        let limitations: [Limitation] = selectedImage == nil ? [] : [.customSelectionIndicatorUnavailable]
        return Materialized(action:action,limitations:limitations)
    }
}

// Explicit owner-managed selection model, not an emulation of all UIMenu behavior.
@MainActor
final class CompatSingleSelection {
    let ids: [String]
    private(set) var selected: String?
    init?(ids:[String],selected:String?=nil) {
        guard !ids.isEmpty, ids.allSatisfy({ !$0.isEmpty }), Set(ids).count==ids.count,
              selected.map({ids.contains($0)}) ?? true else { return nil }
        self.ids=ids
        self.selected=selected
    }

    @discardableResult
    func select(_ id:String, attributes:UIMenuElement.Attributes=[]) -> Bool {
        guard ids.contains(id), !attributes.contains(.disabled), !attributes.contains(.hidden) else { return false }
        guard selected != id else { return false }
        selected=id
        return true
    }

    func state(for id:String) -> UIMenuElement.State {
        selected==id ? .on : .off
    }
}
