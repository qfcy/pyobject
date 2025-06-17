from time import perf_counter
import random
try:
    from pyobject import ObjChain, ProxiedObj
except ImportError:
    import sys,os
    path = __file__
    for i in range(3):
        path = os.path.split(path)[0]
    sys.path.append(path) # 加入当前pyobject库所在的目录
    from pyobject import ObjChain, ProxiedObj

REPEAT_TIMES = 20000

def test_perf(use_objproxy=True):
    chain = ObjChain(export_trivial_obj=False)
    class Cls:
        def __init__(self, value=None):
            self.attr = value
        def meth(self):
            return self.attr
        __call__ = meth
        def __add__(self, other):
            return Cls(other)

    if use_objproxy:
        Cls = chain.add_existing_obj(Cls,"Cls")

    obj1, obj2 = Cls(1), Cls(42)
    obj1.attr, obj2.attr = obj2, obj1
    start = perf_counter()
    for _ in range(REPEAT_TIMES):
        op = random.randint(0,3)
        if op == 0:
            new_obj = obj1 + obj2
            obj1, obj2 = obj2, new_obj
        elif op == 1:
            new_obj = obj1.attr
            obj1, obj2 = obj2, new_obj
        elif op == 2:
            new_obj = obj1() #obj1.meth()
            obj1, obj2 = obj2, new_obj
        elif op == 3:
            obj1.attr = obj1
    print(f"use_objproxy={use_objproxy}: {perf_counter()-start:.9f}s")

if __name__=="__main__":
    print(f"REPEAT_TIMES={REPEAT_TIMES}")
    test_perf(True)
    test_perf(False)