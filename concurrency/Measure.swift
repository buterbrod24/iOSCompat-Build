import Foundation

private enum TestError: Error { case sentinel }
@main struct Measure {
    static func main() async {
        var count=0
        var failed=0
        func check(_ name:String,_ ok:Bool) {
            count += 1
            if !ok { failed += 1 }
            print("\(ok ? "PASS" : "FAIL") \(name)")
        }
        func values(_ stream:AsyncStream<Int>) async -> [Int] {
            var a:[Int]=[]
            for await x in stream { a.append(x) }
            return a
        }
        // Compare buffering and termination against the installed modern runtime.
        for (name, policy, expected) in [
            ("unbounded",AsyncStream<Int>.Continuation.BufferingPolicy.unbounded,[1,2,3]),
            ("newest",.bufferingNewest(2),[2,3]),
            ("oldest",.bufferingOldest(2),[1,2]),
            ("zero",.bufferingNewest(0),[])
        ] {
            let a=AsyncStream<Int>.ioscompatMakeStream(bufferingPolicy:policy)
            let b=AsyncStream<Int>.makeStream(bufferingPolicy:policy)
            for x in [1,2,3] { a.continuation.yield(x); b.continuation.yield(x) }
            a.continuation.finish(); b.continuation.finish()
            let av=await values(a.stream)
            let bv=await values(b.stream)
            check("stream \(name)",av==expected && av==bv)
            if case .terminated = a.continuation.yield(4) { check("terminated \(name)",true) }
            else { check("terminated \(name)",false) }
        }
        let a=AsyncThrowingStream<Int,Error>.ioscompatMakeStream(bufferingPolicy:.bufferingNewest(2))
        let b=AsyncThrowingStream<Int,Error>.makeStream(bufferingPolicy:.bufferingNewest(2))
        for x in [1,2,3] { a.continuation.yield(x); b.continuation.yield(x) }
        a.continuation.finish(throwing:TestError.sentinel)
        b.continuation.finish(throwing:TestError.sentinel)
        func consume(_ stream:AsyncThrowingStream<Int,Error>) async -> ([Int],Bool) {
            var values:[Int]=[]
            do { for try await v in stream { values.append(v) }; return (values,false) }
            catch TestError.sentinel { return (values,true) }
            catch { return (values,false) }
        }
        let av=await consume(a.stream),bv=await consume(b.stream)
        check("throwing buffered values",av.0==[2,3] && av.0==bv.0)
        check("throwing error propagation",av.1 && bv.1)
        let ref=NSObject()
        let r=AsyncStream<NSObject>.ioscompatMakeStream()
        r.continuation.yield(ref); r.continuation.finish()
        var iter=r.stream.makeAsyncIterator()
        let item=await iter.next()
        check("reference identity",item === ref)
        let end=await iter.next()
        check("reference stream ends",end==nil)
        print("TOTAL \(count-failed)/\(count)")
        if failed != 0 { exit(1) }
    }
}
