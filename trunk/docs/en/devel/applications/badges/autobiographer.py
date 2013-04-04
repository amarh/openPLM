class Autobiographer(MetaBadge):
    id = "autobiographer"
    model = UserProfile
    one_time_only = True

    title = "Autobiographer"
    description = "Completed the User Profile"
    link_to_doc = ""
    level = "1"

    # not required
    progress_start = 0
    progress_finish = 2

    # optional functions
    def get_user(self, instance):
        return instance.user

    def check_email(self, instance):
        return instance.user.email

    def check_bio(self, instance):
        return instance.bio

    # required functions
    def get_progress(self, user):
        has_email = 1 if user.email else 0
        has_bio = 1 if user.profile.bio else 0
        return has_email + has_bio

