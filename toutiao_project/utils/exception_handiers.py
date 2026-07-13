from utils.exception import http_exception_handler, integrity_error_handler,sqlalchemy_error_handler,general_exception_handler
from fastapi.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError,SQLAlchemyError


def register_exception_handlers(app):
    #注册全局异常处理：子类在前，父类在后；具体在前，抽象在后
    #全局注册异常处理器：app.add_exception_handler(异常类，异常处理函数名)
    app.add_exception_handler(HTTPException,http_exception_handler) #业务异常
    app.add_exception_handler(IntegrityError,integrity_error_handler) #数据完整性约束
    app.add_exception_handler(SQLAlchemyError,sqlalchemy_error_handler) #数据库异常
    app.add_exception_handler(Exception,general_exception_handler) #未捕获的异常