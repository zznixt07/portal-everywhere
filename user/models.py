from django.db import models

GENDERS = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
    ('apache helicopter', 'Apache Helicopter'),
    ('a10 warthog', 'A10-WartHog'),
    ('blue hair', 'Blue Hair'),
    ('punk', 'Punk'),
    ('uwu', 'uWu'),
    ('gecko', 'Gecko'),
    ('vegan', 'Vegan'),
    ('west virgin', 'West Virgin'),
    ('none', 'No gender'),
    ('middle', 'Middle Gender'),
    ('quarter', 'Quarter Gender'),
    ('gender2', 'Gender 2'),
]


class User(models.Model):
    # id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=64)
    gender = models.CharField(max_length=100, choices=GENDERS, default=None, null=True)
    times_queried = models.PositiveIntegerField('Num. of times queried', default=0)

    def __str__(self):
        return f'{self.username}'

    @classmethod
    def recently_signedup_users(cls):
         return cls.objects.all()[:5]

    class Meta:
        abstract = True
    

class AuthenticatedUser(User):
    pass


class LoginUser(User):
    gender = None
    times_queried = None