#_*_coding:utf-8_*_

import asyncio
import time,uuid
import orm
from orm import Model,String,Integer,Text,Float,Bool

def next_id():
    return '%015d%s000'%(time.time()*1000,uuid.uuid4().hex)

class User(Model):
    def __init__(self,**kw):
        super(User, self).__init__(**kw)

    __table__='users'

    id=String(primary_key=True,default=next_id)
    email=String()
    password=String()
    admin=Bool(default=False)
    name=String()
    image=String(column_type='varchar(500)')
    created_at=Float(default=time.time)

class Blog(Model):
    __table__='blog'

    id=String(primary_key=True,default=next_id)
    user_id=String()
    user_name=String()
    user_image=String(column_type='varchar(500)')
    name=String()
    summary=String(column_type='varchar(200)')
    content=Text()
    created_at=Float(default=time.time)
class Comment(Model):
    __table__='comments'

    id=String(primary_key=True,default=next_id)
    blog_id=String()
    user_id=String()
    user_name= String()
    user_image=String(column_type='varchar(500)')
    content=Text()
    created_at=Float(default=time.time)


'''test'''

'''def test():
    loop=asyncio.get_event_loop()
    loop.run_until_complete(orm.create_pool(loop=loop,user='www-data', password='www-data', db='awesome'))
    u = User(name='Test', email='test@example.com', password='1234567890', image='about:blank')
    loop.run_until_complete(u.save())
    loop.run_until_complete(u.destroy())

test()'''





