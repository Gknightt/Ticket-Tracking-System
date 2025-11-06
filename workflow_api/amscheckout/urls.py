from django.urls import path
from .views import CheckoutListView, CheckoutResolveView, CheckoutCreateView, FlushAndSeedCheckoutView

urlpatterns = [
    path('checkout-tickets/', CheckoutListView.as_view(), name='checkout-list'),
    path('checkout-resolve/<str:ticket_id>/', CheckoutResolveView.as_view(), name='checkout-resolve'),
    path('checkout-create/', CheckoutCreateView.as_view(), name='checkout-create'),
    path('reset/', FlushAndSeedCheckoutView.as_view(), name='flush-seed-checkouts'),
]
