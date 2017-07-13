'''
async web application.
'''
import asyncio 
import json
from  aiohttp import web
from jinja2 import Environment,FileSystemLoader
import logging;logging.basicConfig(level=logging.INFO)
import orm
import os,time
from datetime import datetime
from coroutine_web import add_static,add_routes

def init_jinja2(app,**kw):
    '''
    initial jinja2 render template.
    '''
    logging.info('initial jinja2...')
    options=dict(
        autoescape = kw.get('autoescape', True),
        block_start_string = kw.get('block_start_string', '{%'),
        block_end_string = kw.get('block_end_string', '%}'),
        variable_start_string = kw.get('variable_start_string', '{{'),
        variable_end_string = kw.get('variable_end_string', '}}'),
        auto_reload = kw.get('auto_reload', True)
    )
    path=kw.get('path',None)
    if  path is None:
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'template')
    logging.info('set jinja2 template path:<%s>'%path)
    env=Environment(loader=FileSystemLoader(path),**options)
    filters=kw.get('filters',None)
    if not filters:
        for name,fn in filters:
            env.filters[name]=fn
    app['__template__']=env

def datetime_filter(t):
    '''
    datetime filter.
    '''
    delta=int(time.time()-t)
    if delta<60:
        return u'1分钟前'
    if delta<3600:
        return u'%s分钟前'%(delta//60)
    if delta<86400:
        return u'%s小时前'%(delta//3600)
    if delta<604800:
        return u'%s天前'%(delta//86400)
    else:
        dt=datetime.fromtimestamp(t)
        return u'%s年%s月%s日'%(dt.year,dt.month,dt.day)


async def logger_factory(app,handler):
    async def logger(request):
        logging.info('Receive request:%s %s'%(request.method,request.path))
        return (await handler(request))
    return logger

async def data_factory(app,handler):
    async def parse_data(request):
        if request.method=='POST':
            ct=request.content_type.lower()
            if ct.startwith('application/json'):
                request.__data__=request.json()
                logging.info('request json:%s'%str(request.__data__))
            if ct.startwith('application/x-www-form-urlencoded') or ct.startwith('multipart/form-data'):
                request.__data__=request.post()
                logging.info('request form:%s'%str(request.__data__))
        return (await handler(request))
    return parse_data

async def response_factory(app,handler):
    async def response(request):
        logging.info('Request response...')
        result=await handler(request)
        if isinstance(result,web.StreamResponse):
            return result
        if isinstance(result,bytes):
            resp=web.Response(body=result)
            resp.content_type='application/octet-stream'
            return resp
        if isinstance(result,str):
            if result.startwith('redirect:'):
                return web.HTTPFound(result[9:])
            resp=web.Response(body=result.encode('utf-8'))
            resp.content_type='text/html;charset=utf-8'
            return resp
        if isinstance(result,dict):
            template=result.get('__template__',None)
            if not template:
                resp=web.Response(body=json.dumps(result,ensure_ascii=False,default=lambda o:o.__dict__).encode('utf-8'))
                resp.content_type='application/json;charset=utf-8'
                return resp
            else:
                resp=web.Response(body=app['__template__'].get_template(template).render(**result).encode('utf-8'))
                resp.content_type='text/html;charset=utf-8'
                return resp
        if isinstance(result,int) and result >=100 and result <600:
            return web.Response(result)
        if isinstance(result,tuple) and len(result)==2:
            t,m=result
            if isinstance(t,int) and t>=100 and t<600:
                return web.Response(t,str(m))
        #default
        resp=web.Response(body=str(result).encode('utf-8'))
        resp.content_type='text/plain;charset=utf-8'
        return resp
    return response

async def init(loop):
    await orm.create_pool(loop=loop,user='www-data',password='www-data',db='awesome')
    app=web.Application(loop=loop,middlewares=[response_factory,data_factory,logger_factory])
    init_jinja2(app,filters=dict(datetime=datetime_filter))
    add_static(app)
    add_routes(app,'handlers')
    srv=await loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv


loop=asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()

