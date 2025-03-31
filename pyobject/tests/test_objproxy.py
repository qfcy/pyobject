import sys,os,unittest
try:
    from pyobject import ObjChain, ProxiedObj
except ImportError:
    path = __file__
    for i in range(3):
        path = os.path.split(path)[0]
    sys.path.append(path) # 加入当前pyobject库所在的目录
    from pyobject import ObjChain, ProxiedObj

class TestObjChain(unittest.TestCase):
    def test_target_obj(self): # 测试有target_obj时的行为，如在特定方法（如__str__）中导出值
        chain = ObjChain()
        test_str = "test_str"
        class Cls:
            def __str__(self):
                return test_str

        obj = chain.add_existing_obj(Cls(), "obj")
        self.assertEqual(str(obj), test_str)
        print(f"Code:\n{chain.get_code()}\n")
    def test_no_target_obj(self):
        chain = ObjChain()
        np_ = chain.new_object("import numpy as np","np",
                              use_target_obj=False) # 需要numpy

        arr = np_.array([1,2,3])
        import numpy as np
        real_arr = np.array([1,2,3])
        self.assertEqual(str(arr),str(real_arr))
        print(f"Code:\n{chain.get_code()}\n")
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
        print(f"Code:\n{chain.get_code()}\n")
    def test_isinstance(self):
        class Cls:pass
        chain = ObjChain()
        obj = chain.add_existing_obj(Cls(),"obj")
        self.assertTrue(issubclass(type(obj), Cls)) # 需要有pyobj_extension库，测试才会成功
        self.assertTrue(isinstance(obj, Cls))
        print(f"Code:\n{chain.get_code()}\n")
    def test_with(self):
        class Cls:
            def meth(self):pass
            def __enter__(self):print("Entered `with`")
            def __exit__(self,*args):print("Exited from `with`")

        chain = ObjChain()
        obj = chain.add_existing_obj(Cls(),"obj")
        with obj:
            obj.meth()
        print(f"Code:\n{chain.get_code()}\n")
        print(f"Optimized:\n{chain.get_optimized_code()}\n")

if __name__=="__main__":
    unittest.main()