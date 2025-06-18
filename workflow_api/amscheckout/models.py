from django.db import models

class Checkout(models.Model):
    ticket_id = models.CharField(max_length=100, unique=True)
    asset = models.CharField(max_length=255)
    requestor = models.CharField(max_length=100)
    requestor_location = models.CharField(max_length=255)
    checkout_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    is_checkout = models.BooleanField(default=True)  # status tracker

    def __str__(self):
        return f"{self.ticket_id} - {self.asset}"
