import sys
import re
from django.core.exceptions import ImproperlyConfigured

from django.core.urlresolvers import RegexURLPattern, RegexURLResolver
from django.core.management.base import BaseCommand
# from django.utils import simplejson
import json as simplejson
# from django.utils.datastructures import SortedDict
from collections import OrderedDict as SortedDict
from django.conf import settings



RE_KWARG = re.compile(r"(\(\?P\<(.*?)\>.*?\))") #Pattern for recongnizing named parameters in urls
RE_ARG = re.compile(r"(\(.*?\))") #Pattern for recognizing unnamed url parameters
    

class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Create urls.js file by parsing all of the urlpatterns in the root urls.py file
        """
        try:
            URLS_JS_GENERATED_FILE = getattr(settings, 'URLS_JS_GENERATED_FILE')
        except:
            raise ImproperlyConfigured('You should provide URLS_JS_GENERATED_FILE setting.')

        js_patterns = SortedDict()
        print("Generating Javascript urls file %s" % URLS_JS_GENERATED_FILE)
        Command.handle_url_module(js_patterns, settings.ROOT_URLCONF)
        #output to the file
        urls_file = open(URLS_JS_GENERATED_FILE, "w")
        urls_file.write("dutils.conf.urls = ")
        simplejson.dump(js_patterns, urls_file)
        print("Done generating Javascript urls file %s" % URLS_JS_GENERATED_FILE)
    
    @staticmethod
    def handle_url_module(js_patterns, module_name, prefix=""):
        """
        Load the module and output all of the patterns
        Recurse on the included modules
        """
        if isinstance(module_name, str):
            __import__(module_name)
            root_urls = sys.modules[module_name]
            patterns = root_urls.urlpatterns
        else:
            root_urls = module_name
            patterns = root_urls

        if not isinstance(patterns, list):
            return

        for pattern in patterns:
            if issubclass(pattern.__class__, RegexURLPattern):
                if pattern.name:
                    full_url = prefix + pattern.regex.pattern
                    # Fix django-rest-framework addition
                    full_url = full_url.replace('\\.(?P<format>[a-z0-9]+)/?', '/')
                    for chr in ["^","$"]:
                        full_url = full_url.replace(chr, "")
                    #handle kwargs, args
                    kwarg_matches = RE_KWARG.findall(full_url)
                    if kwarg_matches:
                        for el in kwarg_matches:
                            #prepare the output for JS resolver
                            full_url = full_url.replace(el[0], "<%s>" % el[1])
                    #after processing all kwargs try args
                    args_matches = RE_ARG.findall(full_url)
                    if args_matches:
                        for el in args_matches:
                            full_url = full_url.replace(el, "<>")#replace by a empty parameter name
                    js_patterns[pattern.name] = "/" + full_url
            elif issubclass(pattern.__class__, RegexURLResolver):
                if pattern.urlconf_name:
                    Command.handle_url_module(js_patterns, pattern.urlconf_name, prefix=pattern.regex.pattern)
