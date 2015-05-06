import os

from jinja2 import FileSystemLoader, Environment


CWD = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(CWD, 'html')
ENV = Environment(loader=FileSystemLoader(html_path))


def render(template_name, **kwargs):
    template = ENV.get_template(template_name)
    return template.render(**kwargs)
