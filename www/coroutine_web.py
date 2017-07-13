'''
defined asyncio web model.
'''

from urllib import parse
import functools
import inspect
import logging;logging.basicConfig(level=logging.INFO)
import asyncio
from aiohttp import web
from api_exception import APIError
import os


def request_decorator(path, method):
    '''
    request decorator.
    add attr:method,path.
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = method
        wrapper.__path__ = path
        return wrapper
    return decorator
get = functools.partial(request_decorator, method='GET')
post = functools.partial(request_decorator, method='POST')


def has_var_kw_args(func):
    params = inspect.signature(func).parameters
    for name, param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True


def get_named_kw_args(func):
    args = []
    params = inspect.signature(func).parameters
    for name, para in params.items():
        if para.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)
    return tuple(args)


def has_request_args(func):
    found = False
    params = inspect.signature(func).parameters
    for name, para in params.items():
        if name == 'request':
            found = True
        if found and para.kind != inspect.Parameter.KEYWORD_ONLY and para.kind != inspect.Parameter.VAR_KEYWORD and para.kind != inspect.Parameter.VAR_POSITIONAL:
            raise ValueError(
                'request parameter must be the last named parameter in function: %s' % func.__name__)
    return found


def get_required_kw_args(func):
    args = []
    params = inspect.signature(func).parameters
    for name, para in params.items():
        if para.kind == inspect.Parameter.KEYWORD_ONLY and para.default == inspect.Parameter.empty:
            args.append(name)
    return tuple(args)


class RequestHandler(object):

    def __init__(self, app, func):
        if not inspect.iscoroutinefunction(func) and not inspect.isgeneratorfunction(func):
            func = asyncio.coroutine(func)
        self._app = app
        self._func = func
        self._has_var_kw_args = has_var_kw_args(func)
        self._named_kw_args = get_named_kw_args(func)
        self._has_request_args = has_request_args(func)
        self._required_kw_args = get_required_kw_args(func)

    async def __call__(self, request):
        kw = {}
        if self._has_var_kw_args or self._named_kw_args:
            if request.method == 'GET':
                qs = request.query_string
                for k, v in parse.parse_qs(qs, True).items():
                    kw[k] = v[0]
            if request.method == 'post':
                if not request.content_type:
                    return web.HTTPBadRequest('Missing content type.')
                ct = request.content_type.lower()
                if ct.startwith('application/json'):
                    params = await request.post()
                    if not isinstance(params, dict):
                        return web.HTTPBadRequest('JSON body must be object...')
                    kw = params
                if ct.startwith('application/x-www-form-urlencoded') or ct.startwith('multipart/form-data'):
                    params = await request.post()
                    kw = dict(**params)
                else:
                    return web.HTTPBadRequest('Unknow content type:<%s>' % request.content_type)
        for key, value in request.match_info.items():
            if key in kw:
                logging.warning(
                    'Duplicate name in named arg and kw arg:<%s>' % key)
            kw[key] = value
        if not self._has_var_kw_args and self._named_kw_args:
            copy = {}
            for k, v in kw:
                if k in self._named_kw_args:
                    copy[k] = v
            kw = copy
        if self._has_request_args:
            kw['request'] = request
        if self._required_kw_args:
            for name in self._required_kw_args:
                if name not in kw:
                    return web.HTTPBadRequest('Missing argument:<%s>' % name)

        logging.info('Call with arguments:%s' % str(kw))
        try:
            result = await self._func(**kw)
            return result
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)


def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path)
    logging.info('add static %s => %s' % ('/static/', path))


def add_route(app, func):
    method = getattr(func, '__method__', None)
    path = getattr(func, '__path__', None)
    if method == None or path == None:
        raise ValueError('@get or @post not defined for <%s>' % str(func))
    logging.info('add route:%s %s =>%s(%s)' % (
        method, path, func.__name__, ','.join(inspect.signature(func).parameters.keys())))
    app.router.add_route(method, path, RequestHandler(app, func))


def add_routes(app, module_name):
    '''
    from a module file import request handler function.
    if module_name is like 'A.B',then it means:from A directory import B file.
    else import all function from A file.
    '''
    index = module_name.rfind('.')
    if index == -1:
        mod = __import__(module_name, globals(), locals(), [])
    else:
        name = module_name[index + 1:]
        mod = getattr(__import__(
            module_name[:index], globals(), locals(), [name]), name)
    for attr in dir(mod):
        if attr.startwith('__'):
            continue
        fn = getattr(mod, attr)
        if callable(attr):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__path__', None)
            if method and path:
                add_route(app, fn)
