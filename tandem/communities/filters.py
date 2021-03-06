from django.db.models import Q
from django_filters import rest_framework as filters

from common.models import AvailableLanguage, ProficiencyLevel
from communities.models import Channel


class ChannelFilter(filters.FilterSet):
    """
    Filter class for UserViewSet. Accepts a 'search' parameter that includes all users with a username or description
    which contains the search term.
    """
    search = filters.CharFilter(method='get_search')
    language = filters.MultipleChoiceFilter(field_name='language', choices=AvailableLanguage.choices)
    level = filters.MultipleChoiceFilter(field_name='level', choices=ProficiencyLevel.choices)

    def get_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )

    class Meta:
        model = Channel
        fields = ('search', 'memberships__user', 'language', 'level')
