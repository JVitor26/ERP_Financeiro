from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .auth import ERPTokenObtainPairSerializerWithMFA
from .serializers import UsuarioSerializer


class ERPTokenObtainPairView(TokenObtainPairView):
    serializer_class = ERPTokenObtainPairSerializerWithMFA


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UsuarioSerializer

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)
