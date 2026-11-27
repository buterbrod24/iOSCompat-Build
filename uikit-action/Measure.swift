import UIKit
import Darwin

@main struct Measure {
    @MainActor static func main() {
        var rows: [(String,Bool)] = []
        let icon=UIImage(systemName:"star")
        let selection=UIImage(systemName:"star.fill")
        var desc=CompatActionDescriptor(title:"Favorite",subtitle:"Details",image:icon,
                                       selectedImage:selection,
                                       identifier:UIAction.Identifier(rawValue:"favorite"),
                                       discoverabilityTitle:"Mark as favorite",
                                       attributes:[.destructive],state:.on,handler:{_ in})
        let on=desc.makeLegacyAction()
        rows.append(("title and subtitle preserved",on.action.title=="Favorite" && on.action.subtitle=="Details"))
        rows.append(("identifier and discoverability preserved",on.action.identifier.rawValue=="favorite" && on.action.discoverabilityTitle=="Mark as favorite"))
        rows.append(("ordinary icon not silently replaced",icon != nil && selection != nil && on.action.image === icon))
        rows.append(("custom selection indicator loss reported",on.limitations == [.customSelectionIndicatorUnavailable]))
        rows.append(("selected state and attributes preserved",on.action.state == .on && on.action.attributes.contains(.destructive)))
        desc.selectedImage=nil
        desc.state = .mixed
        desc.attributes=[.disabled,.hidden]
        let mixed=desc.makeLegacyAction()
        rows.append(("mixed state and disabled hidden flags",mixed.action.state == .mixed && mixed.action.attributes.contains(.disabled) && mixed.action.attributes.contains(.hidden)))
        rows.append(("no custom indicator no limitation",mixed.limitations.isEmpty))
        guard let model=CompatSingleSelection(ids:["one","two"],selected:"one") else { exit(1) }
        rows.append(("initial selection",model.state(for:"one") == .on && model.state(for:"two") == .off))
        let switched=model.select("two")
        let repeatSelect=model.select("two")
        rows.append(("single selection transition",switched && !repeatSelect && model.state(for:"one") == .off && model.state(for:"two") == .on))
        let disabled=model.select("one",attributes:.disabled)
        let hidden=model.select("one",attributes:.hidden)
        let unknown=model.select("three")
        rows.append(("blocked selections do not mutate model",!disabled && !hidden && !unknown && model.selected=="two"))
        rows.append(("invalid identifiers rejected",CompatSingleSelection(ids:["one","one"])==nil && CompatSingleSelection(ids:["one"],selected:"two")==nil && CompatSingleSelection(ids:[])==nil))
        let menu=UIMenu(title:"Example",children:[on.action,mixed.action])
        rows.append(("legacy menu accepts native actions",menu.children.count==2))
        for (name,ok) in rows { print("\(ok ? "PASS" : "FAIL") \(name)") }
        print("TOTAL \(rows.filter{$0.1}.count)/\(rows.count)")
        if rows.count != 12 || rows.contains(where:{!$0.1}) { exit(1) }
    }
}
