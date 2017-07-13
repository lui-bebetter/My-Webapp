'''
do configuration.
'''
__author__='luibebetter'

import config_default

class Dict(dict):
    def __init__(self,names=(),values=(),**kw):
        super(Dict,self).__init__(**kw)
        for k,v in zip(names,values):
            self[k]=v
    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError('%s has no attribute %s'%(self.__class__.__name__,key))
    def __setattr__(self,key,value):
        self[key]=value

def toDict(d):
    D=Dict()
    for k,v in d.items():
        if isinstance(v,dict):
            D[k]=toDict(v)
        else:
            D[k]=v
    return D



def merge(default,override):
    '''
    merge configurations.
    '''
    result={}
    for k,v in default.items():
        if k in override:
            if isinstance(v,dict):
                merge(v,override.get(k))
            else:
                result[k]=override[k]
        else:
            result[k]=v
    for k,v in override.items():
        if k not in default:
            result[k]=v
    return result        

configs=config_default.configs
try:
    import config_override
    configs=merge(configs,config_override.configs)
except ImportError:
    pass

configs=toDict(configs)
