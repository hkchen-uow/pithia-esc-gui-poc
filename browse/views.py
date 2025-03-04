from django.urls import reverse
from rdflib import URIRef
from rdflib.resource import Resource
from rdflib.namespace import _SKOS
from common import mongodb_models
from django.shortcuts import render
from bson.objectid import ObjectId
from django.http import HttpResponseNotFound
from django.views.generic import TemplateView

from search.ontology_helpers import ONTOLOGY_SERVER_BASE_URL
from search.helpers import remove_underscore_from_id_attribute
from search.ontology_helpers import create_dictionary_from_pithia_ontology_component, get_graph_of_pithia_ontology_component
from search.views import get_parents_of_registered_ontology_terms, get_registered_computation_types, get_registered_features_of_interest, get_registered_instrument_types, get_registered_measurands, get_registered_observed_properties, get_registered_phenomenons

# Create your views here.
def index(request):
    return render(request, 'browse/index.html', {
        'title': 'Browse'
    })

def resources(request):
    return render(request, 'browse/resources.html', {
        'title': 'Browse Resources'
    })

def schemas(request):
    return render(request, 'browse/schemas.html', {
        'title': 'Browse Schemas'
    })

def ontology(request):
    return render(request, 'browse/ontology.html', {
        'title': 'Browse PITHIA Ontology'
    })

def _split_camel_case(string):
    current_string = string[0]
    string_split = []
    for c in string[1:]:
        if c.isupper():
            string_split.append(current_string)
            current_string = c
        else:
            current_string += c
    string_split.append(current_string)
    return string_split

def ontology_category_terms_list(request, category):
    title = ' '.join(_split_camel_case(category)).title()
    if category.lower() == 'crs':
        title = 'Co-ordinate Reference System'
    elif category.lower() == 'verticalcrs':
        title = 'Vertical Co-ordinate Reference System'
    title += ' Terms'
    return render(request, 'browse/ontology_category_terms_list.html', {
        'category': category,
        'title': title
    })

def ontology_category_terms_list_only(request, category):
    dictionary = create_dictionary_from_pithia_ontology_component(category)
    registered_ontology_terms = []
    parents_of_registered_ontology_terms = []
    if category.lower() == 'observedproperty':
        registered_ontology_terms = get_registered_observed_properties()
        parents_of_registered_ontology_terms = get_parents_of_registered_ontology_terms(registered_ontology_terms, category, None, [])
    elif category.lower() == 'featureofinterest':
        registered_observed_property_ids = get_registered_observed_properties()
        registered_ontology_terms = get_registered_features_of_interest(registered_observed_property_ids)
        parents_of_registered_ontology_terms = get_parents_of_registered_ontology_terms(registered_ontology_terms, category, None, [])
    elif category.lower() == 'instrumenttype':
        registered_ontology_terms = get_registered_instrument_types()
        parents_of_registered_ontology_terms = get_parents_of_registered_ontology_terms(registered_ontology_terms, category, None, [])
    elif category.lower() == 'computationtype':
        registered_ontology_terms = get_registered_computation_types()
        parents_of_registered_ontology_terms = get_parents_of_registered_ontology_terms(registered_ontology_terms, category, None, [])
    elif category.lower() == 'phenomenon':
        registered_observed_property_ids = get_registered_observed_properties()
        registered_ontology_terms = get_registered_phenomenons(registered_observed_property_ids)
        parents_of_registered_ontology_terms = get_parents_of_registered_ontology_terms(registered_ontology_terms, category, None, [])
    elif category.lower() == 'measurand':
        registered_observed_property_ids = get_registered_observed_properties()
        registered_ontology_terms = get_registered_measurands(registered_observed_property_ids)
        parents_of_registered_ontology_terms = get_parents_of_registered_ontology_terms(registered_ontology_terms, category, None, [])
    return render(request, 'browse/ontology_tree_template_outer.html', {
        'dictionary': dictionary,
        'category': category,
        'registered_ontology_terms': registered_ontology_terms,
        'parents_of_registered_ontology_terms': parents_of_registered_ontology_terms,
    })

def _remove_namespace_prefix_from_predicate(p):
    p_identifier_no_prefix = p.identifier.split('#')[-1]
    if len(p.identifier.split('#')) == 1:
        p_identifier_no_prefix = p.identifier.split('/')[-1]
    return p_identifier_no_prefix

def ontology_term_detail(request, category, term_id):
    g = get_graph_of_pithia_ontology_component(category)
    SKOS = _SKOS.SKOS
    resource = None
    resource_uriref = URIRef(f'{ONTOLOGY_SERVER_BASE_URL}{category}/{term_id}')
    triples = list(g.triples((None, SKOS.member, resource_uriref)))
    if len(triples) > 0:
        resource = Resource(g, triples[0][2])
    if resource is None:
        return HttpResponseNotFound(f'Details for the ontology term ID <b>"{term_id}"</b> were not found.')
    resource_predicates_no_prefix = list(set(map(_remove_namespace_prefix_from_predicate, resource.predicates())))
    # Turn resource into a dictionary for easier usage
    resource_dictionary = {}
    resource_predicates_readable = {}
    for p in resource.predicates():
        p_identifier_no_prefix = p.identifier.split('#')[-1]
        if len(p.identifier.split('#')) == 1:
            p_identifier_no_prefix = p.identifier.split('/')[-1]
        if p_identifier_no_prefix not in resource_dictionary and (p_identifier_no_prefix == 'observedProperty' or p_identifier_no_prefix == 'phenomenon' or p_identifier_no_prefix == 'measurand' or p_identifier_no_prefix == 'featureOfInterest' or p_identifier_no_prefix == 'propagationMode' or p_identifier_no_prefix == 'interaction' or p_identifier_no_prefix == 'qualifier' or p_identifier_no_prefix == 'narrower' or p_identifier_no_prefix == 'broader'):
            # Other ontology terms referenced by the resource
            if p_identifier_no_prefix == 'narrower' or p_identifier_no_prefix == 'broader':
                g_other_ontology_term = g
            else:
                g_other_ontology_term = get_graph_of_pithia_ontology_component(p_identifier_no_prefix)
            urls_of_referenced_terms = []
            urls_of_referenced_terms_with_preflabels = []
            for s2, p2, o2 in g.triples((resource_uriref, p.identifier, None)):
                urls_of_referenced_terms.append(str(o2))
            for u in urls_of_referenced_terms:
                u_split = u.split('/')
                ontology_category = u_split[-2]
                ontology_term_id = u_split[-1]
                term_pref_label = ontology_term_id
                pref_label_triples = list(g_other_ontology_term.triples((URIRef(u), SKOS.prefLabel, None)))
                if len(pref_label_triples) > 0:
                    term_pref_label = str(pref_label_triples[0][2])
                if len(pref_label_triples) > 0:
                    urls_of_referenced_terms_with_preflabels.append(f"<a href=\"{reverse('browse:ontology_term_detail', args=[ontology_category, ontology_term_id])}\">{term_pref_label}</a>")
                else:
                    urls_of_referenced_terms_with_preflabels.append(term_pref_label)
            resource_dictionary[p_identifier_no_prefix]= urls_of_referenced_terms_with_preflabels
        if p_identifier_no_prefix not in resource_dictionary:
            if len(list(g.triples((resource_uriref, p.identifier, None)))) > 1:
                resource_dictionary[p_identifier_no_prefix] = []
                for s2, p2, o2 in g.triples((resource_uriref, p.identifier, None)):
                    resource_dictionary[p_identifier_no_prefix].append(str(o2))
            else:
                resource_dictionary[p_identifier_no_prefix] = str(list(g.triples((resource_uriref, p.identifier, None)))[0][2])
    # Have a human-readable version of the predicates to display in the front-end.
    for p in resource_predicates_no_prefix:
        if p == 'broader':
            resource_predicates_readable[p] = 'Broader Terms' 
        elif p == 'narrower':
            resource_predicates_readable[p] = 'Narrower Terms' 
        elif p == 'observedProperty':
            resource_predicates_readable[p] = 'Observed Properties' 
        elif p == 'phenomenon':
            resource_predicates_readable[p] = 'Phenomenons' 
        elif p == 'measurand':
            resource_predicates_readable[p] = 'Measurands' 
        elif p == 'featureOfInterest':
            resource_predicates_readable[p] = 'Features of Interest' 
        elif p == 'interaction':
            resource_predicates_readable[p] = 'Interactions' 
        elif p == 'qualifier':
            resource_predicates_readable[p] = 'Qualifiers'
        else:
            resource_predicates_readable[p] = ' '.join(_split_camel_case(p)).title()
    return render(request, 'browse/ontology_term_detail.html', {
        'title': resource_dictionary['prefLabel'],
        'resource_ontology_url': f'{ONTOLOGY_SERVER_BASE_URL}{category}/{term_id}',
        'resource_dictionary': resource_dictionary,
        'resource_predicates_no_prefix': resource_predicates_no_prefix,
        'resource_predicates_readable': resource_predicates_readable,
        'category': category,
        'category_readable': ' '.join(_split_camel_case(category)).title(),
    })

class ListResourcesView(TemplateView):
    template_name = 'browse/list_resources_of_type.html'
    description = ''
    resource_mongodb_model = None
    resource_type_plural = 'Resources'
    resource_detail_view_name = ''
    resources_list = []

    def get_resources_list(self):
        resources_list = list(self.resource_mongodb_model.find({}))
        return list(map(remove_underscore_from_id_attribute, resources_list))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.resource_type_plural
        context['description'] = self.description
        context['breadcrumb_item_list_resources_of_type_text'] = self.resource_type_plural
        context['resource_type_plural'] = self.resource_type_plural
        context['resource_detail_view_name'] = self.resource_detail_view_name
        context['resources_list'] = self.get_resources_list()

        return context

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class list_organisations(ListResourcesView):
    resource_mongodb_model = mongodb_models.CurrentOrganisation
    resource_type_plural = 'Organisations'
    resource_detail_view_name = 'browse:organisation_detail'
    description = 'Data Provider/Owner organisation'

class list_individuals(ListResourcesView):
    resource_mongodb_model = mongodb_models.CurrentIndividual
    resource_type_plural = 'Individuals'
    resource_detail_view_name = 'browse:individual_detail'
    description = 'An individual, acting in a particular role and associated with an Organisation'

class list_projects(ListResourcesView):
    resource_mongodb_model = mongodb_models.CurrentProject
    resource_type_plural = 'Projects'
    resource_detail_view_name = 'browse:project_detail'
    description = 'An identifiable activity designed to accomplish a set of objectives'

class list_platforms(ListResourcesView):
    resource_mongodb_model = mongodb_models.CurrentPlatform
    resource_type_plural = 'Platforms'
    resource_detail_view_name = 'browse:platform_detail'
    description = 'An identifiable object that brings the acquisition instrument(s) to the appropriate environment (e.g., satellite, ground observatory)'

class list_instruments(ListResourcesView):
    resource_mongodb_model = mongodb_models.CurrentInstrument
    resource_type_plural = 'Instruments'
    resource_detail_view_name = 'browse:instrument_detail'
    description = 'An object responsible for interacting with the Feature of Interest in order to acquire Observed Property values'

class list_operations(ListResourcesView):
    resource_mongodb_model = mongodb_models.CurrentOperation
    resource_type_plural = 'Operations'
    resource_detail_view_name = 'browse:operation_detail'
    description = 'Description of how a platform operates in order to support data acquisition by the instrument'

class list_acquisitions(ListResourcesView):
    resource_mongodb_model = mongodb_models.CurrentAcquisition
    resource_type_plural = 'Acquisitions'
    resource_detail_view_name = 'browse:acquisition_detail'
    description = 'Interaction of the Instrument with the Feature of Interest to obtain its Observed Properties'

class list_computations(ListResourcesView):
    resource_mongodb_model = mongodb_models.CurrentComputation
    resource_type_plural = 'Computations'
    resource_detail_view_name = 'browse:computation_detail'
    description = 'Numerical calculation without interacting with the Feature of Interest; characterised by its numerical input and output'

class list_processes(ListResourcesView):
    resource_mongodb_model = mongodb_models.CurrentProcess
    resource_type_plural = 'Processes'
    resource_detail_view_name = 'browse:process_detail'
    description = 'A designated procedure used to assign a number, term, or other symbols to a Phenomenon generating the Result; consists of Acquisitions and Computations'

class list_data_collections(ListResourcesView):
    resource_mongodb_model = mongodb_models.CurrentDataCollection
    resource_type_plural = 'Data Collections'
    resource_detail_view_name = 'browse:data_collection_detail'
    description = 'Top-level definition of a collection of the model or measurement data, with CollectionResults pointing to its URL(s) for accessing the data. Note: data collections do not include begin and end times, please see Catalogue'

def flatten(d):
    out = {}
    for key, value in d.items():
        if isinstance(value, dict):
            value = [value]
        if isinstance(value, list):
            for subdict in value:
                deeper = flatten(subdict).items()
                out.update({
                    key + '.' + key2: value2 for key2, value2 in deeper
                })
        else:
            out[key] = value
    return out

def resource_detail(request, resource_id, resource_mongodb_model, resource_type_plural, list_resources_of_type_view_name):
    resource = resource_mongodb_model.find_one({
        '_id': ObjectId(resource_id)
    })
    if resource is None:
        return HttpResponseNotFound('Resource not found.')
    resource_flattened = flatten(resource)
    title = resource['identifier']['PITHIA_Identifier']['localID']
    if 'name' in resource:
        title = resource['name']
    return render(request, 'browse/detail.html', {
        'title': title,
        'breadcrumb_item_list_resources_of_type_text': f'{resource_type_plural}',
        'resource': resource,
        'resource_flattened': resource_flattened,
        'list_resources_of_type_view_name': list_resources_of_type_view_name
    })

def organisation_detail(request, organisation_id):
    return resource_detail(request, organisation_id, mongodb_models.CurrentOrganisation, 'Organisations', 'browse:list_organisations')

def individual_detail(request, individual_id):
    return resource_detail(request, individual_id, mongodb_models.CurrentIndividual, 'Individuals', 'browse:list_individuals')

def project_detail(request, project_id):
    return resource_detail(request, project_id, mongodb_models.CurrentProject, 'Projects', 'browse:list_projects')

def platform_detail(request, platform_id):
    return resource_detail(request, platform_id, mongodb_models.CurrentPlatform, 'Platforms', 'browse:list_platforms')

def instrument_detail(request, instrument_id):
    return resource_detail(request, instrument_id, mongodb_models.CurrentInstrument, 'Instruments', 'browse:list_instruments')

def operation_detail(request, operation_id):
    return resource_detail(request, operation_id, mongodb_models.CurrentOperation, 'Operations', 'browse:list_operations')

def acquisition_detail(request, acquisition_id):
    return resource_detail(request, acquisition_id, mongodb_models.CurrentAcquisition, 'Acquisitions', 'browse:list_acquisitions')

def computation_detail(request, computation_id):
    return resource_detail(request, computation_id, mongodb_models.CurrentComputation, 'Computations', 'browse:list_computations')

def process_detail(request, process_id):
    return resource_detail(request, process_id, mongodb_models.CurrentProcess, 'Processes', 'browse:list_processes')

def data_collection_detail(request, data_collection_id):
    return resource_detail(request, data_collection_id, mongodb_models.CurrentDataCollection, 'Data Collections', 'browse:list_data_collections')