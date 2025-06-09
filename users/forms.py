from django import forms
from django.contrib.auth.models import User

class UserEditForm(forms.ModelForm):
    password = forms.CharField(
        label='新密碼（如需變更）', 
        required=False, 
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ['username', 'email']  # 不要包含 password