import random
from django.core.management.base import BaseCommand
from faker import Faker
from amscheckout.models import Checkout

class Command(BaseCommand):
    help = 'Seed 20 fake technology-related checkout records'

    def handle(self, *args, **kwargs):
        fake = Faker()
        Checkout.objects.all().delete()  # Optional: wipe previous data

        asset_names = [
            "MacBook Pro", "Dell XPS 13", "iPad Pro", "Surface Laptop", "Canon EOS R5",
            "Sony A7 III", "Logitech MX Master 3", "Samsung Galaxy Tab", "GoPro Hero 9",
            "Lenovo ThinkPad", "HP Spectre x360", "Apple Pencil", "DJI Mavic Air 2",
            "Wacom Intuos Pro", "Asus ROG Zephyrus", "External SSD", "Noise Cancelling Headphones",
            "Bluetooth Keyboard", "Mechanical Keyboard", "4K Monitor"
        ]

        locations = ["Manila HQ", "Cebu Branch", "Makati Office", "Davao Hub", "QC Tech Center"]

        for i in range(20):
            ticket_id = f"TK-{fake.unique.random_int(min=1000, max=9999)}"
            asset = random.choice(asset_names)
            requestor = fake.name()
            requestor_location = random.choice(locations)
            checkout_date = fake.date_between(start_date='-30d', end_date='today')

            # 50% chance the asset is still checked out
            if random.choice([True, False]):
                return_date = None
                is_checkout = True
            else:
                return_date = fake.date_between(start_date=checkout_date, end_date='today')
                is_checkout = False

            Checkout.objects.create(
                ticket_id=ticket_id,
                asset=asset,
                requestor=requestor,
                requestor_location=requestor_location,
                checkout_date=checkout_date,
                return_date=return_date,
                is_checkout=is_checkout
            )


        self.stdout.write(self.style.SUCCESS('✅ Seeded 20 tech-related checkout records.'))
