from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from .forms import SignUpForm
from django.conf import settings

# Create your views here.
class HomeView(TemplateView):
    template_name = 'common/landing.html'

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
            else:
                messages.success(request, "Account created successfully!")

            return HttpResponseRedirect(reverse_lazy('login'))

        # Otherwise use built-in parent class-based checks
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)