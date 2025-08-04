from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from .models import Publication, Profile

class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ['content', 'media']
        widgets = {
            'content': forms.Textarea(attrs={'placeholder': '¿Qué quieres funar?', 'class': 'form-control'}),
        }

class RegisterForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password_confirm = forms.CharField(label='Repeat Password', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Las contraseñas no coinciden.')
        email = cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            self.add_error('email', 'Este email ya está registrado.')
        return cleaned_data

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput)

class RecoverPasswordForm(PasswordResetForm):
    email = forms.EmailField(label='Email', max_length=254)

class ProfileEditForm(forms.ModelForm):
    # User fields
    first_name = forms.CharField(
        max_length=30, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'edit-input', 'placeholder': 'Nombre'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'edit-input', 'placeholder': 'Apellido'})
    )
    email = forms.EmailField(
        required=True, 
        widget=forms.EmailInput(attrs={'class': 'edit-input', 'placeholder': 'correo@ejemplo.com'})
    )
    
    class Meta:
        model = Profile
        fields = [
            'avatar', 'biography', 'birth_date', 'favorite_color', 
            'favorite_games', 'national_id', 'favorite_books', 
            'favorite_music', 'programming_languages'
        ]
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'avatar-input', 'accept': 'image/*'}),
            'biography': forms.Textarea(attrs={
                'class': 'edit-textarea', 
                'placeholder': 'Cuéntanos sobre ti...', 
                'maxlength': 130,
                'rows': 4
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'date-input', 
                'type': 'date'
            }),
            'favorite_color': forms.TextInput(attrs={
                'class': 'edit-input', 
                'placeholder': 'Tu color favorito'
            }),
            'favorite_games': forms.TextInput(attrs={
                'class': 'edit-input', 
                'placeholder': 'Tus videojuegos favoritos'
            }),
            'national_id': forms.TextInput(attrs={
                'class': 'edit-input', 
                'placeholder': 'V-12345678'
            }),
            'favorite_books': forms.TextInput(attrs={
                'class': 'edit-input', 
                'placeholder': 'Tus libros favoritos'
            }),
            'favorite_music': forms.TextInput(attrs={
                'class': 'edit-input', 
                'placeholder': 'Tu música favorita'
            }),
            'programming_languages': forms.TextInput(attrs={
                'class': 'edit-input', 
                'placeholder': 'Lenguajes de programación que conoces'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Set initial values for user fields
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name  
            self.fields['email'].initial = user.email
            
            # If we have initial data from instance, make sure user fields are populated
            if hasattr(self, 'instance') and self.instance:
                self.initial.update({
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                })
            
    def save(self, commit=True, user=None):
        profile = super().save(commit=False)
        
        if user and commit:
            # Update user fields
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            
            profile.save()
            
        return profile

class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        label='Contraseña actual',
        widget=forms.PasswordInput(attrs={
            'class': 'password-input',
            'placeholder': 'Ingresa tu contraseña actual'
        })
    )
    new_password = forms.CharField(
        label='Nueva contraseña',
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'password-input',
            'placeholder': 'Ingresa tu nueva contraseña'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('La contraseña actual no es correcta.')
        return old_password

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        old_password = self.cleaned_data.get('old_password')
        
        if new_password and old_password and new_password == old_password:
            raise forms.ValidationError('La nueva contraseña debe ser diferente a la actual.')
        
        return new_password

    def save(self):
        """Cambiar la contraseña del usuario"""
        new_password = self.cleaned_data['new_password']
        self.user.set_password(new_password)
        self.user.save()
        return self.user
