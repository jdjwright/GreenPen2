# coding: utf-8

from __future__ import unicode_literals

from django import forms
from django.http.request import HttpRequest
from django.template import Template
from django.template.context import RequestContext
from django.test import TestCase

from jstree import widgets


class JsTreeWidgetTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        self.url = None
        self.form_rendering = None
        self.template = None
        super(JsTreeWidgetTestCase, self).__init__(*args, **kwargs)

    def get_widget(self, result_hidden=False):
        return widgets.JsTreeWidget(url=self.url, result_hidden=result_hidden)

    def get_form(self, result_hidden=False):
        class MyForm(forms.Form):
            my_field = forms.CharField(label="My Field with é"'(-èè_çà',
                                       widget=self.get_widget(result_hidden=result_hidden))

        return MyForm()

    def render_form(self, result_hidden=False):
        self.form_rendering = self.template.render(
            RequestContext(request=HttpRequest(), dict_={'form': self.get_form(result_hidden=result_hidden), })
        )

    def setUp(self):
        self.url = "/url/to/test/"
        self.template = Template(
            """
            {{ form.media }}
            <form method="POST">
                {% for field in form %}
                    {{ field.label }}: {{ field }}
                {% endfor %}
            </form>
            """
        )
        self.render_form()

    def test_field_ispresent(self):
        self.assertIn('id="id_my_field"', self.form_rendering)

    def test_tree_field_ispresent(self):
        self.assertIn('id="id_my_field-tree"', self.form_rendering)

    def test_css_ispresent(self):
        widget = self.get_widget()
        self.assertIn("{}".format(widget.media['css']), self.form_rendering)

    def test_js_ispresent(self):
        widget = self.get_widget()
        self.assertIn("{}".format(widget.media['js']), self.form_rendering)

    def test_custom_js_ispresent(self):
        self.assertIn('<script type="text/javascript">', self.form_rendering)

    def test_hidden_field_ispresent(self):
        self.render_form(result_hidden=True)
        self.assertIn('<input type="hidden" name="my_field" id="id_my_field"', self.form_rendering)

    def test_url_ispresent(self):
        self.assertIn('{}'.format(self.url), self.form_rendering)
