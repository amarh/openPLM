"this is the locale selecting middleware that will look at accept headers"

from django.utils import translation
from django.middleware.locale import LocaleMiddleware


class ProfileLocaleMiddleware(LocaleMiddleware):
    """
    This is a very simple middleware that parses a request
    and decides what translation object to install in the current
    thread context. This allows pages to be dynamically
    translated to the language the user desires (if the language
    is available, of course).

    It behaves like the default LocaleMiddleware except that it
    uses language stored in the profile if the user is authenticated.
    """

    def process_request(self, request):
        # related tickets: #81 and #157
        if request.user.is_authenticated():
            # priority order:
            # 1. session
            # 2. profile
            # if the user select a language before log in
            # the session language is used
            # otherwise, the profile language is used
            language = request.session.get("django_language")
            profile = request.user.profile
            saved_language = profile.language
            if language is None:
                language = saved_language
            else:
                # session language set at the login page: update the profile
                profile.language = language
                profile.save()
        else:
            language = translation.get_language_from_request(request)
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()

