from __future__ import unicode_literals

from django.conf import settings
from django.forms.widgets import Input
import json


class JsTreeWidget(Input):
    template_name = "jstree/jstree.html"
    url = None

    def get_context(self, name, value, attrs):
        context = super(JsTreeWidget, self).get_context(name, value, attrs)
        context.update({
            'url': self.url,
        })
        return context

    def __init__(self, url, result_hidden=False, attrs=None):
        """
        JsTreePathFile Doc usage
        :param url: URL will serve AJAX results. See https://www.jstree.com/docs/json/
        :param result_hidden: Hide readonly input which contains selected result
        :param attrs: Override django widget HTML attributes
        """
        super(JsTreeWidget, self).__init__(attrs=attrs)
        self.url = url

        if result_hidden:
            self.input_type = 'hidden'

        else:
            self.input_type = 'text'
            # custom widget if not specified in attrs
            self.attrs.setdefault('readonly', True)
            self.attrs.setdefault('required', True)
            self.attrs.setdefault('max_length', 255)
            self.attrs.setdefault('size', 100)

    def set_url(self, url):
        self.attrs['url'] = url
        self.url = url

    def value_from_datadict(self, data, files, name):
        return json.loads(data[name])

    class Media:
        css = {
            'all': (
                'jstree/css/themes/default/style.css',
            )
        }
        js = (
            'jstree/js/jstree{}.js'.format('.min' if settings.DEBUG else ''),
        )
