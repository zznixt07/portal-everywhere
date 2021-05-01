from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.contrib.auth import views as auth_views
# from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UserSignupForm, UserLoginForm
from .models import AuthenticatedUser, LoginUser
from django.contrib.auth.hashers import check_password, make_password
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def signup(request):
    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        if form.is_valid():
            form.cleaned_data['password'] = make_password(form.cleaned_data['password'])
            AuthenticatedUser(**form.cleaned_data).save()
            return redirect(reverse('user:login'))
        else:
            messages.error(request, 'Invalid form data!', fail_silently=True)
            context = {
                'form': form
            }
    else:
        context = {
            'form': UserSignupForm()
        }
    return render(request, 'user/signup.html', context=context)

def login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        context = {
            'form': form
        }
        if form.is_valid():
            try:
                data = request.POST
                hashed_password = (
                    AuthenticatedUser.objects.get(username=data['username']).password
                )
                if check_password(data['password'], hashed_password):
                    return redirect(reverse('home:index'))
            except AuthenticatedUser.DoesNotExist:
                pass
            messages.error(request, 'Username or Password doesnt match.', fail_silently=True)
        else:
            logger.debug('form is NOT valid.')
            messages.error(request, 'Invalid form data!', fail_silently=True)
    else:
        context = {
            'form': UserLoginForm()
        }
    return render(request, 'user/login.html', context=context)


class OwnLoginView(generic.FormView):
    template_name = 'user/login.html' # default: <app_name>/<model_name>_detail.html
    form_class = UserLoginForm
    success_url = reverse_lazy('home:index')

class OwnSignupView(generic.CreateView):
    template_name = 'user/signup.html'
    form_class = UserSignupForm
    success_url = reverse_lazy('home:login')


class OwnLoginView(auth_views.LoginView):
    template_name = 'user/login.html' # default: <app_name>/<model_name>_detail.html
    # form_class = UserLoginForm
    success_url = reverse_lazy('home:index')
    redirect_authenticated_user = True


class OwnLogoutView(auth_views.LogoutView):
    template_name = 'user/logout.html'


def logout(request):
    pass

def view_users(request):
    context = {
        'users': AuthenticatedUser.recently_signedup_users()
    }
    return render(request, 'user/view_users.html', context=context)