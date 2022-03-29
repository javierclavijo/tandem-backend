from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from communities.models import Channel, Membership
from chats.models import UserChat
from chats.serializers import UserChatSerializer, ChannelChatSerializer


class UserChatViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to view chats, send messages and edit them, etc.
    """

    class Meta:
        model = UserChat

    def get_queryset(self):
        return self.request.user.chats.all()

    queryset = UserChat.objects.all()
    serializer_class = UserChatSerializer
    permission_classes = [permissions.IsAuthenticated]


class ChannelChatViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to view channel chats, send messages and edit them, etc.
    """

    class Meta:
        model = Channel

    def get_queryset(self):
        return Channel.objects.filter(memberships__user=self.request.user)

    queryset = Channel.objects.all()
    serializer_class = ChannelChatSerializer
    permission_classes = [permissions.IsAuthenticated]


class ChatListView(APIView):
    """
    View to list the current user's user and channel chats. Returns a JSON list with the URL and name for each chat,
    plus information about the chat's latest message.

    * Requires authentication
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        chats = []

        # Fetch list of the user's channels and annotate with the channel's latest message, then append to the list
        # of chats
        memberships = Membership.objects.filter(user=user).select_related('channel')
        for chat in memberships:
            latest_message = chat.channel.messages.order_by('-timestamp').first()
            chat_object = {
                'url': reverse('channelchat-detail', kwargs={'pk': chat.pk}),
                'name': chat.channel.name,
                'latest_message': {
                    'content': latest_message.content,
                    'timestamp': latest_message.timestamp,
                    'author': latest_message.author.username
                }
            }
            chats.append(chat_object)

        # Do the same for user chats, appending the other user's name to the dict
        for chat in user.chats.all():
            latest_message = chat.messages.order_by('-timestamp').first()
            chat_object = {
                'url': reverse('userchat-detail', kwargs={'pk': chat.pk}),
                'name': chat.users.exclude(pk=request.user.pk).get().username,
                'latest_message': {
                    'content': latest_message.content,
                    'timestamp': latest_message.timestamp,
                    'author': latest_message.author.username
                }
            }
            chats.append(chat_object)

        # Sort chats by latest message datetime
        chats = list(sorted(chats, key=lambda x: x['latest_message']['timestamp'], reverse=True))
        return Response({"chats": chats})
