# -*- coding: utf-8 -*-
import random
import json
import time

import scrapy
from scrapy.http import FormRequest
from scrapy.http import Request
from scrapy.utils.response import open_in_browser
from scrapy import signals
from pydispatch import dispatcher
import pandas as pd

from ..items import DigitEyesItem


class DigiteyesSpiderSpider(scrapy.Spider):
    name = 'digiteyes'
    # allowed_domains = ['http://www.digit-eyes.com']
    api_url = "https://www.digit-eyes.com/cgi-bin/digiteyes.cgi/"
    barcodes = pd.read_excel(io="Barcodes.xlsx")['barcode']
    logins_df = pd.read_csv("logins.csv")
    REQ_PER_LOGIN = 450

    def __init__(self, sku_range="15-19", *args, **kwargs):
        super(DigiteyesSpiderSpider, self).__init__(*args, **kwargs)
        dispatcher.connect(self.spider_closed, signals.spider_closed)
        self.start_index = int(sku_range.split('-')[0])
        self.end_index = int(sku_range.split('-')[1])
        assert self.start_index < self.end_index, "start of range should be less than end"

    def spider_closed(self, spider):
        """
        Save the logins file with additional info about usage.
        """
        self.logger.debug("Saving modified logins file to logins.csv")
        self.logins_df.to_csv("logins.csv", index=False)

    def start_requests(self):
        """
        Setup sessions for multiple accounts and call create account method
        """
        num_items = self.end_index - self.start_index
        login_bins = num_items // self.REQ_PER_LOGIN
        remaining_reqs = num_items - (login_bins*self.REQ_PER_LOGIN)
        if remaining_reqs > 0:
            login_bins += 1

        for i in range(login_bins):
            temp_start = self.start_index + (self.REQ_PER_LOGIN-1)*(i)
            temp_end = self.start_index + (self.REQ_PER_LOGIN-1)*(i+1)
            if temp_end > self.end_index:
                # plus one to make the last item range inclusive
                temp_end = self.end_index + 1
            item_range = str(temp_start)+'-'+str(temp_end)

            yield Request(self.api_url,
                          callback=self.create_account,
                          dont_filter=True,
                          meta={"cookiejar": i,
                                "sku_range": item_range,
                                "login_account_num": i})

    def create_account(self, response):
        """
        This method will create an account, if not existed, 
        otherwise account will be logged in.
        """
        login_account_num = response.meta["login_account_num"]
        self.logins_df.loc[login_account_num,
                           "status"] = response.meta["sku_range"]
        self.logins_df.loc[login_account_num, "dated"] = time.asctime()
        form_data = {
            "upcCode": "",
            "realName": self.logins_df.loc[login_account_num, "name"],
            "email": self.logins_df.loc[login_account_num, "email"],
            "workPhone": "",
            "passwd": "%A&U$gn=7L",
            "passwd2": "%A&U$gn=7L",
            "question": "Select+a+verification+question",
            "response": "",
            "address": "",
            "address2": "",
            "city": "",
            "state": "",
            "otherstate": "",
            "zip": "",
            "country": "US",
            "apiUser": "2487",
            "action": "Create+Account"
        }
        print(self.logins_df.loc[login_account_num])
        return FormRequest.from_response(response,
                                         formdata=form_data,
                                         callback=self.generate_item_urls,
                                         meta={"cookiejar": response.meta["cookiejar"],
                                               "sku_range": response.meta["sku_range"]})

    def generate_item_urls(self, response):
        # print(response.request.url)
        # open_in_browser(response)

        urls = []
        start = response.meta["sku_range"].split("-")[0]
        end = response.meta["sku_range"].split("-")[-1]
        barcodes_slice = self.barcodes.iloc[int(start): int(end)]

        for b in barcodes_slice:
            urls.append(
                f"http://www.digit-eyes.com/cgi-bin/digiteyes.cgi?action=upcList&upcCode={b}")

        # for url in urls:
        #     yield scrapy.Request(url=url, callback=self.parse_item,
        #                          meta={"cookiejar": response.meta["cookiejar"]})

    def parse_item(self, response):
        item = DigitEyesItem()

        try:
            json_rsp_str = response.css(
                "td.cCol > script:nth-child(2)::text").get()

            json_rsp = json.loads(json_rsp_str)

            item["name"] = json_rsp.get("name")
            item["brand"] = json_rsp["brand"].get("name")
            item["sku"] = json_rsp.get("sku")
            item["description"] = json_rsp.get("description")

            if json_rsp.get("image") != ['']:
                item["image_urls"] = json_rsp.get("image")
            else:
                item["image_urls"] = []

            try:
                if json_rsp["offers"] != "":
                    item["product_url"] = json_rsp["offers"].get("url")
                else:
                    item["product_url"] = ""
            except AttributeError:
                # there might be multiple offers for a product, only getting last one
                item["product_url"] = json_rsp["offers"][-1].get("url")

            yield item

        except TypeError:
            self.logger.error(f"No hit against {response.url}")

        except Exception:
            self.logger.error(f"No hit against {response.url}", exc_info=True)


# scrapy crawl digiteyes -a sku_range=67-71
