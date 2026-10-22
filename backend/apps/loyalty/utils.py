import random
import string
from apps.loyalty.models import Customer

def generate_unique_card_number(organization, length=10):
    while True:
        card_number = ''.join(random.choices(string.digits, k=length))
        if card_number.startswith('0'):
            continue
        if not Customer.objects.filter(organization=organization, iiko_card_number=card_number).exists():
            return card_number
