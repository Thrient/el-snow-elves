import requests

class Url:
    def __init__(self, url):
        self.urls = [url]
        self.loadTXT()

    def findBestUrl(self):
        for url in self.urls:
            code = self.testUrl(url)
            if code == 200:
                return url
        return None

    @staticmethod
    def testUrl(url, timeout=5):
        try:
            # 发送HEAD请求，跟随重定向
            response = requests.head(
                url,
                timeout=timeout,
                allow_redirects=True,
                verify=False
            )
            return response.status_code  # 成功返回状态码（200、3xx重定向最终状态码等）

        # 捕获域名解析失败（核心异常）
        except requests.exceptions.ConnectionError as e:
            print(e)
            return None
        except requests.exceptions.Timeout as e:
            print(e)
            return None

    def loadTXT(self):
        response = requests.get(
            "https://api.gitcode.com/api/v5/repos/weixin_58151590/elves/raw/url.txt?access_token=svzwvRF9ta7WHetWiu4Ff1qE",
            timeout=10
        )
        self.urls += [line.strip() for line in response.text.splitlines() if line.strip()]
