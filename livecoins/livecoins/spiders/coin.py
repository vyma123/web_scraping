import scrapy


class CoinSpider(scrapy.Spider):
    name = "coin"
    allowed_domains = ["www.chotot.com"]
    start_urls = ["https://www.chotot.com"]

    def parse(self, response):
        pass
