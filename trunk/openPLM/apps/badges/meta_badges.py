"""
.. module:: meta_badges
"""

from django.db.models import Q
from django.contrib.comments import Comment
from django.utils.translation import ugettext_lazy as _

from openPLM.plmapp import models

from utils import MetaBadge

class Autobiographer(MetaBadge):
    """
    Badge won by user who completed his (her) profile (first name, last name and e mail)
    """
    id = "autobiographer"
    model = models.UserProfile
    one_time_only = True

    title = _("Autobiographer")
    description = _("Completed the User Profile")
    level = "1"

    progress_finish = 3


    def get_progress(self, user):
        has_email = 1 if user.email else 0
        has_f_name = 1 if user.first_name else 0
        has_l_name = 1 if user.last_name else 0
        return has_email + has_f_name + has_l_name


#: badges won when user cancel objects
class SerialKiller(MetaBadge):
    """
    Badge won by user who cancelled XX objects.
    (number of object set to 20 here but it can be modified)
    """
    id= "serialkiller"
    model = models.History
    one_time_only = True

    title = _("Serial Killer")
    description = _("Cancelled XX objects")
    link_to_doc = "PLMObject/1_common.html#lifecycle"
    level = "2"

    #assuming the badge serial killer is awarded when user has cancelled 20 objects
    progress_finish = 20


    def get_progress(self, user):
        cancel_hist = self.model.objects.filter(user=user,action='Cancel').count()
        return cancel_hist


#: badges won by sponsoring or delegating
class WelcomeAA(MetaBadge):
    """
    Badge won by user who sponsored at least 4 users
    """
    id = "welcomeaa"
    model = models.DelegationLink
    one_time_only = True

    title = _("Welcome A.A.")
    description = _("Sponsored 4 users")
    link_to_doc = "tuto_3_user.html#delegation"
    level = "2"

    progress_finish = 4

    def get_user(self, instance):
        return instance.delegator

    def get_progress(self, user):
        sponsored = self.model.current_objects.filter(delegator=user,role='sponsor').count()
        return sponsored


class GodFather(MetaBadge):
    """
    Badge won by user who sponsored more than 10 users
    """
    id = "godfather"
    model = models.DelegationLink
    one_time_only = True

    title = _("God Father")
    description = _("Sponsored more than 10 users")
    link_to_doc = "tuto_3_user.html#delegation"
    level = "3"

    progress_finish=10

    def get_user(self, instance):
        return instance.delegator

    def get_progress(self, user):
        sponsored = self.model.current_objects.filter(delegator=user,role='sponsor').count()
        return sponsored


class DelegateSponsor(MetaBadge):
    """
    Badge won by user who delegate to his(her) sponsor
    """
    id="delegatesponsor"
    model = models.DelegationLink
    one_time_only = True

    title = _("Who's the boss now")
    description = _("Delegate right(s) to his (her) sponsor")
    link_to_doc = "tuto_3_user.html#delegation"
    level = "3"

    def get_user(self, instance):
        return instance.delegator

    def get_progress (self, user):
        sponsor_qs = self.model.current_objects.filter(delegatee = user, role='sponsor')
        if not sponsor_qs :
            return 0

        sponsor = sponsor_qs[0].delegator
        progress = int(self.model.current_objects.filter(delegator = user, delegatee = sponsor).exists())
        return progress



#: badges won by manipulating files

PONY_NAMES = set(["pinkie pie", "applejack", "twilight sparkle", "rarity", "rainbow dash", "fluttershy"])

_added_file_query = Q(action__in=("File added", "added file"))
_deleted_file_query = Q(action__in=("File deleted", "deleted file"))

class PonyRider(MetaBadge):
    """
    Badge won by user who added a file named pinkie pie, applejack, twilight sparkle, rarity, rainbow dash OR fluttershy
    """
    id="ponyrider"
    model = models.History
    one_time_only = True

    title = _("Pony Rider")
    description = _("Added a file named pinkie pie, applejack, twilight sparkle, rarity, rainbow dash or fluttershy")
    level = "2"

    def get_progress(self, user):
        doc_file_hist = self.model.objects.filter(user=user).filter(_added_file_query)
        progress = 0
        for h in doc_file_hist :
            f_name = h.details.split(" : ")[1]
            if f_name in PONY_NAMES:
                progress = 1
                break
        return progress


class SuperPonyRider(MetaBadge):
    """
    Badge won by users who added files named according to ALL characters from my little pony
    """
    id="superponyrider"
    model = models.History
    one_time_only = True

    title = _("Super Pony Rider")
    description = _("Added files named pinkie pie, applejack, twilight sparkle, rarity, rainbow dash and fluttershy")
    level = "4"

    pony_names=["pinkie pie", "applejack", "twilight sparkle", "rarity", "rainbow dash", "fluttershy"]

    def get_progress(self, user):
        doc_file_hist = self.model.objects.filter(user=user).filter(_added_file_query)
        progress = 0
        f_names = []
        for h in doc_file_hist :
            f_names.append(h.details.split(" : ")[1])
        progress = int(set(f_names).issuperset(PONY_NAMES))
        return progress


class DragonSlayer(MetaBadge):
    """
    Badge won by user who added and destroyed a file named spike
    """
    id = "drangonslayer"
    model = models.History
    one_time_only = True

    title = _("Dragon Slayer")
    description = _("Added and destroyed a file named spike")
    level = "4"

    def get_progress(self, user):
        spike_hist = self.model.objects.filter(user=user, action__icontains="file", details__icontains=" spike")
        if not spike_hist:
            return 0

        if spike_hist.filter(_added_file_query) and spike_hist.filter(_deleted_file_query):
            progress = 1
        else:
            progress = 0
        return progress


#: badges won by user who diffused informations

class Herald(MetaBadge):
    """
    Badge won by user who notified 50 users
    """
    id ="herald"
    model = models.History
    one_time_only = True

    title = _("Herald")
    description = _("Notified 50 users")
    level = "3"

    progress_finish = 50

    def get_progress(self, user):
        notified = self.model.objects.filter(user=user, action="New notified").count()
        return notified


class Journalist(MetaBadge):
    """
    Badge won by users who published XX objects.
    """
    id="journalist"
    model = models.History
    one_time_only = True

    title = _("Journalist")
    description = _("Published XX objects")
    level = "3"

    # until the numbers of objects to published, to won this badge , is set
    progress_finish = 20

    def get_progress(self, user):
        published = self.model.objects.filter(user=user, action="Publish").count()
        return published

    def check_action(self, instance):
        return instance.action == "Publish"

    def check_can_publish(self, instance):
        """
        only user who can publish can win this badge
        """
        user = instance.user
        return user.profile.can_publish


#: badges won by user who created links or objects

class HiruleHero(MetaBadge):
    """
    Badge won by users who created 100 part-document links
    """
    id="hirulehero"
    model = models.History
    one_time_only = True

    title = _("Hirule's Hero")
    description = _("Created 100 part-documents links")
    level = "3"

    progress_finish = 100

    def get_progress(self, user):
        linked = self.model.objects.filter(user=user, action="Link : document-part").count()
        return linked

    def check_action(self, instance):
        return instance.action == "Link : document-part"


class WelcomeToHogwarts(MetaBadge):
    """
    Create a Part named "Wizard Wand"
    """
    id="welcometohogwarts"
    model = models.History
    one_time_only = True

    title = _("Welcome To Hogwarts")
    description = _("Created a Part named `Wizard Wand`")
    level = "4"

    def get_progress(self, user):
        wizard = models.Part.objects.filter(creator=user, name="Wizard Wand").exists()
        progress = 1 if wizard else 0
        return progress


class EmmettBrown(MetaBadge):
    """
    Created 121 parts/documents
    """
    id="emmettbrown"
    model = models.History
    one_time_only = True

    title = _("Emmett Brown")
    description = _("Created 121 parts and documents")
    level = "4"

    progress_finish = 121

    def get_progress(self, user):
        created = models.PLMObject.objects.filter(creator=user).count()
        return created



class Guru(MetaBadge):
    """
    Create XX groups
    """
    id="guru"
    model = models.GroupHistory
    one_time_only = True

    title = _("Guru")
    description = _("Created XX groups")
    level = "4"

    progress_finish = 10

    def get_user(self, instance):
        return instance.user

    def get_progress(self, user):
        created = models.GroupInfo.objects.filter(creator=user).count()
        return created


#: badges won manipulating object
class Archivist(MetaBadge):
    """
    Badge won by user who deprecated XX documents
    """
    id="archivist"
    model = models.History
    one_time_only = True

    title = _("Archivist")
    description = _("Deprecated XX documents")
    level = "3"

    #until the number of deprecated doc is set
    progress_finish = 20

    def get_progress(self, user):
        docs_deprecated = models.Document.objects.filter(state='deprecated').values_list('id', flat=True)
        deprecated = self.model.objects.filter(user=user, action__in=["Promote", "Modify", "promoted", "demoted"],
                details__regex=r'changes?.* from.* to .*deprecated.*$', plmobject__in=docs_deprecated).count()
        return deprecated


class WisedOne(MetaBadge):
    """
    Reject 500 documents signatures
    """
    id="wisedone"
    model = models.History
    one_time_only = True

    title = _("Wised One")
    description = _("Rejected 500 objects signatures (or demoted 500 objects)")
    link_to_doc = "PLMObject/1_common.html#lifecycle"
    level = "4"

    progress_finish = 10

    def get_progress(self, user):
        rejected = self.model.objects.filter(user=user, action__in=("Demote", "demoted")).count()
        return rejected/50


class Replicant(MetaBadge):
    """
    Badge won by user who cloned a part/document
    """
    id="replicant"
    model = models.History
    one_time_only = True

    title = _("Replicant")
    description = _("Cloned a part/document")
    link_to_doc = "PLMObject/1_common.html#attributes"
    level = "1"

    def get_progress(self, user):
        progress = 1 if self.model.objects.filter(user=user, action__in=("Clone", "cloned")).exists() else 0
        return progress


class Frankeinstein(MetaBadge):
    """
    Badge won by user who clonee a cancelled or deprecated object
    """
    id="frankeinstein"
    model = models.History
    one_time_only = True

    title = _("Frankeinstein")
    description = _("Cloned a cancelled or deprecated object")
    link_to_doc = "PLMObject/1_common.html#attributes"
    level = "2"

    def get_progress(self, user):
        cloned = self.model.objects.filter(user=user, action__in=("Clone", "cloned"))
        if not cloned :
            return 0

        cloned = [c.plmobject for c in cloned if c.plmobject.is_cancelled or c.plmobject.is_deprecated]
        progress = 0 if not cloned else 1
        return progress


class Tipiak(MetaBadge):
    """
    Badge won by user who cloned object (s)he doesn't own/ didn't create
    """
    id="tipiak"
    model = models.History
    one_time_only = True

    title = _("Tipiak")
    description = _("Cloned object owned and created by another user")
    link_to_doc = "PLMObject/1_common.html#attributes"
    level = "3"

    def get_progress(self, user):
        cloned = self.model.objects.filter(user=user, action__in=("Clone", "cloned"))
        if not cloned :
            return 0

        cloned = [c for c in cloned if c.plmobject.owner != user and c.plmobject.creator != user]
        progress = 0 if not cloned else 1
        return progress


#: property badges
class Materialistic(MetaBadge):
    """
    Badge won by user who owns more than 1000 objects
    """
    id="materialistic"
    model = models.PLMObject
    one_time_only = True

    title = _("Materialistic")
    description = _("Owns more than 1000 objects")
    level = "3"

    progress_finish = 10

    def get_user(self, instance):
        return instance.owner

    def get_progress(self, user):
        owned = self.model.objects.filter(owner=user).count()
        return owned/100


class Popular(MetaBadge):
    """
    Badge won by user who belongs to 20 groups or more
    """
    id="popular"
    model = models.GroupHistory
    one_time_only = True

    title = _("Popular")
    description = _("Belongs to 20 groups or more")
    level = "4"

    progress_finish = 20

    def get_user(self, instance):
        if instance.action == "User added":
            user_name = instance.details
            return models.User.objects.get(username=user_name)
        else :
            return None

    def get_progress(self, user):
        if user :
            groups = models.GroupInfo.objects.filter(id__in=user.groups.all()).count()
            return groups
        else :
            return 0


#: comment badges
class DarthVader(MetaBadge):
    """
    Added the comment "Chocking Hazard"
    """
    id="darthvader"
    model = Comment
    one_time_only = True

    title =_("Darth Vader")
    description = _("Posted the comment `Chocking Hazard`")
    level = "4"

    def get_progress(self, user):
        comments = self.model.objects.filter(user=user).values_list('comment', flat=True)
        comments = [c.lower() for c in comments]
        progress = 1 if "chocking hazard" in comments else 0
        return progress


class RadicalEdward(MetaBadge):
    """
    Post 100 :) comments
    """
    id="radicaledward"
    model = Comment
    one_time_only = True

    title = _("Radical Edward")
    description = _("Posted 100 :) comments")
    level = "4"

    progress_start = 0
    progress_finish = 100

    def get_user(self, instance):
        return instance.user

    def get_progress(self, user):
        comments = Comment.objects.filter(user=user).values_list('comment', flat=True)
        count = 0
        for c in comments:
            if ":)" in c :
                count = count +1
        return count


