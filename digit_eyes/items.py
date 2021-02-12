# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DigitEyesItem(scrapy.Item):

    name = scrapy.Field()
    brand = scrapy.Field()
    sku = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()
    description = scrapy.Field()
    product_url = scrapy.Field()
