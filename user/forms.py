from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import AuthenticatedUser

# GENDERS = [
#     ('male', 'Male'),
#     ('female', 'Female'),
#     ('other', 'Other'),
#     ('apache helicopter', 'Apache Helicopter'),
#     ('a10 warthog', 'A10-WartHog'),
#     ('blue hair', 'Blue Hair'),
#     ('punk', 'Punk'),
#     ('uwu', 'uWu'),
#     ('gecko', 'Gecko'),
#     ('vegan', 'Vegan'),
#     ('west virgin', 'West Virgin'),
#     ('none', 'No gender'),
#     ('middle', 'Middle Gender'),
#     ('quarter', 'Quarter Gender'),
#     ('gender2', 'Gender 2'),
# ]

# class UserForm(forms.Form):
#     username = forms.CharField(max_length=32)
#     password = forms.CharField(max_length=64)
#     gender = forms.CharField(max_length=200, choices=forms.Select(choices=GENDERS))
    

class UserSignupForm(forms.ModelForm):

    class Meta:
        model = AuthenticatedUser
        fields = ['username', 'password', 'gender', 'times_queried']


# class UserSignupForm(UserCreationForm):
#     pass


class UserLoginForm(UserSignupForm):

    class Meta(UserSignupForm.Meta):
        exclude = ['gender', 'times_queried']
