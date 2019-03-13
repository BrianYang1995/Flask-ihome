# coding:utf-8

from flask import Blueprint, current_app, make_response
from flask_wtf import csrf
html = Blueprint('web_html', __name__)


@html.route("/<re(r'.*'):html_file_name>")
def web_page(html_file_name):
    """提供html文件"""

    # 如果接收 / 说明是主页
    if not html_file_name:
        html_file_name = 'index.html'

    # 如果不是favicon.ico
    if html_file_name != 'favicon.ico':
        html_file_name = 'html/' + html_file_name

    # 返回响应
    resp = make_response(current_app.send_static_file(html_file_name))

    # csrf_token
    csrf_token = csrf.generate_csrf()

    # 写入cookie
    resp.set_cookie('csrf_token', csrf_token)

    return resp