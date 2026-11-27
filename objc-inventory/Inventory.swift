import UIKit
import ObjectiveC
import Darwin

// Read method lists rather than sending messages to unverified selectors.
// No method injection, swizzling, dynamic resolver call or instance creation.
@MainActor
enum ObjCInventory {
    static let classes = ["UIView","UIViewController","UITraitCollection","UIAction",
                          "UIPresentationController","UITextItem","UIContentUnavailableView",
                          "UIContentUnavailableConfiguration","NSAttributedString"]
    static let protocols = ["NSObject","UIContentConfiguration","UITraitEnvironment",
                            "UITraitChangeObservable","UITraitChangeRegistration"]
    struct Query {
        let cls: String
        let selector: String
        let classMethod: Bool
        init(_ cls:String,_ selector:String,_ classMethod:Bool=false) {
            self.cls=cls; self.selector=selector; self.classMethod=classMethod
        }
    }
    static let queries = [
        Query("UIView","traitCollection"), Query("UIView","traitCollectionDidChange:"),
        Query("UIView","registerForTraitChanges:withAction:"),
        Query("UIView","registerForTraitChanges:withHandler:"),
        Query("UIView","unregisterForTraitChanges:"),
        Query("UIViewController","traitCollectionDidChange:"),
        Query("UIViewController","registerForTraitChanges:withAction:"),
        Query("UIViewController","registerForTraitChanges:withHandler:"),
        Query("UIViewController","contentUnavailableConfiguration"),
        Query("UIViewController","setContentUnavailableConfiguration:"),
        Query("UIPresentationController","traitCollection"),
        Query("UITraitCollection","userInterfaceStyle"),
        Query("UITraitCollection","horizontalSizeClass"),
        Query("UITraitCollection","preferredContentSizeCategory"),
        Query("UIAction","title"), Query("UIAction","subtitle"),
        Query("UIAction","setSubtitle:"), Query("UIAction","selectedImage"),
        Query("UIAction","setSelectedImage:"),
        Query("UIContentUnavailableConfiguration","emptyConfiguration",true),
        Query("UIContentUnavailableConfiguration","loadingConfiguration",true),
        Query("UITextItem","range")
    ]

    static func lookup(_ name:String) -> AnyClass? {
        name.withCString { objc_lookUpClass($0) }
    }
    static func classLine(_ name:String) -> String {
        guard let cls=lookup(name) else { return "CLASS\t\(name)\tNOT_OBSERVED" }
        return "CLASS\t\(name)\tPRESENT\t" + (class_getSuperclass(cls).map { NSStringFromClass($0) } ?? "-")
    }
    static func protocolLine(_ name:String) -> String {
        let found=name.withCString { objc_getProtocol($0) } != nil
        return "PROTOCOL\t\(name)\t\(found ? "PRESENT" : "NOT_OBSERVED")"
    }
    static func methodLine(_ q:Query) -> String {
        let prefix="METHOD\t\(q.cls)\t\(q.classMethod ? "+" : "-")\t\(q.selector)"
        guard let cls=lookup(q.cls) else { return prefix+"\tCLASS_NOT_OBSERVED" }
        var current: AnyClass?=q.classMethod ? object_getClass(cls) : cls
        var depth=0
        while let owner=current, depth<128 {
            var count:UInt32=0
            if let methods=class_copyMethodList(owner,&count) {
                defer { free(methods) }
                for i in 0..<Int(count) {
                    let method=methods[i]
                    if NSStringFromSelector(method_getName(method))==q.selector {
                        let enc=method_getTypeEncoding(method).map { String(cString:$0) } ?? "-"
                        return prefix+"\tPRESENT\t"+NSStringFromClass(owner)+"\t"+enc
                    }
                }
            }
            current=class_getSuperclass(owner)
            depth+=1
        }
        return prefix+"\tNOT_OBSERVED"
    }
    static func run() -> [String] {
        classes.map(classLine) + protocols.map(protocolLine) + queries.map(methodLine)
    }
}
