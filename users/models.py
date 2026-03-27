from django.db import models


class UserRegistrationModel(models.Model):
    name = models.CharField(max_length=100)
    loginid = models.CharField(unique=True, max_length=100)
    password = models.CharField(max_length=100)
    mobile = models.CharField(unique=True, max_length=100)
    email = models.CharField(unique=True, max_length=100)
    locality = models.CharField(max_length=100)
    address = models.CharField(max_length=1000)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    status = models.CharField(max_length=100)

    def __str__(self):
        return self.loginid

    class Meta:
        db_table = 'UserRegistrations'


class PredictionHistory(models.Model):
    loginid = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    predicted_class = models.CharField(max_length=100)
    confidence = models.CharField(max_length=20)
    prediction_image = models.ImageField(upload_to='prediction_images/')
    source = models.CharField(max_length=20, default='upload')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} - {self.predicted_class}"

    class Meta:
        db_table = 'PredictionHistory'