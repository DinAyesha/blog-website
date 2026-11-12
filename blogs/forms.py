
from django import forms
from django.contrib.auth.models import User
from .models import UserProfile


class UserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        if User.objects.filter(email__iexact=email).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError(
                "This email is already registered."
            )

        return email


class UserProfileForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ['profile_picture']
