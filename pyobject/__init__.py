"""A multifunctional all-in-one utility tool for managing internal Python \
objects, compatible with nearly all Python 3 versions.
一个多功能合一的提供操作Python对象底层工具的Python包, 支持几乎所有Python 3版本。
"""
import sys
from warnings import warn
from pprint import pprint

__version__="1.2.9.2"

__all__=["objectname","bases","describe","desc"]
_ignore_names=["__builtins__","__doc__"]

MAXLENGTH=150

def objectname(obj):
    # 返回对象的全名，类似__qualname__属性
    # if hasattr(obj,"__qualname__"):return obj.__qualname__
    if not obj.__class__==type:obj=obj.__class__
    if not hasattr(obj,"__module__") or obj.__module__=="__main__":
        return obj.__name__
    return "{}.{}".format(obj.__module__,obj.__name__)

def bases(obj,level=0,tab=4):
    # 打印对象的基类
    if not obj.__class__==type:obj=obj.__class__
    if obj.__bases__:
        if level:print(' '*(level*tab),end='')
        print(*obj.__bases__,sep=',')
        for cls in obj.__bases__:
            bases(cls,level,tab)

_trans_table=str.maketrans("\n\t","  ") # 替换特殊字符为空格
def shortrepr(obj,maxlength=MAXLENGTH,repr_func=None):
    if repr_func is None:repr_func = repr
    result=repr_func(obj).translate(_trans_table)
    if len(result)>maxlength:
        return result[:maxlength]+"..."
    return result

def describe(obj,level=0,maxlevel=1,tab=4,verbose=False,file=None):
    '''"Describe" an object by printing its attributes.
Parameters:
maxlevel: The number of levels to print the object's attributes.
tab: The number of spaces for indentation, default is 4.
verbose: A boolean value indicating whether to print special methods (e.g., __init__).
file: A file-like object for printing output.
'''
    if file is None:file=sys.stdout
    if level==maxlevel:
        result=repr(obj)
        if result.startswith('[') or result.startswith('{'):pprint(result)
        else:print(result,file=file)
    elif level>maxlevel:raise ValueError(
        "Argument level is larger than maxlevel")
    else:
        print(shortrepr(obj)+': ',file=file)
        if type(obj) is type:
            print("Base classes of the object:",file=file)
            bases(obj,level+1,tab)
            print(file=file)
        for attr in dir(obj):
            if verbose or not attr.startswith("_"):
                print(' '*tab*(level+1)+attr+': ',end='',file=file)
                try:
                    if not attr in _ignore_names:
                        describe(getattr(obj,attr),level+1,maxlevel,
                                tab,verbose,file)
                    else:print(shortrepr(getattr(obj,attr)),file=file)
                except AttributeError:
                    print("<AttributeError!>",file=file)

desc=describe #别名

# 导入其他子模块中的函数和类
try:
    from pyobject.browser import browse
    __all__.append("browse")
# SystemError: 修复Python 3.4下的bug
except (ImportError,SystemError):warn("Failed to import module pyobject.browser.")
try:
    from pyobject.search import make_list,make_iter,search #,test_make_list,test_search
    __all__.extend(["make_list","make_iter","search"])
# 同上
except (ImportError,SystemError):warn("Failed to import pyobject.search.")

try:
    from pyobject.code import Code
    __all__.append("Code")
except (ImportError,SystemError):warn("Failed to import pyobject.code.")
try:
    from pyobject.pyobj_extension import *
    __all__.extend(["convptr","py_incref","py_decref","getrealrefcount",
                    "setrefcount","list_in","getrefcount_nogil","setrefcount_nogil",
                    "get_type_flag","set_type_flag","set_type_base","set_type_bases",
                    "set_type_mro","get_type_subclasses","set_type_subclasses",
                    "set_type_subclasses_by_cls"])
except ImportError:warn("Failed to import pyobject.pyobj_extension.")
try:
    from pyobject.objproxy import DynObj,ObjChain,ProxiedObj
    __all__.extend(["DynObj","ObjChain","ProxiedObj"])
except (ImportError, SyntaxError):
    warn("Failed to import pyobject.objproxy.") # Python 3.5及以下不支持f-string，无法使用objproxy库

def desc_demo():
    try:
        describe(type,verbose=True)
    except BaseException as err:
        print("STOPPED!",file=sys.stderr)
        if type(err) is not KeyboardInterrupt:raise

if __name__=="__main__":desc_demo()
