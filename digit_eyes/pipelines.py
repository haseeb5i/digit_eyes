# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import scrapy
from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline


class DigitEyesPipeline:
    def process_item(self, item, spider):
        if item['images'] == []:
            # no image obtained for the item
            raise DropItem
        else:
            del item['images']
            del item['image_urls']

        return item


class CustomImagesPipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
        for image_url in item.get('image_urls', []):
            yield scrapy.Request(image_url, meta={'image_name': item['sku']})

    def file_path(self, request, response=None, info=None, *, item=None):
        return '{}.jpg'.format(request.meta['image_name'])
