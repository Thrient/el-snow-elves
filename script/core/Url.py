import logging
import time

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError, TooManyRedirects, InvalidURL

logger = logging.getLogger(__name__)


class Url:
    def __init__(self, primary_url: str, txt_url: str = None):
        self.primary_url = primary_url.rstrip('/')
        self.txt_url = txt_url or (
            "https://api.gitcode.com/api/v5/repos/weixin_58151590/elves/raw/url.txt"
            "?access_token=svzwvRF9ta7WHetWiu4Ff1qE"
        )
        self.urls = []
        self._load_urls()

    def _load_urls(self):
        seen = set()
        self.urls.append(self.primary_url)
        seen.add(self.primary_url)

        try:
            response = requests.get(self.txt_url, timeout=10)
            response.raise_for_status()
            for line in response.text.splitlines():
                url = line.strip().rstrip('/')
                if url and url not in seen:
                    self.urls.append(url)
                    seen.add(url)
        except RequestException as e:
            logger.info(f"加载远程 url.txt 失败: {e}")

    @staticmethod
    def measure_latency(url: str, timeout: int = 10) -> tuple[float | None, int | None]:
        """
        测量 URL 延迟（毫秒），返回 (延迟ms, 最终状态码)
        """
        session = requests.Session()

        # 添加 User-Agent 头，避免某些网站拒绝无头请求
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        })

        for method in (session.head, session.get):
            start_time = time.perf_counter()
            try:
                # 正确传递参数的方式：url 作为关键字参数
                # noinspection PyArgumentList
                response = method(
                    url=url,
                    timeout=timeout,
                    allow_redirects=True,
                    verify=False
                )
                elapsed = (time.perf_counter() - start_time) * 1000
                return elapsed, response.status_code
            except Timeout:
                logger.info(f"请求超时: {url}")
                return None, None
            except ConnectionError:
                logger.info(f"连接错误: {url}")
                return None, None
            except TooManyRedirects:
                logger.info(f"重定向过多: {url}")
                return None, None
            except InvalidURL:
                logger.info(f"无效 URL: {url}")
                return None, None
            except RequestException as e:
                if method == session.head:
                    # HEAD 方法失败，继续尝试 GET 方法
                    continue
                else:
                    logger.info(f"请求异常 [{url}]: {e}")
                    return None, None
        return None, None

    def find_best_url_by_latency(self, min_status: int = 200, max_status: int = 299) -> str | None:
        results = []
        logger.info("正在测试各 URL 延迟...")
        logger.info(f"共有 {len(self.urls)} 个 URL 待测试")

        for i, url in enumerate(self.urls, 1):
            logger.info(f"\n测试 URL {i}/{len(self.urls)}: {url}")
            latency, status = self.measure_latency(url)
            if latency is not None and min_status <= status <= max_status:
                logger.info(f"  成功 -> 延迟: {latency:.0f}ms, 状态码: {status}")
                results.append((latency, url))
            else:
                logger.info(f"  失败 -> 状态码: {status if status else '超时/连接失败'}")

        if not results:
            logger.info("\n所有 URL 均不可用")
            return None

        # 按延迟排序，选择最快的
        results.sort(key=lambda x: x[0])

        logger.info("\n" + "=" * 50)
        logger.info("测试结果汇总:")
        for i, (latency, url) in enumerate(results, 1):
            logger.info(f"{i}. {url} -> {latency:.0f}ms")

        best_latency, best_url = results[0]
        logger.info(f"\n最佳 URL: {best_url} (延迟: {best_latency:.0f}ms)")
        return best_url
