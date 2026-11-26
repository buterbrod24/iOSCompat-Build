import Foundation

@main struct Measure {
    static func main() {
        let a=NSObject(), b=NSObject()
        let input:[AnyObject]=[a]
        let contiguous=ContiguousArray(input)
        let result=appendArray(input,b,64)
        let other=appendContiguous(contiguous,b,64)
        let copy=copyArray(input)
        let checks=[
            input.count==1 && result.count==2,
            result[0]===a && result[1]===b,
            contiguous.count==1 && other.count==2,
            other[0]===a && other[1]===b,
            copy.count==1 && copy[0]===a,
            getElement(result,1)===b
        ]
        for (i,ok) in checks.enumerated(){print("\(ok ? "PASS" : "FAIL") array check \(i+1)")}
        print("TOTAL \(checks.filter{$0}.count)/\(checks.count)")
        if checks.contains(false){exit(1)}
    }
}
