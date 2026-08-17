from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    

    blood_group = forms.ChoiceField(
        choices=[
            ('A+', 'A+'),
            ('A-', 'A-'),
            ('B+', 'B+'),
            ('B-', 'B-'),
            ('AB+', 'AB+'),
            ('AB-', 'AB-'),
            ('O+', 'O+'),
            ('O-', 'O-'),
        ]
    )
    district=forms.ChoiceField(choices=[('Achham', 'Achham'),
    ('Arghakhanchi', 'Arghakhanchi'),
    ('Baglung', 'Baglung'),
    ('Baitadi', 'Baitadi'),
    ('Bajhang', 'Bajhang'),
    ('Bajura', 'Bajura'),
    ('Banke', 'Banke'),
    ('Bara', 'Bara'),
    ('Bardiya', 'Bardiya'),
    ('Bhaktapur', 'Bhaktapur'),
    ('Bhojpur', 'Bhojpur'),
    ('Chitwan', 'Chitwan'),
    ('Dadeldhura', 'Dadeldhura'),
    ('Dailekh', 'Dailekh'),
    ('Dang', 'Dang'),
    ('Darchula', 'Darchula'),
    ('Dhading', 'Dhading'),
    ('Dhankuta', 'Dhankuta'),
    ('Dhanusha', 'Dhanusha'),
    ('Dolakha', 'Dolakha'),
    ('Dolpa', 'Dolpa'),
    ('Doti', 'Doti'),
    ('Eastern Rukum', 'Eastern Rukum'),
    ('Gorkha', 'Gorkha'),
    ('Gulmi', 'Gulmi'),
    ('Humla', 'Humla'),
    ('Ilam', 'Ilam'),
    ('Jajarkot', 'Jajarkot'),
    ('Jhapa', 'Jhapa'),
    ('Jumla', 'Jumla'),
    ('Kailali', 'Kailali'),
    ('Kalikot', 'Kalikot'),
    ('Kanchanpur', 'Kanchanpur'),
    ('Kapilvastu', 'Kapilvastu'),
    ('Kaski', 'Kaski'),
    ('Kathmandu', 'Kathmandu'),
    ('Kavrepalanchok', 'Kavrepalanchok'),
    ('Khotang', 'Khotang'),
    ('Lalitpur', 'Lalitpur'),
    ('Lamjung', 'Lamjung'),
    ('Mahottari', 'Mahottari'),
    ('Makwanpur', 'Makwanpur'),
    ('Manang', 'Manang'),
    ('Morang', 'Morang'),
    ('Mugu', 'Mugu'),
    ('Mustang', 'Mustang'),
    ('Myagdi', 'Myagdi'),
    ('Nawalpur', 'Nawalpur'),
    ('Nuwakot', 'Nuwakot'),
    ('Okhaldhunga', 'Okhaldhunga'),
    ('Palpa', 'Palpa'),
    ('Panchthar', 'Panchthar'),
    ('Parbat', 'Parbat'),
    ('Parsa', 'Parsa'),
    ('Pyuthan', 'Pyuthan'),
    ('Ramechhap', 'Ramechhap'),
    ('Rasuwa', 'Rasuwa'),
    ('Rautahat', 'Rautahat'),
    ('Rolpa', 'Rolpa'),
    ('Rupandehi', 'Rupandehi'),
    ('Salyan', 'Salyan'),
    ('Sankhuwasabha', 'Sankhuwasabha'),
    ('Saptari', 'Saptari'),
    ('Sarlahi', 'Sarlahi'),
    ('Sindhuli', 'Sindhuli'),
    ('Sindhupalchok', 'Sindhupalchok'),
    ('Siraha', 'Siraha'),
    ('Solukhumbu', 'Solukhumbu'),
    ('Sunsari', 'Sunsari'),
    ('Surkhet', 'Surkhet'),
    ('Syangja', 'Syangja'),
    ('Tanahun', 'Tanahun'),
    ('Taplejung', 'Taplejung'),
    ('Terhathum', 'Terhathum'),
    ('Udayapur', 'Udayapur'),
    ('Western Rukum', 'Western Rukum')])

    municipality = forms.CharField(
    max_length=100,
    required=True,
    widget=forms.TextInput(
        attrs={
            'placeholder': 'Example: Kathmandu Metropolitan City'
        }
    )
)

    ward = forms.IntegerField(
        min_value=1,
        max_value=35,
        required=True,
        widget=forms.NumberInput(
            attrs={
                'placeholder': 'Example: 10'
            }
        )
    )

    area = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Example: New Baneshwor'
            }
        )
    )
    
    phoneno = forms.CharField(
    max_length=15,
    initial='+977 '
    )

    gender = forms.ChoiceField(choices=[
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
    ])
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

  


    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'blood_group',
            'district',
            'municipality',
            'ward',
            'area',
            'phoneno',
            'gender',
            'date_of_birth',
            'password1',
            'password2',
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()

        return user
