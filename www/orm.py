import asyncio
import aiomysql
import logging
logging.basicConfig(level=logging.INFO)


async def create_pool(loop, **kw):
    logging.info('create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw.get('db', 'test'),
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )


async def select(sql, args, size=None):
    logging.info("excuting SQL:'%s',%s" % (sql, args))
    global __pool
    with (await __pool) as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(sql.replace('?', '%s'), args or ())
        if size:
            result = await cursor.fetchmany(size)
        else:
            result = await cursor.fetchall()
        await cursor.close()
        logging.info('rows returned:%s' % (len(result)))
        return result
'''insert,update,alter'''


async def execute(sql, args):
    logging.info("excuting SQL:'%s',%s" % (sql, args))
    with (await __pool) as conn:
        cursor = await conn.cursor(aiomysql.DictCursor)
        await cursor.execute(sql.replace('?', '%s'), args)
        affected_line = cursor.rowcount
        await cursor.close()
        return affected_line
# loop=asyncio.get_event_loop()
# loop.run_until_complete(create_pool(loop=loop,user='root',password='lui1993nkwuli'))
#loop.run_until_complete(select('select * from user where id=?',('1',)))


def create_args(num):
    args_string = []
    for i in range(num):
        args_string.append('?')
    return ','.join(args_string)


class Field(object):

    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s,%s:%s>' % (self.__class__.__name__, self.column_type, self.name)


class Integer(Field):

    def __init__(self, name=None, column_type='INTERGER', primary_key=False, default=None):
        super(Integer, self).__init__(name, column_type, primary_key, default)


class String(Field):

    def __init__(self, name=None, column_type='VARCHAR(50)', primary_key=False, default=None):
        super(String, self).__init__(name, column_type, primary_key, default)


class Float(Field):

    def __init__(self, name=None, column_type='FLOAT', primary_key=False, default=None):
        super().__init__(name, column_type, primary_key, default)


class Bool(Field):

    def __init__(self, name=None, column_type='Bool', primary_key=False, default=None):
        super(Bool, self).__init__(name, column_type, primary_key, default)


class Text(Field):
    def __init__(self,name=None,column_type='Text',primary_key=False,default=None):
        super(Text,self).__init__(name,column_type,primary_key,default)



class ModelMetaclass(type):

    def __new__(cls, name, bases, attrs):
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)

        table_name = attrs.get('__table__', None) or name
        '''found mapping'''
        primaryKey = None
        fields = []
        mappings = {}
        for key, value in attrs.items():
            if isinstance(value, Field):
                print('found mapping:%s==>%s' % (key, value))
                mappings[key] = value
                if value.primary_key:
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for fields:%s' % key)
                    primaryKey = key
                else:
                    fields.append(key)
        for item in mappings.keys():
            attrs.pop(item)
        if not primaryKey:
            raise RuntimeError('no primaryKey...')
        attrs['__mappings__'] = mappings
        attrs['__primary_key__'] = primaryKey
        attrs['__fields__'] = fields
        attrs['__table__'] = table_name

        '''构造默认的sql语句(非完整，缺少args)'''
        format_fields = list(map(lambda f: "`%s`" %(mappings.get(f).name or f,), fields))
        format_fields.append("`%s`" %(mappings.get(primaryKey).name or primaryKey,))
        #'select fields,primaryKey from table'
        attrs['__select__'] = "select %s from `%s`" % (','.join(format_fields), table_name)

        #'insert into table(fields,primarykey) values(?,?,?)'
        attrs['__insert__'] = 'insert into `%s`(%s) values(%s) ' % (table_name, ','.join(format_fields), create_args(len(format_fields)))

        #'update table set fields=? where primaryKey=?'
        attrs['__update__'] = 'updata `%s` set %s where `%s`=?' %(table_name, ','.join(map(lambda f: '%s=?' %f, format_fields.pop())), mappings[primaryKey].name or primaryKey)

        #'delete from table where primaryKey=?'
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (table_name, mappings[primaryKey].name or primaryKey)
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):

    def __init__(self, **kw):
        super().__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' has no attribute '%s'" %key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)
        
    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if not value:
            if key in self.__mappings__:
                field = self.__mappings__[key]
                if field.default is not None:
                    value = field.default() if callable(field.default) else field.default
                    logging.info('using default value for %s :%s' %(key, value))
                    setattr(self, key, value)
        return value

    '''与数据库操作有关的方法'''

    # 插入一条记录
    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        row = await execute(self.__insert__, args)
        if row != 1:
            logging.warn('failed to insert to record.(affected rows:%s)' % row)

    # 更新记录
    async def update(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rw = await execute(self.__update__, args)
        if rw != 1:
            raise RuntimeError('failed to remove.(affected_line:%s)' % row)
        return row

    async def destroy(self):
        args=[self.getValue(self.__primary_key__)]
        row=await execute(self.__delete__,args)
        if row != 1:
            raise RuntimeError('failed to destroy.(affected_line:%s)' % row)
        return row

    # 删除一条记录
    @classmethod
    async def remove(cls, pk):
        row = await execute(cls.__delete__, [pk])
        if row != 1:
            raise RuntimeError('failed to remove.(affected_line:%s)' % row)
        return row

    # 查找 by primaryKey
    @classmethod
    async def findone(cls, pk):
        '''find by primaryKey'''
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__mappings__[cls.__primary_key__].name or cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    # 查找 By Where
    @classmethod
    async def findwhere(cls, where=None, args=None, **kw):  # where:where后面的条件字符串(没有？) args:seclect语句参数
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args == None:
            args = []
        orderby = kw.get('orderby', None)
        if orderby:
            sql.append('order by')
            sql.append(orderby)
        limit = kw.get('limit', None)
        if limit:
            if isinstance(limit, int):
                sql.append('limit')
                sql.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('limit')
                sql.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await select(','.join(sql), args)
        return [cls(**item) for item in rs]
