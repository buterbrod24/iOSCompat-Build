// Deliberately no @available(iOS 17, *) on these clients.
// Test the SDK's own back-deployment behavior at each minimum OS.
@inline(never)
public func normalFactory<T>(_ type: T.Type, _ policy: AsyncStream<T>.Continuation.BufferingPolicy)
    -> (stream: AsyncStream<T>, continuation: AsyncStream<T>.Continuation) {
    AsyncStream<T>.makeStream(of: type, bufferingPolicy: policy)
}
@inline(never)
public func throwingFactory<T>(_ type: T.Type, _ policy: AsyncThrowingStream<T, Error>.Continuation.BufferingPolicy)
    -> (stream: AsyncThrowingStream<T, Error>, continuation: AsyncThrowingStream<T, Error>.Continuation) {
    AsyncThrowingStream<T, Error>.makeStream(of: type, throwing: Error.self, bufferingPolicy: policy)
}
