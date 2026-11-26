import AppIntents
import Foundation
import Darwin

struct Descriptor {
    let kind:UInt32
    let flags:UInt32
    let signatureCount:Int
    let requirementCount:Int
    let baseFlag:UInt32
}
func descriptor(_ h:UnsafeMutableRawPointer,_ name:String) -> Descriptor? {
    guard let p=dlsym(h,name) else {return nil}
    let flags=p.load(as:UInt32.self)
    let generic=Int(p.load(fromByteOffset:12,as:UInt32.self))
    let requirements=Int(p.load(fromByteOffset:16,as:UInt32.self))
    guard flags & 0x1f == 3, generic==1, requirements==1 else {return nil}
    let base=p.load(fromByteOffset:24+generic*12,as:UInt32.self)
    return Descriptor(kind:flags & 0x1f,flags:flags,signatureCount:generic,requirementCount:requirements,baseFlag:base)
}
@main struct Measure {
    @MainActor static func main() async throws {
        guard #available(iOS 17.0, *) else {exit(2)}
        var total=0,passed=0
        func check(_ name:String,_ ok:Bool) {
            total += 1
            if ok {passed += 1}
            print("\(ok ? "PASS" : "FAIL") \(name)")
        }
        let local=LocalActivityIntent()
        let stock=StockActivityIntent()
        check("local inherited generic witness",localThroughActivity(LocalActivityIntent.self))
        check("stock inherited generic witness",stockThroughActivity(StockActivityIntent.self))
        check("local positive cast",localDynamic(local))
        check("stock positive cast",stockDynamic(stock))
        check("local rejects stock",!localDynamic(stock))
        check("stock rejects local",!stockDynamic(local))
        check("local inherits native SystemIntent",(local as Any) is any SystemIntent)
        check("stock inherits native SystemIntent",(stock as Any) is any SystemIntent)
        _ = try await local.perform()
        check("local perform",true)
        _ = try await stock.perform()
        check("stock perform",true)
        print("TOTAL \(passed)/\(total)")
        print("Distinct nominal identities are intentional; no native descriptor alias is authorized")
        if total != passed {exit(1)}
    }
}
