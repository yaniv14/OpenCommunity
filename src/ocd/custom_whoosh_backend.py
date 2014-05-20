from __future__ import unicode_literals
from haystack.backends.whoosh_backend import WhooshEngine
from haystack.backends.whoosh_backend import WhooshSearchBackend
from haystack.fields import BooleanField
from django.db.models.loading import get_model
from haystack.constants import ID, DJANGO_CT, DJANGO_ID
from haystack.models import SearchResult
from haystack.utils import get_identifier
from whoosh.writing import AsyncWriter

class MyWhooshSearchBackend(WhooshSearchBackend):
    def update(self, index, iterable, commit=True):
        if not self.setup_complete:
            self.setup()

        self.index = self.index.refresh()
        writer = AsyncWriter(self.index)

        for obj in iterable:
            doc = index.full_prepare(obj)

            # Really make sure it's unicode, because Whoosh won't have it any
            # other way.
            for key in doc:
                doc[key] = self._from_python(doc[key])

            # Document boosts aren't supported in Whoosh 2.5.0+.
            if 'boost' in doc:
                del doc['boost']

            try:
                writer.update_document(**doc)
            except Exception as e:
                if not self.silently_fail:
                    raise

                # We'll log the object identifier but won't include the actual object
                # to avoid the possibility of that generating encoding errors while
                # processing the log message:
                #self.log.error(u"%s while preparing object for update" % e.__class__.__name__, exc_info=True, extra={
                self.log.error(u"%s while preparing object for update" % e.__name__, exc_info=True, extra={
                    "data": {
                        "index": index,
                        "object": get_identifier(obj)
                    }
                })

        if len(iterable) > 0:
            # For now, commit no matter what, as we run into locking issues otherwise.
            writer.commit()

    def _process_results(self, raw_page, highlight=False, query_string='', spelling_query=None, result_class=None):
        from haystack import connections
        results = []

        # It's important to grab the hits first before slicing. Otherwise, this
        # can cause pagination failures.
        hits = len(raw_page)

        if result_class is None:
            result_class = SearchResult

        facets = {}
        spelling_suggestion = None
        unified_index = connections[self.connection_alias].get_unified_index()
        indexed_models = unified_index.get_indexed_models()

        for doc_offset, raw_result in enumerate(raw_page):
            score = raw_page.score(doc_offset) or 0
            app_label, model_name = raw_result[DJANGO_CT].split('.')
            additional_fields = {}
            model = get_model(app_label, model_name)

            if model and model in indexed_models:
                for key, value in raw_result.items():
                    index = unified_index.get_index(model)
                    string_key = str(key)

#                    if string_key in index.fields and hasattr(index.fields[string_key], 'convert'):
                    # Patch this up to exclude BooleanField because it's broken
                    # https://github.com/toastdriven/django-haystack/issues/382
                    if (string_key in index.fields and
                        callable(getattr(index.fields[string_key], 'convert', None)) and
                        not isinstance(index.fields[string_key], BooleanField)):
                        # Special-cased due to the nature of KEYWORD fields.
                        if index.fields[string_key].is_multivalued:
                            if value is None or len(value) is 0:
                                additional_fields[string_key] = []
                            else:
                                additional_fields[string_key] = value.split(',')
                        else:
                            additional_fields[string_key] = index.fields[string_key].convert(value)
                    else:
                        additional_fields[string_key] = self._to_python(value)

                del(additional_fields[DJANGO_CT])
                del(additional_fields[DJANGO_ID])

                if highlight:
                    from whoosh import analysis
                    from whoosh.highlight import highlight, ContextFragmenter, UppercaseFormatter
                    sa = analysis.StemmingAnalyzer()
                    terms = [term.replace('*', '') for term in query_string.split()]

                    additional_fields['highlighted'] = {
                        self.content_field_name: [highlight(additional_fields.get(self.content_field_name), terms, sa, ContextFragmenter(terms), UppercaseFormatter())],
                        }

                result = result_class(app_label, model_name, raw_result[DJANGO_ID], score, **additional_fields)
                results.append(result)
            else:
                hits -= 1

        if self.include_spelling:
            if spelling_query:
                spelling_suggestion = self.create_spelling_suggestion(spelling_query)
            else:
                spelling_suggestion = self.create_spelling_suggestion(query_string)

        return {
            'results': results,
            'hits': hits,
            'facets': facets,
            'spelling_suggestion': spelling_suggestion,
            }


class MyWhooshEngine(WhooshEngine):
    backend = MyWhooshSearchBackend