// Value-scoped, explicitly typed object registry. No native Environment ABI.
struct CompatObjectScope {
    private var objects:[ObjectIdentifier:AnyObject]=[:]
    func object<T:AnyObject & Observable>(_ type:T.Type)->T? {
        objects[ObjectIdentifier(type)] as? T
    }
    func setting<T:AnyObject & Observable>(_ type:T.Type,_ value:T?)->Self {
        var next=self
        next.objects[ObjectIdentifier(type)]=value
        return next
    }
}
