from django.contrib.auth import get_user_model, login, authenticate, logout
from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer, extend_schema_view, \
    OpenApiParameter
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import permissions, status, parsers, fields, mixins
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from common.models import ProficiencyLevel, AvailableLanguage
from users.filters import UserFilter
from users.models import UserLanguage
from users.serializers import UserSerializer, UserLanguageSerializer, UserPasswordUpdateSerializer


@extend_schema_view(
    retrieve=extend_schema(
        description="Returns the details of the specified user.",
    ),
    list=extend_schema(
        description="Returns a list of users.",
        parameters=[
            OpenApiParameter('levels', type=OpenApiTypes.STR, many=True,
                             description="Filters users by the level of their learning (i.e. non-native) languages."),
        ]
    ),
    create=extend_schema(
        description="Creates a user."
    ),
    partial_update=extend_schema(
        description="Modifies the details of the specified user.",
    ),
    discover=extend_schema(
        description="Returns a random list of users who aren't friends with the session's user.",
        parameters=[
            OpenApiParameter('native_language', type=OpenApiTypes.STR, many=True,
                             description="Filters users by their native languages."),
            OpenApiParameter('learning_language', type=OpenApiTypes.STR, many=True,
                             description="Filters users by the languages they're learning."),
            OpenApiParameter('levels', type=OpenApiTypes.STR, many=True,
                             description="Filters users by the level of their learning (i.e. non-native) languages."),
        ]
    )
)
class UserViewSet(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """
    Allows users to be viewed, created or edited.
    """

    class Meta:
        model = get_user_model()

    queryset = get_user_model().objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser]
    filterset_class = UserFilter
    permission_classes = [DRYPermissions]

    # Disable PUT method, as it's not currently supported due to nested serializer fields
    http_method_names = ['get', 'post', 'patch', 'delete', 'head']

    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        """
        Creates a user and its associated language objects
        """
        response = super(UserViewSet, self).create(request, *args, **kwargs)
        user_id = response.data['id']
        user_object = get_user_model().objects.get(id=user_id)

        try:
            native_languages = request.data["nativeLanguages"]
            if not isinstance(native_languages, list):
                raise ValueError('This field must be a list value.')

            if not len(native_languages):
                raise ValueError(
                    f'This field must include at least one of the following choices: {AvailableLanguage.values}.')

            for language in native_languages:
                if language not in AvailableLanguage.values:
                    raise ValueError(f"'{language}' is not a valid choice.")
                language_object = UserLanguage.objects.create(
                    user=user_object,
                    language=language,
                    level=ProficiencyLevel.NATIVE
                )
                language_object.save()

            serializer = self.get_serializer(user_object)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        except KeyError:
            """Rollback the transaction if the native_languages attribute wasn't provided. """
            transaction.set_rollback(True)
            return Response({'nativeLanguages': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            """Rollback the transaction if native_languages doesn't have the correct format or any of the provided 
            languages is not a valid choice. """
            transaction.set_rollback(True)
            return Response({'nativeLanguages': [str(e)]}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def discover(self, request):
        """ Returns a list of random users which aren't friends of the session's user. """
        # Exclude users who are friends with the session's user from the queryset and order it randomly.
        self.queryset = self.Meta.model.objects.exclude(friend_chats__users=request.user).order_by('?')
        return self.list(self, request)


@extend_schema_view(
    retrieve=extend_schema(
        description="Returns the details of the specified language object.",
    ),
    create=extend_schema(
        description="Creates a user language object."
    ),
    partial_update=extend_schema(
        description="Modifies the details of the specified language object.",
    ),
    destroy=extend_schema(
        description="Deletes the specified language object."
    )
)
class UserLanguageViewSet(mixins.RetrieveModelMixin,
                          mixins.CreateModelMixin,
                          mixins.UpdateModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):
    """
    Allows user languages to be viewed, created or edited.
    """

    class Meta:
        model = UserLanguage

    queryset = UserLanguage.objects.all()
    serializer_class = UserLanguageSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head']
    permission_classes = [DRYPermissions]


@extend_schema(
    responses={
        200: OpenApiResponse(response=inline_serializer(name="session_info_response", fields={
            "id": fields.UUIDField(allow_null=True),
            "url": fields.CharField(allow_blank=True),
        })),
    },
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@ensure_csrf_cookie
def get_session_info(request):
    """
    Returns the user's ID and detail URL in case they're authenticated, or null if they're not. Always returns
     a CSRF token cookie, so that non-logged-in clients can fetch it and use it in login requests.
    """
    user = request.user
    if request.user.is_authenticated:
        user_id = str(user.id)
        url = request.build_absolute_uri(reverse('customuser-detail', kwargs={'pk': user_id}))
        return Response({'id': user_id, 'url': url}, status=status.HTTP_200_OK)
    else:
        return Response({'id': None, 'url': None}, status=status.HTTP_200_OK)
    # Sources:
    # - https://medium.com/swlh/django-rest-framework-and-spa-session-authentication-with-docker-and-nginx-aa64871f29cd
    # - https://briancaffey.github.io/2021/01/01/session-authentication-with-django-django-rest-framework-and-nuxt/
    # - https://stackoverflow.com/a/59120949


@extend_schema(
    request=inline_serializer(name="login_request", fields={
        "username": fields.CharField(),
        "password": fields.CharField(),
    }),
    responses={
        204: OpenApiResponse(description="Successful login.", response=None),
        401: OpenApiResponse(description="Invalid credentials.",
                             response=inline_serializer(name="login_response_unauthorized", fields={
                                 "non_field_errors": fields.ListField(child=fields.CharField())
                             })),
        403: OpenApiResponse(description="Required field not provided.",
                             response=inline_serializer(name="login_response_bad_request", fields={
                                 "username": fields.ListField(child=fields.CharField()),
                                 "password": fields.ListField(child=fields.CharField()),
                             })),
    })
class LoginView(APIView):
    """
    Attempts user login.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            username = request.data['username']
            password = request.data['password']
            user = authenticate(request=request, username=username, password=password)

            if user is None:
                return Response({"non_field_errors": ["Unable to log in with provided credentials."]},
                                status=status.HTTP_401_UNAUTHORIZED)

            login(request, user)
            return Response(None, status=status.HTTP_204_NO_CONTENT)
        except KeyError as e:
            return Response({str(e.args[0]): ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
    #   Partial source: https://www.guguweb.com/2022/01/23/django-rest-framework-authentication-the-easy-way/


@extend_schema(
    responses={
        204: OpenApiResponse(description="Successful logout.", response=None),
    },
    request=None
)
class LogoutView(APIView):
    """
    Attempts user logout.
    """

    def post(self, request):
        logout(request)
        return Response(None, status.HTTP_204_NO_CONTENT)


@extend_schema(
    request=inline_serializer("set_password_request", fields={
        "new_password": fields.CharField(),
        "old_password": fields.CharField(),
    }),
    responses={
        200: OpenApiResponse(description="Successful password change.",
                             response=None),
        400: OpenApiResponse(description="Required field not provided.",
                             response=None),
        401: OpenApiResponse(description="Incorrect old password provided.",
                             response=None)
    }
)
class SetPassword(APIView):
    """
    Updates the session user's password.
    """

    def patch(self, request):
        try:
            new_password = request.data["newPassword"]
            old_password = request.data["oldPassword"]

        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        authenticated = check_password(old_password, request.user.password)
        if not authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # Filter the received request data to avoid setting unwanted data
        data = {"password": new_password}
        serializer = UserPasswordUpdateSerializer(request.user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(request.user, serializer.validated_data)

        return Response(UserSerializer(request.user, context={'request': request}).data, status=status.HTTP_200_OK)
