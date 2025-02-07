import sys
from copy import deepcopy
from math import inf

NoneType=type(None)
class NewNoneType:
    """A new None type designed to replace any objects with practical functionality.
Compared to Python's built-in NoneType, this type can do anything.
It can be added, subtracted, multiplied, called, etc, \
supporting many "magic" methods and interfaces.
However, these methods do nothing and only return a default value.
Examples (partial usage):
>>> none=NewNoneType()
>>> none
>>> print(none)
NewNoneType
>>> none.write()
>>> none.write=1
>>> none.write
1
>>> none+'1'
'1'
>>> none-1
-1
>>> none>0
False
>>> none>=0
True
>>> none<0
False
>>> none<=0
True
>>> none==None
True"""
    def __init__(self):
        self.__items={}
    def __call__(self,*args,**kwargs):
        return type(self)() # 复制一份自身
    def __getattr__(self,name):
        return type(self)()
    def __setattr__(self,name,value):
        self.__dict__[name]=value
    def __str__(self):
        return type(self).__name__
    def __repr__(self):
        return ""

    def __eq__(self,other):
        if isinstance(other,NewNoneType):
            return other.__dict__==self.__dict__ and \
                   other.__items==self.__items
        availbles=(None, 0, "")
        for availble in availbles:
            if other == availble:return True
        return False
    def __ne__(self,other):
        return not self == other
    def __ge__(self,other):
        return other<=0
    def __gt__(self,other):
        return other<0
    def __le__(self,other):
        return other>=0
    def __lt__(self,other):
        return other>0

    def __add__(self,other):
        return other
    def __sub__(self,other):
        return -other
    def __mul__(self,other):
        return type(self)()
    def __truediv__(self,other):
        if other==0:raise ZeroDivisionError
        return type(self)()
    def __floordiv__(self,other):
        if other==0:raise ZeroDivisionError
        return type(self)()
    def __mod__(self, other):
        if other==0:raise ZeroDivisionError
        return type(self)()
    def __pow__(self, other):return 0 ** other
    def __lshift__(self, other):return type(self)()
    def __rshift__(self, other):return type(self)()
    def __and__(self, other):return other
    def __xor__(self, other):return other
    def __or__(self, other):return other

    def __radd__(self,other):
        return other
    def __rsub__(self,other):
        return -other
    def __rmul__(self,other):
        return type(self)()
    def __rtruediv__(self,other):raise ZeroDivisionError
    def __rfloordiv__(self,other):raise ZeroDivisionError
    def __rmod__(self, other):raise ZeroDivisionError
    def __rpow__(self, other):return other ** 0
    def __rlshift__(self, other):return other
    def __rrshift__(self, other):return other
    def __rand__(self, other):return other
    def __rxor__(self, other):return other
    def __ror__(self, other):return other

    def __neg__(self):return type(self)()
    def __abs__(self):return type(self)()
    def __invert__(self):return ~0

    def __int__(self):return 0
    def __float__(self):return 0.0
    def __complex__(self):return complex(0)
    def __bool__(self):return False

    def __len__(self): return len(self.__items)
    def __getitem__(self, key): return self.__items[key]
    def __setitem__(self, key, value): self.__items[key]=value
    def __delitem__(self, key): del self.__items[key]
    def __iter__(self):return iter(self.__items)
    def __contains__(self, item):return False
    def __hash__(self):
        if self.__dict__ or self.__items:
            raise ValueError("use hash() after modifying a newNoneType object")
        return 0

    def __enter__(self): pass
    def __exit__(self, exc_type, exc_value, traceback): pass

class ObjDict:
    "A fake dictionary based on an object's attibutes."
    def __init__(self,obj):
        self.obj=obj
    def __getitem__(self,key):
        return getattr(self.obj,key)
    def __setitem__(self,key,value):
        setattr(self.obj,key,value)
    def __delitem__(self,key):
        delattr(self.obj,key)
    def get(self,key,default):
        return getattr(self.obj,key,default)

    def __iter__(self):
        return dir(self.obj).__iter__()
    def keys(self):
        return dir(self.obj)
    def clear(self):
        for key in self.keys():
            try:
                delattr(self.obj,key)
            except Exception as err:
                print(type(err).__name__+":", err,
                      file=sys.stderr)
    def __str__(self):
        return str(dict(self))

    def __copy__(self):
        return ObjDict(self.obj)
    def __deepcopy__(self,*args):
        newobj=deepcopy(self.obj)
        return ObjDict(newobj)
    def __repr__(self):
        try:
            return "ObjDict(%r)"%self.obj
        except AttributeError: # ObjDict对象没有obj属性时
            return object.__repr__(self)
    def todict(self):
        return dict(self)
    @staticmethod
    def dict_to_obj(dict):
        """>>> d=ObjDict(ObjDict(1)).todict()
>>> ObjDict.dict_to_obj(d)
ObjDict(1)
"""
        obj=object.__new__(dict["__class__"])
        obj.__dict__.update(dict)
        return obj
    # for pickle
    def __getstate__(self):
        return self.obj
    def __setstate__(self,arg):
        self.obj=arg

class Copier:
    "Copy other objects' attributes and mimic their behavior."
    def __init__(self,obj,copy_internal=False,onerror=None):
        """obj: The object to be copied.
copy_internal: Whether to copy magic methods.
onerror: A callback function accepting an exception object \
that will be called when any errors occur."""
        self._source_obj=obj
        for attr in dir(obj):
            if copy_internal or not (attr.startswith("__") 
                    and attr.endswith("__")):
                try:
                    setattr(self,attr,getattr(obj,attr))
                except Exception as err:
                    if onerror is not None:onerror(err)

if __name__=="__main__":
    import doctest
    doctest.testmod() # Ignore failure messages indicating "expected nothing but got <BLANKLINE>"