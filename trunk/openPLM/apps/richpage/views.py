from django.http import HttpResponseRedirect

from openPLM.plmapp.utils import r2r
from openPLM.plmapp.views.base import handle_errors, get_generic_data


from .forms import PageForm

@handle_errors
def display_files(request, obj_type, obj_ref, obj_revi):
    """
    Files page of a :class:`.Page`.
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    ctx['current_page'] = 'files'
    return r2r('richpage/files.html', ctx, request)


@handle_errors(undo="../files/")
def edit_content(request, obj_type, obj_ref, obj_revi):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if request.method == "POST":
        form = PageForm(request.POST)
        if form.is_valid():
            obj.edit_content(form.cleaned_data["page_content"])
            return HttpResponseRedirect("../files/")
    else:
        form = PageForm(initial={"page_content": obj.page_content})
    ctx["form"] = form
    return r2r('richpage/edit_content.html', ctx, request)

