from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from .forms import SignUpForm

# Create your views here.
class HomeView(TemplateView):
    template_name = 'common/landing.html'

# Sign Up View
class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'common/signup.html'
