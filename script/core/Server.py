import logging
import os
import time
from threading import Thread

from flask import Flask, send_file, request, jsonify


class Server(Thread):
    def __init__(self, url, host, port, debug=False):
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.debug = debug
        self.url = url
        self.app = None
        self._setup_logging()
        self._create_app()

    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.DEBUG if self.debug else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _create_app(self):
        """创建 Flask 应用"""
        self.app = Flask(__name__)

        # MIME 类型映射
        self.mime_types = {
            '.js': 'application/javascript',
            '.mjs': 'application/javascript',
            '.css': 'text/css',
            '.html': 'text/html',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
            '.ttf': 'font/ttf',
            '.eot': 'application/vnd.ms-fontobject'
        }

        self._setup_routes()

    def _setup_routes(self):
        """设置路由"""

        @self.app.route('/')
        def index():
            """首页"""
            self.logger.debug('访问首页')
            return self._serve_file('index.html')

        @self.app.route('/<path:filename>')
        def serve_files(filename):
            """静态文件服务"""
            self.logger.debug(f'请求文件: {filename}')
            return self._serve_file(filename)

        @self.app.route('/api/health')
        def health_check():
            """健康检查接口"""
            return jsonify({
                'status': 'healthy',
                'server': 'PyWebViewServer',
                'timestamp': time.time()
            })

        @self.app.errorhandler(404)
        def not_found(error):
            """404 错误处理"""
            self.logger.warning(f'文件未找到: {request.path}')
            return jsonify({'error': 'File not found'}), 404

        @self.app.errorhandler(500)
        def internal_error(error):
            """500 错误处理"""
            self.logger.error(f'服务器错误: {error}')
            return jsonify({'error': 'Internal server error'}), 500

    def _serve_file(self, filename: str):
        """
        服务静态文件

        Args:
            filename: 文件名

        Returns:
            文件响应或404错误
        """
        # 安全检查，防止路径遍历攻击
        safe_path = os.path.normpath(filename)
        if safe_path.startswith('..') or safe_path.startswith('/'):
            self.logger.warning(f'非法路径访问: {filename}')
            return jsonify({'error': 'Invalid path'}), 403

        file_path = os.path.join(self.url, safe_path)

        # 检查文件是否存在
        if not os.path.exists(file_path):
            self.logger.warning(f'文件不存在: {file_path}')
            return jsonify({'error': 'File not found'}), 404

        # 如果是目录，尝试服务 index.html
        if os.path.isdir(file_path):
            index_path = os.path.join(file_path, 'index.html')
            if os.path.exists(index_path):
                file_path = index_path
            else:
                return jsonify({'error': 'Directory listing not allowed'}), 403

        # 获取文件扩展名并设置 MIME 类型
        _, ext = os.path.splitext(file_path)
        mimetype = self.mime_types.get(ext.lower(), 'text/plain')

        self.logger.debug(f'服务文件: {file_path}, MIME: {mimetype}')
        return send_file(file_path, mimetype=mimetype)

    def run(self):
        self.app.run(
            host=self.host,
            port=self.port,
            debug=self.debug,
            use_reloader=False,  # 避免在子线程中重新加载
            threaded=True
        )

