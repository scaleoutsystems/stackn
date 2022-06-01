from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from .forms import SignUpForm
from django.conf import settings

# Create your views here.
class HomeView(TemplateView):
    template_name = 'common/landing.html'

class RegistrationCompleteView(TemplateView):
    template_name = 'registration/registration_complete.html'

# Sign Up View
class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'common/signup.html'

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            form.save()
            if settings.INACTIVE_USERS:
                messages.success(request, "Account request has been registered! Please wait for admin to approve!")
                redirect_name = 'common:success'
            else:
                messages.success(request, "Account created successfully!")
                redirect_name = 'login'

            return HttpResponseRedirect(reverse_lazy(redirect_name))

        # Otherwise use built-in parent class-based checks
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)