import traceback
from pyexpat import ExpatError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import FormView
from register.register import register_metadata_xml_file

from .forms import UploadFileForm
from register import xml_conversion_checks_and_fixes
from common import mongodb_models

# Create your views here.
def index(request):
    return render(request, 'register/index.html', {
        'title': 'Resource Metadata Registration'
    })

class RegisterResourceFormView(FormView):
    resource_mongodb_model = None
    resource_conversion_validate_and_correct_function = None
    success_url = ''
    form_class = UploadFileForm
    template_name = 'register/file_upload.html'

    a_or_an = ''
    resource_type = ''
    validation_url = ''
    post_url = ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Register {self.a_or_an} {self.resource_type.title()}'
        context['validation_url'] = self.validation_url
        context['post_url'] = self.post_url
        context['form'] = self.form_class
        return context

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Form validation
        form = UploadFileForm(request.POST, request.FILES)
        xml_file = request.FILES['file']
        if form.is_valid():
            # XML should have already been validated at
            # the template, and validation could take
            # place again, but takes a long time. Another
            # method which verifies validation took place
            # should be implemented.
            try:
                registration_results = register_metadata_xml_file(xml_file, self.resource_mongodb_model, self.resource_conversion_validate_and_correct_function)
                if registration_results == 'This XML metadata file has been registered before.':
                    messages.error(request, registration_results)
                else:
                    messages.success(request, f'Successfully registered {xml_file.name}.')
            except ExpatError as err:
                print(err)
                print(traceback.format_exc())
                messages.error(request, 'An error occurred whilst parsing the XML.')
            except BaseException as err:
                print(err)
                print(traceback.format_exc())
                messages.error(request, 'An unexpected error occurred.')
        else:
            messages.error(request, 'The form submitted was not valid.')
        return super().post(request, *args, **kwargs)

class organisation(RegisterResourceFormView):
    resource_mongodb_model = mongodb_models.CurrentOrganisation
    success_url = reverse_lazy('register:organisation')

    a_or_an = 'an'
    resource_type = 'organisation'
    validation_url = reverse_lazy('validation:organisation')
    post_url = reverse_lazy('register:organisation')

class individual(RegisterResourceFormView):
    resource_mongodb_model = mongodb_models.CurrentIndividual
    success_url = reverse_lazy('register:individual')

    a_or_an = 'an'
    resource_type = 'individual'
    validation_url = reverse_lazy('validation:individual')
    post_url = reverse_lazy('register:individual')

class project(RegisterResourceFormView):
    resource_mongodb_model = mongodb_models.CurrentProject
    success_url = reverse_lazy('register:project')

    a_or_an = 'a'
    resource_type = 'project'
    validation_url = reverse_lazy('validation:project')
    post_url = reverse_lazy('register:project')

class platform(RegisterResourceFormView):
    resource_mongodb_model = mongodb_models.CurrentPlatform
    success_url = reverse_lazy('register:platform')

    a_or_an = 'a'
    resource_type = 'platform'
    validation_url = reverse_lazy('validation:platform')
    post_url = reverse_lazy('register:platform')

class instrument(RegisterResourceFormView):
    resource_mongodb_model = mongodb_models.CurrentInstrument
    success_url = reverse_lazy('register:instrument')

    a_or_an = 'an'
    resource_type = 'instrument'
    validation_url = reverse_lazy('validation:instrument')
    post_url = reverse_lazy('register:instrument')

class operation(RegisterResourceFormView):
    resource_mongodb_model = mongodb_models.CurrentOperation
    success_url = reverse_lazy('register:operation')

    a_or_an = 'an'
    resource_type = 'operation'
    validation_url = reverse_lazy('validation:operation')
    post_url = reverse_lazy('register:operation')

class acquisition(RegisterResourceFormView):
    resource_mongodb_model = mongodb_models.CurrentAcquisition
    resource_conversion_validate_and_correct_function = xml_conversion_checks_and_fixes.format_acquisition_dictionary
    success_url = reverse_lazy('register:acquisition')

    a_or_an = 'an'
    resource_type = 'acquisition'
    validation_url = reverse_lazy('validation:acquisition')
    post_url = reverse_lazy('register:acquisition')

class computation(RegisterResourceFormView):
    resource_mongodb_model = mongodb_models.CurrentComputation
    resource_conversion_validate_and_correct_function = xml_conversion_checks_and_fixes.format_computation_dictionary
    success_url = reverse_lazy('register:computation')

    a_or_an = 'a'
    resource_type = 'computation'
    validation_url = reverse_lazy('validation:computation')
    post_url = reverse_lazy('register:computation')

class process(RegisterResourceFormView):
    resource_mongodb_model = mongodb_models.CurrentProcess
    resource_conversion_validate_and_correct_function = xml_conversion_checks_and_fixes.format_process_dictionary
    success_url = reverse_lazy('register:process')

    a_or_an = 'a'
    resource_type = 'process'
    validation_url = reverse_lazy('validation:process')
    post_url = reverse_lazy('register:process')

class data_collection(RegisterResourceFormView):
    resource_mongodb_model = mongodb_models.CurrentDataCollection
    resource_conversion_validate_and_correct_function = xml_conversion_checks_and_fixes.format_data_collection_dictionary
    success_url = reverse_lazy('register:data_collection')

    a_or_an = 'a'
    resource_type = 'data collection'
    validation_url = reverse_lazy('validation:data_collection')
    post_url = reverse_lazy('register:data_collection')
