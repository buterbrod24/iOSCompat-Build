// Independent compiler evidence for reference-element array specialization.
// No replacement exports or assumptions about private buffer layout.
import Foundation

@inline(never)
public func appendArray(_ input:[AnyObject], _ element:AnyObject, _ capacity:Int)->[AnyObject] {
    var result = input
    result.reserveCapacity(capacity)
    result.append(element)
    return result
}
@inline(never)
public func appendContiguous(_ input:ContiguousArray<AnyObject>, _ element:AnyObject, _ capacity:Int)->ContiguousArray<AnyObject> {
    var result = input
    result.reserveCapacity(capacity)
    result.append(element)
    return result
}
@inline(never)
public func copyArray(_ input:[AnyObject])->ContiguousArray<AnyObject> {
    ContiguousArray(input)
}
@inline(never)
public func getElement(_ input:[AnyObject], _ i:Int)->AnyObject { input[i] }
