#-!- coding:utf-8 -!-

############################################################################
# openPLM - open source PLM
# Copyright 2010 Philippe Joulaud, Pierre Cosquer
#
# This file is part of openPLM.
#
#    openPLM is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    openPLM is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with openPLM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pcosquer@linobject.com
################################################################################

import os.path
import datetime
import warnings
from collections import namedtuple

from pyPdf import PdfFileWriter, PdfFileReader
from pyPdf.generic import NameObject, DictionaryObject, NumberObject,\
    StreamObject, ArrayObject, IndirectObject

from django import http
from django.conf import settings
from django.template.loader import get_template
from django.template import Context
from django.db.models.query import Q

try:
    import xhtml2pdf.pisa as pisa
except ImportError:
    import ho.pisa as pisa
import cStringIO as StringIO

from openPLM.plmapp.views.base import get_obj, handle_errors, get_generic_data
from openPLM.plmapp.controllers import get_controller
from openPLM.plmapp.views import r2r, render_attributes
from openPLM.plmapp.forms import DisplayChildrenForm
from openPLM.apps.pdfgen.forms import get_pdf_formset

class StreamedPdfFileWriter(PdfFileWriter):
    """
    Iterable :class:`PdfFileWriter` (from pyPDF).

    Usage::

        >>> pdf_file = StreamedPdfFileWriter()
        >>> # add contents
        >>> response = HttpResponse(pdf_file)
        >>> # set response headers
    """

    def _sweepIndirectReferences(self, externMap, data):
        # mostly based on _sweepIndirectReferences from pyPDF
        # self.stack is replaced by a set (self.set)
        if isinstance(data, DictionaryObject):
            for key, value in data.iteritems():
                origvalue = value
                value = self._sweepIndirectReferences(externMap, value)
                if isinstance(value, StreamObject):
                    # a dictionary value is a stream.  streams must be indirect
                    # objects, so we need to change this value.
                    value = self._addObject(value)
                data[key] = value
            return data
        elif isinstance(data, ArrayObject):
            for i in xrange(len(data)):
                value = self._sweepIndirectReferences(externMap, data[i])
                if isinstance(value, StreamObject):
                    # an array value is a stream.  streams must be indirect
                    # objects, so we need to change this value
                    value = self._addObject(value)
                data[i] = value
            return data
        elif isinstance(data, IndirectObject):
            # internal indirect references are fine
            if data.pdf == self:
                if data.idnum in self.set:
                    return data
                else:
                    self.set.add(data.idnum)
                    realdata = self.getObject(data)
                    self._sweepIndirectReferences(externMap, realdata)
                    #self.set.remove(data.idnum)
                    return data
            else:
                newobj = externMap.get((data.pdf, data.generation, data.idnum), None)
                if newobj is None:
                    newobj = data.pdf.getObject(data)
                    self._objects.append(None) # placeholder
                    idnum = len(self._objects)
                    newobj_ido = IndirectObject(idnum, 0, self)
                    externMap[(data.pdf, data.generation, data.idnum)] = newobj_ido
                    newobj = self._sweepIndirectReferences(externMap, newobj)
                    self._objects[idnum-1] = newobj
                    return newobj_ido
                return newobj
        else:
            return data

    def __iter__(self):

        warnings.simplefilter('ignore', DeprecationWarning)
        # mostly based on PdfFileWriter.write

        # Begin writing, so that, even if _sweepIndirectReferences takes
        # a long time, the download begins
        object_positions = []
        length = 0
        s = self._header + "\n"
        yield s
        length += len(s)

        externalReferenceMap = {}
        self.set = set()
        self._sweepIndirectReferences(externalReferenceMap, self._root)
        del self.set

        stream = StringIO.StringIO()
        for i, obj in enumerate(self._objects):
            idnum = (i + 1)
            object_positions.append(length)
            s1 = str(idnum) + " 0 obj\n"
            obj.writeToStream(stream, None)
            s2 = stream.getvalue() + "\nendobj\n"
            yield s1 + s2
            length += len(s1) + len(s2)
            stream.reset()
            stream.truncate()

        # xref table
        xref_location = length
        yield("xref\n")
        yield("0 %s\n" % (len(self._objects) + 1))
        yield "0000000000 65535 f \n"

        for offset in object_positions:
            yield "%010d 00000 n \n" % offset

        # trailer
        yield("trailer\n")
        trailer = DictionaryObject()
        trailer.update({
                NameObject("/Size"): NumberObject(len(self._objects) + 1),
                NameObject("/Root"): self._root,
                NameObject("/Info"): self._info,
                })
        if hasattr(self, "_ID"):
            trailer[NameObject("/ID")] = self._ID
        if hasattr(self, "_encrypt"):
            trailer[NameObject("/Encrypt")] = self._encrypt
        trailer.writeToStream(stream, None)
        yield stream.getvalue()

        # eof
        yield("\nstartxref\n%s\n%%%%EOF\n" % (xref_location))
        warnings.simplefilter('default', DeprecationWarning)

def fetch_resources(uri, rel):
    # only load static/media files (security)
    sroot = os.path.normpath(settings.STATIC_ROOT)
    mroot = os.path.normpath(settings.MEDIA_ROOT)
    if uri.startswith(settings.STATIC_URL):
        path = os.path.join(sroot, uri[len(settings.STATIC_URL):])
    elif uri.startswith(settings.MEDIA_URL):
        path = os.path.join(mroot, uri[len(settings.MEDIA_URL):])
    else:
        return ""
    path = os.path.normpath(path)
    if path.startswith((sroot, mroot)) and os.path.exists(path):
        return path
    return ""


def render_to_pdf(template_src, context_dict, filename):
    warnings.simplefilter('ignore', DeprecationWarning)
    template = get_template(template_src)
    context = Context(context_dict)
    html = template.render(context)
    result = StringIO.StringIO()
    pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("utf-16")), result,
        link_callback=fetch_resources)
    if not pdf.err:
        response = http.HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
        warnings.simplefilter('default', DeprecationWarning)
        return response
    warnings.simplefilter('default', DeprecationWarning)
    raise ValueError()

@handle_errors
def attributes(request, obj_type, obj_ref, obj_revi):
    """
    View that returns the object's attributes as a PDF file.
    """
    obj = get_obj(obj_type, obj_ref, obj_revi, request.user)
    if hasattr(obj, "check_readable"):
        obj.check_readable(raise_=True)
    ctx = {"obj" : obj,}
    attributes = render_attributes(obj, obj.attributes)
    if hasattr(obj, "state"):
        attributes.append((obj.get_verbose_name("state"), obj.state.name, False))
    ctx['attributes'] = attributes
    filename = u"%s_%s_%s.pdf" % (obj_type, obj_ref, obj_revi)
    return render_to_pdf('attributes.xhtml', ctx, filename)

StateHistory = namedtuple("StateHistory", "date user state")

_actions = Q(action="Promote") | Q(action="Demote")
def get_state_histories(ctrl):
    lifecycle = ctrl.lifecycle.to_states_list()
    histories = ctrl.HISTORY.objects.filter(_actions, plmobject=ctrl.object)
    r = [StateHistory(ctrl.ctime, ctrl.creator, lifecycle[0])]
    index = 1
    for h in histories.order_by("date").select_related("user"):
        r.append(StateHistory(h.date, h.user, lifecycle[index]))
        if h.action == "Promote":
            index += 1
        else:
            index -= 1
    return r


def download_merged_pdf(obj, files):
    """
    Returns a HTTPResponse that contains all PDF files merged into a
    single PDF file.
    """
    warnings.simplefilter('ignore', DeprecationWarning)

    filename = u"%s_%s_%s_files.pdf" % (obj.type, obj.reference, obj.revision)
    output = StreamedPdfFileWriter()

    # generate a summary
    ctx = { "obj" : obj, "files" : files,
            "state_histories" : get_state_histories(obj),
            }
    template = get_template("summary.xhtml")
    html  = template.render(Context(ctx))
    result = StringIO.StringIO()
    pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("utf-16")), result)
    result.seek(0)
    inp = PdfFileReader(result)
    for page in inp.pages:
        output.addPage(page)

    # append all pdfs
    for pdf_file in files:
        inp = PdfFileReader(file(pdf_file.file.path, "rb"))
        for page in inp.pages:
            output.addPage(page)
    response = http.StreamingHttpResponse(output, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    warnings.simplefilter('default', DeprecationWarning)
    return response


def select_pdf_document(request, ctx, obj):
    """
    Views to select pdf files to download.

    :type obj: :class:`.DocumentController`
    """
    if request.GET.get("Download"):
        formset = get_pdf_formset(obj, request.GET)
        if formset.is_valid():
            files = []
            for form in formset.forms:
                selected = form.cleaned_data["selected"]
                if selected:
                    df = form.cleaned_data["id"]
                    files.append(df)
            return download_merged_pdf(obj, files)
    else:
        formset = get_pdf_formset(obj)
    ctx["pdf_formset"] = formset
    return r2r("select_pdf_doc.html", ctx, request)

class FakeLink(object):

    def __init__(self, id, child):
        self.id = id
        self.child = child

def select_pdf_part(request, ctx, obj):
    """
    View helper to select pdf files to download.

    :type obj: :class:`.PartController`
    """
    data = request.GET if request.GET.get("Download") else None
    # retrieve all pdf files (from documents attached to children parts)
    children = obj.get_children(-1)
    formsets = []
    self_link = FakeLink("self", child=obj.object)
    for level, link in [(0, self_link)] + list(children):
        link.formsets = []
        for l in link.child.documentpartlink_part.now():
            doc = l.document
            ctrl = get_controller(doc.type)(doc, request.user)
            if ctrl.check_readable(raise_=False):
                formset = get_pdf_formset(doc, data,
                        prefix="pdf_%s_%d" % (link.id, doc.id))
                link.formsets.append(formset)
        formsets.append((level, link))

    if data:
        # returns a pdf file if all formsets are valid
        valid = True
        files = []
        for level, link in formsets:
            for formset in link.formsets:
                if formset.is_valid():
                    for form in formset.forms:
                        selected = form.cleaned_data["selected"]
                        if selected:
                            df = form.cleaned_data["id"]
                            files.append(df)
                else:
                    valid = False
        if valid:
            return download_merged_pdf(obj, files)
    ctx["children"] = formsets
    return r2r("select_pdf_part.html", ctx, request)

@handle_errors
def select_pdf(request, obj_type, obj_ref, obj_revi):
    """
    View to download a merged pdf file that contains all pdf files.

    Redirects to :func:`select_pdf_part` or :func:`select_pdf_document`
    according to the type of the object.

    Raises :exc:`ValueError` if the object is not a part or a document.
    """

    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    if obj.is_document:
        return select_pdf_document(request, ctx, obj)
    elif obj.is_part:
        return select_pdf_part(request, ctx, obj)
    else:
        raise ValueError()

@handle_errors
def bom_pdf(request, obj_type, obj_ref, obj_revi):
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    obj.check_readable(raise_=True)

    if not hasattr(obj, "get_children"):
        # TODO
        raise TypeError()
    date = None
    level = "first"
    state = "all"
    show_documents = False
    if request.GET:
        display_form = DisplayChildrenForm(request.GET)
        if display_form.is_valid():
            date = display_form.cleaned_data["date"]
            level = display_form.cleaned_data["level"]
            state = display_form.cleaned_data["state"]
            show_documents = display_form.cleaned_data["show_documents"]
    ctx.update(obj.get_bom(date, level, state, show_documents))
    ctx["date"] = date or datetime.datetime.utcnow()
    filename = u"%s_%s_%s-bom.pdf" % (obj_type, obj_ref, obj_revi)
    return render_to_pdf("bom.xhtml", ctx, filename)
