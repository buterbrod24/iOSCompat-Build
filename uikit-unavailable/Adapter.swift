import UIKit

// Original source-level placeholder component for explicit opt-in clients.
struct CompatUnavailableConfiguration {
    var title: String?
    var message: String?
    var image: UIImage?
    var loading = false
    var actionTitle: String?
    var action: (() -> Void)?

    static func empty(title:String,message:String?=nil,image:UIImage?=nil) -> Self {
        Self(title:title,message:message,image:image)
    }
    static func loading(title:String?=nil) -> Self {
        Self(title:title,loading:true)
    }
}

@MainActor
final class CompatUnavailableView: UIView {
    let titleLabel=UILabel()
    let messageLabel=UILabel()
    let iconView=UIImageView()
    let indicator=UIActivityIndicatorView(style:.medium)
    let actionButton=UIButton(type:.system)
    private let scroll=UIScrollView()
    private let stack=UIStackView()
    private var action: (() -> Void)?

    init(configuration:CompatUnavailableConfiguration) {
        super.init(frame:.zero)
        backgroundColor = .systemBackground
        scroll.translatesAutoresizingMaskIntoConstraints=false
        stack.translatesAutoresizingMaskIntoConstraints=false
        stack.axis = .vertical
        stack.alignment = .center
        stack.spacing = 12
        addSubview(scroll)
        scroll.addSubview(stack)
        NSLayoutConstraint.activate([
            scroll.topAnchor.constraint(equalTo:safeAreaLayoutGuide.topAnchor),
            scroll.bottomAnchor.constraint(equalTo:safeAreaLayoutGuide.bottomAnchor),
            scroll.leadingAnchor.constraint(equalTo:leadingAnchor),
            scroll.trailingAnchor.constraint(equalTo:trailingAnchor),
            stack.topAnchor.constraint(greaterThanOrEqualTo:scroll.contentLayoutGuide.topAnchor,constant:24),
            stack.bottomAnchor.constraint(lessThanOrEqualTo:scroll.contentLayoutGuide.bottomAnchor,constant:-24),
            stack.leadingAnchor.constraint(equalTo:scroll.contentLayoutGuide.leadingAnchor,constant:24),
            stack.trailingAnchor.constraint(equalTo:scroll.contentLayoutGuide.trailingAnchor,constant:-24),
            scroll.contentLayoutGuide.widthAnchor.constraint(equalTo:scroll.frameLayoutGuide.widthAnchor),
            scroll.contentLayoutGuide.heightAnchor.constraint(greaterThanOrEqualTo:scroll.frameLayoutGuide.heightAnchor),
            stack.centerYAnchor.constraint(equalTo:scroll.contentLayoutGuide.centerYAnchor),
        ])
        for label in [titleLabel,messageLabel] {
            label.numberOfLines=0
            label.textAlignment = .center
            label.adjustsFontForContentSizeCategory=true
        }
        titleLabel.font = .preferredFont(forTextStyle:.title2)
        titleLabel.accessibilityTraits.insert(.header)
        messageLabel.font = .preferredFont(forTextStyle:.body)
        messageLabel.textColor = .secondaryLabel
        iconView.contentMode = .scaleAspectFit
        iconView.isAccessibilityElement=false
        iconView.tintColor = .secondaryLabel
        iconView.setContentCompressionResistancePriority(.defaultLow,for:.horizontal)
        iconView.setContentCompressionResistancePriority(.defaultLow,for:.vertical)
        indicator.hidesWhenStopped=true
        indicator.accessibilityLabel=NSLocalizedString("Loading",comment:"Placeholder spinner")
        actionButton.titleLabel?.adjustsFontForContentSizeCategory=true
        actionButton.titleLabel?.font = .preferredFont(forTextStyle:.body)
        actionButton.titleLabel?.numberOfLines=0
        actionButton.addTarget(self,action:#selector(activate),for:.touchUpInside)
        for view in [iconView,indicator,titleLabel,messageLabel,actionButton] { stack.addArrangedSubview(view) }
        apply(configuration)
    }
    required init?(coder:NSCoder) { return nil }

    func apply(_ value:CompatUnavailableConfiguration) {
        titleLabel.text=value.title
        titleLabel.isHidden=value.title?.isEmpty ?? true
        messageLabel.text=value.message
        messageLabel.isHidden=value.message?.isEmpty ?? true
        iconView.image=value.image
        iconView.isHidden=value.image==nil
        if value.loading { indicator.startAnimating() } else { indicator.stopAnimating() }
        action=value.action
        actionButton.setTitle(value.actionTitle,for:.normal)
        actionButton.isHidden=(value.actionTitle?.isEmpty ?? true) || value.action==nil
        actionButton.isEnabled = !actionButton.isHidden
    }
    @objc private func activate() {
        _ = performConfiguredAction()
    }
    @discardableResult
    func performConfiguredAction() -> Bool {
        guard !actionButton.isHidden, actionButton.isEnabled, let action else { return false }
        action()
        return true
    }
}

// Explicit owner-managed lifecycle, without replacing UIViewController properties.
@MainActor
final class CompatUnavailableHost {
    private weak var container:UIView?
    private(set) var placeholder:CompatUnavailableView?
    init(container:UIView) { self.container=container }
    func update(_ configuration:CompatUnavailableConfiguration?) {
        guard let configuration else { placeholder?.removeFromSuperview();placeholder=nil;return }
        if let placeholder { placeholder.apply(configuration);return }
        guard let container else { return }
        let view=CompatUnavailableView(configuration:configuration)
        view.translatesAutoresizingMaskIntoConstraints=false
        container.addSubview(view)
        NSLayoutConstraint.activate([
            view.topAnchor.constraint(equalTo:container.topAnchor),
            view.bottomAnchor.constraint(equalTo:container.bottomAnchor),
            view.leadingAnchor.constraint(equalTo:container.leadingAnchor),
            view.trailingAnchor.constraint(equalTo:container.trailingAnchor)
        ])
        placeholder=view
    }
}
