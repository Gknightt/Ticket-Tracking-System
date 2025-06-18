# views.py

from rest_framework import generics
from .models import Project
from rest_framework.views import APIView
from .serializers import ProjectSerializer
from rest_framework.response import Response
from rest_framework import status

class ProjectListView(generics.ListAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

class ProjectDetailView(generics.RetrieveAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'pk'

class ProjectApproveView(APIView):
    def post(self, request, ticket_id):
        try:
            project = Project.objects.get(ticket_id=ticket_id)
        except Project.DoesNotExist:
            return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        project.is_approved = True
        project.save()
        return Response({"message": f"Project {ticket_id} approved."})