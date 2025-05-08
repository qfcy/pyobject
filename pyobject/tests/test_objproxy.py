import sys,os,unittest
try:
    from pyobject import ObjChain, ProxiedObj
except ImportError:
    path = __file__
    for i in range(3):
        path = os.path.split(path)[0]
    sys.path.append(path) # 加入当前pyobject库所在的目录
    from pyobject import ObjChain, ProxiedObj

def current_func_name(level = 0):
    frame = sys._getframe()
    for i in range(level + 1):
        if frame is None:return None
        frame = frame.f_back
    if frame is None:return None
    return frame.f_code.co_name

class TestObjChain(unittest.TestCase):
    def print_code(self, chain, print_optimized=False):
        print(f"Test {current_func_name(level = 1)}:")
        print(f"Code:\n{chain.get_code()}")
        if print_optimized:
            print(f"Optimized:\n{chain.get_optimized_code()}\n")
        print()
    def test_target_obj(self): # 测试有target_obj时的行为，如在特定方法（如__str__）中导出值
        chain = ObjChain()
        test_str = "test_str"
        class Cls:
            def __str__(self):
                return test_str

        obj = chain.add_existing_obj(Cls(), "obj")
        self.assertEqual(str(obj), test_str)
        self.print_code(chain)
    def test_no_target_obj(self):
        chain = ObjChain()
        np_ = chain.new_object("import numpy as np","np",
                              use_target_obj=False) # 需要numpy

        arr = np_.array([1,2,3])
        import numpy as np
        real_arr = np.array([1,2,3])
        self.assertEqual(str(arr),str(real_arr))
        self.print_code(chain)
    def test_mixed_target_obj(self): # 测试混合有、无target_obj属性
        class Cls_:
            def __init__(self,obj):
                self.obj = obj

        chain = ObjChain()
        Cls = chain.add_existing_obj(Cls_, "Cls")
        # 无target_obj模式
        Cls2 = chain.new_object("class Cls2:pass","Cls2",use_target_obj=False)
        obj2 = Cls2()
        # 有target_obj模式
        obj = Cls(obj2)
        self.assertTrue(chain.get_target(obj).obj is obj2)
        self.print_code(chain)
    def test_isinstance(self):
        class Cls:pass
        class Cls2:pass
        chain = ObjChain()
        obj = chain.add_existing_obj(Cls(),"obj")
        self.assertTrue(issubclass(type(obj), Cls))
        self.assertFalse(issubclass(type(obj), Cls2))
        self.assertTrue(isinstance(obj, Cls))
        self.assertFalse(isinstance(obj, Cls2))
        self.print_code(chain)
    def test_with(self):
        class Cls:
            def meth(self):pass
            def __enter__(self):print("Entered `with`")
            def __exit__(self,*args):print("Exited from `with`")

        chain = ObjChain()
        obj = chain.add_existing_obj(Cls(),"obj")
        with obj:
            obj.meth()
        self.print_code(chain)
    def test_inheritance(self):
        class Cls:
            def meth(self):pass

        chain = ObjChain(hook_inheritance = True)
        cls = chain.add_existing_obj(Cls,"Cls")
        class Inherited(cls):pass
        Inherited().meth()
        self.print_code(chain, print_optimized = True)
    def test_export(self): # 测试export_funcs和export_attrs
        class Cls:
            def __init__(self):
                self.attr = 42
            def meth(self):
                return 42

        chain = ObjChain()
        obj = chain.add_existing_obj(Cls(),"obj",
                                     export_attrs = ["attr"],
                                     export_funcs = ["meth"])
        self.assertTrue(type(obj.attr) is int)
        self.assertTrue(type(obj.meth()) is int)
        self.print_code(chain)
    def test_delayed_export(self): # 测试属性的延迟导出
        class Cls:
            def __init__(self):
                self.attr = 42
            def meth(self):
                return 42

        class Cls2:
            pass
        chain = ObjChain()
        target_obj = Cls2()
        target_obj.attr = Cls()
        target_obj.attr1 = Cls2()
        target_obj.attr1.attr2 = Cls()
        obj = chain.add_existing_obj(target_obj,"obj",
                                     export_attrs = ["attr1.attr2.attr"],
                                     export_funcs = ["attr1.attr2.meth"])
        self.assertTrue(type(obj.attr1.attr2.attr) is int)
        self.assertTrue(type(obj.attr1.attr2.meth()) is int)
        self.assertFalse(type(obj.attr.attr) is int)
        self.assertFalse(type(obj.attr.meth()) is int)
        self.print_code(chain)

if __name__=="__main__":
    unittest.main()