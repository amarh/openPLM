from django.http import HttpResponseRedirect

from openPLM.plmapp.utils import r2r
from openPLM.plmapp.views.base import handle_errors, get_generic_data


from .forms import PageForm

@handle_errors
def display_page(request, obj_type, obj_ref, obj_revi):
    """
    Files page of a :class:`.Page`.
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    ctx['current_page'] = 'page'
    return r2r('richpage/page.html', ctx, request)


@handle_errors(undo="../page/")
def edit_content(request, obj_type, obj_ref, obj_revi):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if request.method == "POST":
        form = PageForm(request.POST)
        if form.is_valid():
            obj.edit_content(form.cleaned_data["page_content"])
            return HttpResponseRedirect("../page/")
    else:
        form = PageForm(initial={"page_content": obj.page_content})
    ctx["form"] = form
    ctx['current_page'] = 'page'
    return r2r('richpage/edit_content.html', ctx, request)

