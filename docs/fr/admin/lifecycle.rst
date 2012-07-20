===============
Cycle de vie
===============


Ajouter un nouveau cycle de vie
===============================

Un cycle de vie doit contenir au moins 3 états :

    1. un état *draft* (brouillon)
    #. des états optionnels
    #. un état officiel
    #. un état *deprecated*

Utiliser l'interface administrateur
++++++++++++++++++++++++++++++++++++

Premièrement, vous devez créer tous les états: ouvrez la page
:samp:`http://{server}/admin/plmapp/state/add` et créez les. Le seul champ requis
est le nom de l'état, il correspond à ce qui sera affiché dans la page cycle de
vie. Un état peut apparaitre dans plusieurs cycles de vie.

Ensuite vous aurez besoin de créer un cycle de vie : ouvrez la page
:samp:`http://{server}/admin/plmapp/lifecycle/add/` et créez le.
Deux champs sont obligatoire : le nom (il correspond au choix proposé lors de la création d'objet) et l'état officiel.

Vous devez ensuite créer les objets (nommés lifecyclestates) qui lient les états avec 
le cycle de vie. Ouvrez la page
:samp:`http://{server}/admin/plmapp/lifecyclestates/add/` et créez un objet
par état. Trois champs sont obligatoires :

    1. Le cycle de vie
    2. L'état
    3. Un rang (champ *rank*): ce champ (un entier) est utilisé pour ordonner les états,
       le premier état doit avoir le plus petit rang.

Via le shell python
++++++++++++++++++++++++++++

Il est possible de créer un cycle de vie en le programmant.

Ouvrez un shell python (:command:`./manage.py shell`):

    >>> from openPLM.plmapp.models import Lifecycle
    >>> from openPLM.plmapp.lifecycle import LifecycleList
    >>> # arguments: name of the lifecycle, name of the official state, names off all states (ordered) 
    >>> lcl = LifecycleList("mylifecycle", "official", "draft", "state2", "state3", "official", "deprecated")
    >>> Lifecycle.from_lifecyclelist(lcl) # create the lifecycle
    <Lifecycle: Lifecycle<mylifecycle>>

.. seealso:: :class:`.LifecycleList`


Comment changer le cycle de vie d'un objet
===========================================

Si vous avez à changer le cycle de vie d'un objet, vous devez :
    
    1. Éditer sa page PLMObject (via l'interface administrateur):
       assurez vous que son état apparaisse dans le nouveau cycle de vie

    2. Assurez vous qu'il y a un (ni plus ni moins) signataire assigné à 
       chaque niveau (numéro de l'état moins un niveau):
       Ajoutez/éditez :class:`PLMObjectUserLink` requis (:samp:`http://{server}/plmapp/plmobjectuserlink/`).
       Tous les roles manquant doivent commencer par ``sign_``.

.. note::

    Si vous devez sélectionner un role de signataire au-delà du 10ème niveau, vous
    devrez mettre à jour le code de :file:`plmapp/models.py`, trouvez les lignes suivantes::
                
        ROLES = [ROLE_OWNER, ROLE_NOTIFIED, ROLE_SPONSOR]
        for i in range(10): # increase this number
            level = level_to_sign_str(i)
            ROLES.append(level)
        ROLE_READER = "reader"

    augmentez le nombre 10 et relancer votre serveur.

    (Oui, c'est agaçant, mais vous ne devriez pas changer le cycle de vie d'un objet).


           

