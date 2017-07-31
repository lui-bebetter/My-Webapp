'''
URL handler functions.
'''
import asyncio
import logging;logging.basicConfig(level=logging.INFO)
from coroutine_web import get,post
from models import User,Blog,Comment
__author__='luibebetter'


@get('/')
async def index(request):
    logging.info('hello')
    users=await User.findwhere()
    return {
    '__template__':'test.html',
    'users':users
    }
