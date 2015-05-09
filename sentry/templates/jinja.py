import os
import urlparse

from sentry import config
from jinja2 import FileSystemLoader, Environment


CWD = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(CWD, 'html')
ENV = Environment(loader=FileSystemLoader(html_path))


def get_pf_url():
    pf_prefix = config.get_config('pf_prefix')
    pf_uri = config.get_config('pf_uri')
    pf_url = urlparse.urljoin(pf_prefix, pf_uri)
    return pf_url


def render(template_name, **kwargs):
    template = ENV.get_template(template_name)

    # Constantly inject these arguments to templates
    env = config.get_config('env_name')
    pf_url = get_pf_url()

    kwargs.setdefault(env, env)
    kwargs.setdefault(pf_url, pf_url)

    return template.render(**kwargs)
