import Foundation

private enum ProbeError: Error { case expected }
private typealias Completion = @convention(c) (UnsafeMutableRawPointer?, Int32) -> Void

// This entry is only used in our own rebinding experiment on iOS 16.2.
// No availability override or application-wide modification.
@available(iOS 17.0, *)
@_cdecl("ioscompat_stock_stream_tests")
public func streamTests(_ context: UnsafeMutableRawPointer?, _ callback: @escaping @convention(c) (UnsafeMutableRawPointer?, Int32) -> Void) {
    Task {
        var mask:Int32 = 0
        let a = AsyncStream<Int>.makeStream(bufferingPolicy:.bufferingNewest(2))
        a.continuation.yield(1); a.continuation.yield(2); a.continuation.yield(3)
        a.continuation.finish()
        var values:[Int]=[]
        for await x in a.stream { values.append(x) }
        if values == [2,3] { mask |= 1 }
        if case .terminated = a.continuation.yield(4) { mask |= 2 }
        let b = AsyncThrowingStream<Int,Error>.makeStream(bufferingPolicy:.bufferingOldest(2))
        b.continuation.yield(5); b.continuation.yield(6); b.continuation.yield(7)
        b.continuation.finish(throwing:ProbeError.expected)
        values=[]
        do { for try await x in b.stream { values.append(x) } }
        catch ProbeError.expected { mask |= 4 }
        catch {}
        if values == [5,6] { mask |= 8 }
        let obj = NSObject()
        let c = AsyncStream<NSObject>.makeStream()
        c.continuation.yield(obj); c.continuation.finish()
        var iterator = c.stream.makeAsyncIterator()
        let first = await iterator.next()
        if first === obj { mask |= 16 }
        let end = await iterator.next()
        if end == nil { mask |= 32 }
        callback(context,mask)
    }
}
