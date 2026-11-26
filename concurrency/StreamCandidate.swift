// Independent implementation using the synchronous legacy stream initializer.
// No executor, runtime, or protocol descriptor replacement.
import Foundation

@available(iOS 16.0, *)
public extension AsyncStream {
    @inline(never)
    static func ioscompatMakeStream(
        of elementType: Element.Type = Element.self,
        bufferingPolicy limit: Continuation.BufferingPolicy = .unbounded
    ) -> (stream: AsyncStream<Element>, continuation: Continuation) {
        var captured: Continuation?
        let stream = AsyncStream<Element>(bufferingPolicy: limit) { captured = $0 }
        guard let continuation = captured else {
            preconditionFailure("Legacy initializer did not synchronously supply its continuation")
        }
        return (stream, continuation)
    }
}

@available(iOS 16.0, *)
public extension AsyncThrowingStream where Failure == Error {
    @inline(never)
    static func ioscompatMakeStream(
        of elementType: Element.Type = Element.self,
        throwing failureType: Failure.Type = Failure.self,
        bufferingPolicy limit: Continuation.BufferingPolicy = .unbounded
    ) -> (stream: AsyncThrowingStream<Element, Failure>, continuation: Continuation) {
        var captured: Continuation?
        let stream = AsyncThrowingStream<Element, Failure>(bufferingPolicy: limit) { captured = $0 }
        guard let continuation = captured else {
            preconditionFailure("Legacy initializer did not synchronously supply its continuation")
        }
        return (stream, continuation)
    }
}
