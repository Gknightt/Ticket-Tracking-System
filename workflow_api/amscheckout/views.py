from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Checkout
from .serializers import CheckoutSerializer

# GET /api/ams/checkout-tickets
class CheckoutListView(generics.ListAPIView):
    queryset = Checkout.objects.all()
    serializer_class = CheckoutSerializer

# POST /api/ams/checkout-resolve/{ticket_id}
class CheckoutResolveView(APIView):
    def post(self, request, ticket_id):
        try:
            checkout = Checkout.objects.get(ticket_id=ticket_id)
        except Checkout.DoesNotExist:
            return Response({"detail": "Ticket not found"}, status=status.HTTP_404_NOT_FOUND)

        is_checkout = request.data.get("is_checkout")
        if is_checkout is None:
            return Response({"detail": "Missing 'is_checkout'"}, status=status.HTTP_400_BAD_REQUEST)

        checkout.is_checkout = is_checkout
        checkout.save()
        return Response(CheckoutSerializer(checkout).data, status=status.HTTP_200_OK)

# POST /api/ams/checkout-create
class CheckoutCreateView(generics.CreateAPIView):
    serializer_class = CheckoutSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

