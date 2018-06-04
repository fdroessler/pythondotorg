import importlib
import inspect
import pprint

from django.apps import apps
from django.core.management import BaseCommand, call_command


class Command(BaseCommand):

    help = 'Create initial data by using factories.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app_label',
            dest='app_label',
            help='Provide an app label to create app specific data (e.g. --app_label boxes)',
            default=False
        )

    def collect_initial_data_functions(self, app_label=None):
        functions = {}
        if app_label:
            app_list = [apps.get_app_config(app_label)]
        else:
            app_list = apps.get_app_configs()
        for app in app_list:
            try:
                factory_module = importlib.import_module('{}.factories'.format(app.name))
            except ImportError:
                continue
            else:
                for name, function in inspect.getmembers(factory_module, inspect.isfunction):
                    if name == 'initial_data':
                        functions[app.name] = function
                        break
        return functions

    def handle(self, *args, **options):
        verbosity = options['verbosity']
        app_label = options['app_label']
        msg = (
            'Note that this command won\'t cleanup the database before '
            'creating new data.\n'
            'Type \'y\' or \'yes\' to continue, \'n\' or \'no\' to cancel: '
        )
        confirm = input(self.style.WARNING(msg))
        if confirm not in ('y', 'yes'):
            return
        if verbosity > 0:
            self.stdout.write('Creating initial data for \'sitetree\'... ', ending='')
        try:
            call_command('loaddata', 'sitetree_menus', '-v0')
        except Exception as exc:
            self.stdout.write(self.style.ERROR('{}: {}'.format(type(exc).__name__, exc)))
        else:
            if verbosity > 0:
                self.stdout.write(self.style.SUCCESS('DONE'))
        functions = self.collect_initial_data_functions(app_label)
        for app_name, function in functions.items():
            if verbosity > 0:
                self.stdout.write('Creating initial data for {!r}... '.format(app_name), ending='')
            try:
                result = function()
            except Exception as exc:
                self.stdout.write(self.style.ERROR('{}: {}'.format(type(exc).__name__, exc)))
                continue
            else:
                if verbosity > 0:
                    self.stdout.write(self.style.SUCCESS('DONE'))
                if verbosity >= 2:
                    pprint.pprint(result)
