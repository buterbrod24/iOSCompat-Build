extern int ioscompat_leaf_value(void);
int main(void) { return ioscompat_leaf_value() == 42 ? 0 : 1; }
