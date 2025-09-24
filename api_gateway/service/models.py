from django.db import models

class Service(models.Model):
    system = models.CharField(max_length=100)
    service = models.CharField(max_length=100)
    base_url = models.URLField()

    class Meta:
        unique_together = ('system', 'service')

    def __str__(self):
        return f"{self.system}/{self.service}"
