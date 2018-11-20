from io import StringIO
from contextlib import ContextDecorator

from django.test import TestCase
from django.contrib.contenttypes.models import ContentType

from translations.management.commands.synctranslations import Command

from sample.models import Continent, Country, City
from sample.utils import create_samples


class override_tmeta(ContextDecorator):
    """Override the TranslatableMeta for testing."""

    def __init__(self, model, fields=None):
        self.model = model
        if fields is None:
            self.fields = []
        else:
            self.fields = fields

    def __enter__(self):
        self.old_tmeta = getattr(self.model, 'TranslatableMeta')

        class new_tmeta:
            fields = self.fields

        setattr(self.model, 'TranslatableMeta', new_tmeta)

        if hasattr(self.model, '_cached_translatable_fields'):
            delattr(self.model, '_cached_translatable_fields')
        if hasattr(self.model, '_cached_translatable_fields_names'):
            delattr(self.model, '_cached_translatable_fields_names')

    def __exit__(self, exc_type, exc_value, traceback):
        setattr(self.model, 'TranslatableMeta', self.old_tmeta)

        if hasattr(self.model, '_cached_translatable_fields'):
            delattr(self.model, '_cached_translatable_fields')
        if hasattr(self.model, '_cached_translatable_fields_names'):
            delattr(self.model, '_cached_translatable_fields_names')


class CommandTest(TestCase):
    """Tests for `Command`."""

    def test_execute(self):
        out = StringIO()
        command = Command(stdout=out)
        command.run_from_argv(['manage.py', 'synctranslations'])

        self.assertIs(
            hasattr(command, 'stdin'),
            True
        )

    def test_get_content_types_no_app_labels(self):
        command = Command()
        content_types = command.get_content_types()

        self.assertListEqual(
            sorted(
                list(content_types.values_list('app_label', 'model')),
                key=lambda x: (x[0], x[1])
            ),
            [
                ('admin', 'logentry'),
                ('auth', 'group'),
                ('auth', 'permission'),
                ('auth', 'user'),
                ('contenttypes', 'contenttype'),
                ('sample', 'city'),
                ('sample', 'continent'),
                ('sample', 'country'),
                ('sample', 'timezone'),
                ('sessions', 'session'),
                ('translations', 'translation'),
            ]
        )

    def test_get_content_types_one_app_label(self):
        command = Command()
        content_types = command.get_content_types('sample')

        self.assertListEqual(
            sorted(
                list(content_types.values_list('app_label', 'model')),
                key=lambda x: (x[0], x[1])
            ),
            [
                ('sample', 'city'),
                ('sample', 'continent'),
                ('sample', 'country'),
                ('sample', 'timezone'),
            ]
        )

    def test_get_content_types_two_app_labels(self):
        command = Command()
        content_types = command.get_content_types('sample', 'translations')

        self.assertListEqual(
            sorted(
                list(content_types.values_list('app_label', 'model')),
                key=lambda x: (x[0], x[1])
            ),
            [
                ('sample', 'city'),
                ('sample', 'continent'),
                ('sample', 'country'),
                ('sample', 'timezone'),
                ('translations', 'translation'),
            ]
        )

    def test_get_content_types_all_app_labels(self):
        command = Command()
        content_types = command.get_content_types(
            'admin', 'auth', 'contenttypes', 'sessions',
            'sample', 'translations'
        )

        self.assertListEqual(
            sorted(
                list(content_types.values_list('app_label', 'model')),
                key=lambda x: (x[0], x[1])
            ),
            [
                ('admin', 'logentry'),
                ('auth', 'group'),
                ('auth', 'permission'),
                ('auth', 'user'),
                ('contenttypes', 'contenttype'),
                ('sample', 'city'),
                ('sample', 'continent'),
                ('sample', 'country'),
                ('sample', 'timezone'),
                ('sessions', 'session'),
                ('translations', 'translation'),
            ]
        )

    def test_get_obsolete_translations_no_content_types_no_fields(self):
        create_samples(
            continent_names=['europe', 'asia'],
            country_names=['germany', 'south korea'],
            city_names=['cologne', 'seoul'],
            continent_fields=['name', 'denonym'],
            country_fields=['name', 'denonym'],
            city_fields=['name', 'denonym'],
            langs=['de', 'tr']
        )

        command = Command()
        obsolete_translations = command.get_obsolete_translations()

        self.assertQuerysetEqual(
            obsolete_translations.order_by('id'),
            []
        )

    def test_get_obsolete_translations_one_content_type_no_fields(self):
        create_samples(
            continent_names=['europe', 'asia'],
            country_names=['germany', 'south korea'],
            city_names=['cologne', 'seoul'],
            continent_fields=['name', 'denonym'],
            country_fields=['name', 'denonym'],
            city_fields=['name', 'denonym'],
            langs=['de', 'tr']
        )

        command = Command()
        obsolete_translations = command.get_obsolete_translations(
            *list(ContentType.objects.get_for_models(Continent).values())
        )

        self.assertQuerysetEqual(
            obsolete_translations.order_by('id'),
            []
        )

    def test_get_obsolete_translations_two_content_types_no_fields(self):
        create_samples(
            continent_names=['europe', 'asia'],
            country_names=['germany', 'south korea'],
            city_names=['cologne', 'seoul'],
            continent_fields=['name', 'denonym'],
            country_fields=['name', 'denonym'],
            city_fields=['name', 'denonym'],
            langs=['de', 'tr']
        )

        command = Command()
        obsolete_translations = command.get_obsolete_translations(
            *list(ContentType.objects.get_for_models(Continent, Country).values())
        )

        self.assertQuerysetEqual(
            obsolete_translations.order_by('id'),
            []
        )

    def test_get_obsolete_translations_all_content_types_no_fields(self):
        create_samples(
            continent_names=['europe', 'asia'],
            country_names=['germany', 'south korea'],
            city_names=['cologne', 'seoul'],
            continent_fields=['name', 'denonym'],
            country_fields=['name', 'denonym'],
            city_fields=['name', 'denonym'],
            langs=['de', 'tr']
        )

        command = Command()
        obsolete_translations = command.get_obsolete_translations(
            *list(ContentType.objects.all())
        )

        self.assertQuerysetEqual(
            obsolete_translations.order_by('id'),
            []
        )

    @override_tmeta(Continent, fields=['name'])
    @override_tmeta(Country, fields=['name'])
    @override_tmeta(City, fields=['name'])
    def test_get_obsolete_translations_no_content_types_one_field(self):
        create_samples(
            continent_names=['europe', 'asia'],
            country_names=['germany', 'south korea'],
            city_names=['cologne', 'seoul'],
            continent_fields=['name', 'denonym'],
            country_fields=['name', 'denonym'],
            city_fields=['name', 'denonym'],
            langs=['de', 'tr']
        )

        command = Command()
        obsolete_translations = command.get_obsolete_translations()

        self.assertQuerysetEqual(
            obsolete_translations.order_by('id'),
            []
        )

    @override_tmeta(Continent, fields=['name'])
    @override_tmeta(Country, fields=['name'])
    @override_tmeta(City, fields=['name'])
    def test_get_obsolete_translations_one_content_type_one_field(self):
        create_samples(
            continent_names=['europe', 'asia'],
            country_names=['germany', 'south korea'],
            city_names=['cologne', 'seoul'],
            continent_fields=['name', 'denonym'],
            country_fields=['name', 'denonym'],
            city_fields=['name', 'denonym'],
            langs=['de', 'tr']
        )

        command = Command()
        obsolete_translations = command.get_obsolete_translations(
            *list(ContentType.objects.get_for_models(Continent).values())
        )

        self.assertQuerysetEqual(
            obsolete_translations.order_by('id'),
            [
                '<Translation: European: Europäisch>',
                '<Translation: European: Avrupalı>',
                '<Translation: Asian: Asiatisch>',
                '<Translation: Asian: Asyalı>'
            ]
        )

    @override_tmeta(Continent, fields=['name'])
    @override_tmeta(Country, fields=['name'])
    @override_tmeta(City, fields=['name'])
    def test_get_obsolete_translations_two_content_types_one_field(self):
        create_samples(
            continent_names=['europe', 'asia'],
            country_names=['germany', 'south korea'],
            city_names=['cologne', 'seoul'],
            continent_fields=['name', 'denonym'],
            country_fields=['name', 'denonym'],
            city_fields=['name', 'denonym'],
            langs=['de', 'tr']
        )

        command = Command()
        obsolete_translations = command.get_obsolete_translations(
            *list(ContentType.objects.get_for_models(Continent, Country).values())
        )

        self.assertQuerysetEqual(
            obsolete_translations.order_by('id'),
            [
                '<Translation: European: Europäisch>',
                '<Translation: European: Avrupalı>',
                '<Translation: German: Deutsche>',
                '<Translation: German: Almanca>',
                '<Translation: Asian: Asiatisch>',
                '<Translation: Asian: Asyalı>',
                '<Translation: South Korean: Südkoreanisch>',
                '<Translation: South Korean: Güney Korelı>'
            ]
        )

    @override_tmeta(Continent, fields=['name'])
    @override_tmeta(Country, fields=['name'])
    @override_tmeta(City, fields=['name'])
    def test_get_obsolete_translations_all_content_types_one_field(self):
        create_samples(
            continent_names=['europe', 'asia'],
            country_names=['germany', 'south korea'],
            city_names=['cologne', 'seoul'],
            continent_fields=['name', 'denonym'],
            country_fields=['name', 'denonym'],
            city_fields=['name', 'denonym'],
            langs=['de', 'tr']
        )

        command = Command()
        obsolete_translations = command.get_obsolete_translations(
            *list(ContentType.objects.all())
        )

        self.assertQuerysetEqual(
            obsolete_translations.order_by('id'),
            [
                '<Translation: European: Europäisch>',
                '<Translation: European: Avrupalı>',
                '<Translation: German: Deutsche>',
                '<Translation: German: Almanca>',
                '<Translation: Cologner: Kölner>',
                '<Translation: Cologner: Kolnlı>',
                '<Translation: Asian: Asiatisch>',
                '<Translation: Asian: Asyalı>',
                '<Translation: South Korean: Südkoreanisch>',
                '<Translation: South Korean: Güney Korelı>',
                '<Translation: Seouler: Seüler>',
                '<Translation: Seouler: Seullı>'
            ]
        )
