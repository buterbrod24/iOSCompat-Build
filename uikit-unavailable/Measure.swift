import UIKit
import Darwin

@main struct Measure {
    @MainActor static func main() {
        var rows:[(String,Bool)]=[]
        let parent=UIView(frame:CGRect(x:0,y:0,width:390,height:844))
        let host=CompatUnavailableHost(container:parent)
        host.update(nil)
        rows.append(("nil does not create placeholder",parent.subviews.isEmpty))
        host.update(.empty(title:"No results",message:"Try again"))
        guard let view=host.placeholder else { exit(1) }
        rows.append(("empty title and message",view.titleLabel.text=="No results" && view.messageLabel.text=="Try again"))
        rows.append(("empty state hides missing optional content",view.iconView.isHidden && view.actionButton.isHidden && !view.indicator.isAnimating))
        rows.append(("dynamic type and header accessibility",view.titleLabel.adjustsFontForContentSizeCategory && view.messageLabel.adjustsFontForContentSizeCategory && view.titleLabel.accessibilityTraits.contains(.header)))
        host.update(.loading(title:"Loading"))
        rows.append(("loading reuses view",host.placeholder === view && parent.subviews.count==1 && view.indicator.isAnimating))
        rows.append(("loading clears prior message",view.messageLabel.isHidden && view.messageLabel.text==nil))
        var count=0
        var retry=CompatUnavailableConfiguration.empty(title:"Offline",image:UIImage(systemName:"wifi.slash"))
        retry.actionTitle="Retry"
        retry.action={count+=1}
        host.update(retry)
        view.actionButton.sendActions(for:.touchUpInside)
        rows.append(("retry action and image",count==1 && !view.iconView.isHidden && !view.actionButton.isHidden && !view.indicator.isAnimating))
        host.update(.empty(title:"Done"))
        view.actionButton.sendActions(for:.touchUpInside)
        rows.append(("old action cleared",count==1 && view.actionButton.isHidden && !view.actionButton.isEnabled))
        host.update(nil)
        rows.append(("removal detaches view",host.placeholder==nil && view.superview==nil && parent.subviews.isEmpty))
        host.update(.empty(title:"New"))
        parent.layoutIfNeeded()
        rows.append(("recreate and constrain to owner",host.placeholder !== view && host.placeholder?.frame==parent.bounds))
        for (name,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(name)") }
        print("TOTAL \(rows.filter{$0.1}.count)/\(rows.count)")
        if rows.count != 10 || rows.contains(where:{!$0.1}) { exit(1) }
    }
}
