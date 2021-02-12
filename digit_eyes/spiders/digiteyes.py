import json

import scrapy
import pandas as pd

from ..items import DigitEyesItem


class DigiteyesSpiderSpider(scrapy.Spider):
    name = 'digiteyes'
    # allowed_domains = ['http://www.digit-eyes.com']
    # start_urls = ['http://www.digit-eyes.com/']

    def __init__(self, sku_range="15-19", *args, **kwargs):
        super(DigiteyesSpiderSpider, self).__init__(*args, **kwargs)
        self.start_index = int(sku_range.split('-')[0])
        self.end_index = int(sku_range.split('-')[1])
        assert self.start_index < self.end_index, "start of range should be less than end"

    def get_urls(self, file_path):
        urls = []
        barcodes = pd.read_excel(io=file_path)['barcode']
        barcodes_slice = barcodes.iloc[self.start_index - 1:self.end_index + 1]

        for b in barcodes_slice:
            urls.append(
                f"http://www.digit-eyes.com/cgi-bin/digiteyes.cgi?action=upcList&upcCode={b}")

        return urls

    def start_requests(self):
        # starting urls for scraping
        urls = self.get_urls("Barcodes.xlsx")

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        item = DigitEyesItem()

        # bad_title = 'Digit-Eyes Voice Labeling System'
        # if response.css("title::text").get() != bad_title:

        json_rsp_str = response.css(
            "td.cCol > script:nth-child(2)::text").get()

        if json_rsp_str != None:
            json_rsp = json.loads(json_rsp_str)

            item["name"] = json_rsp.get("name")
            item["brand"] = json_rsp["brand"].get("name")
            item["sku"] = json_rsp.get("sku")
            item["description"] = json_rsp.get("description")

            if json_rsp.get("image") != ['']:
                item["image_urls"] = json_rsp.get("image")
            else:
                item["image_urls"] = None

            try:
                if json_rsp["offers"] != "":
                    item["product_url"] = json_rsp["offers"].get("url")
                else:
                    item["product_url"] = ""
            except AttributeError:
                # there might be multiple offers for a product, only getting last one
                item["product_url"] = json_rsp["offers"][-1].get("url")

            yield item

        else:
            self.logger.error(f"No hit against {response.url}")


# scrapy crawl digiteyes -a sku_range=67-71
