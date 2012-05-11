from django.core.files import temp as tempfile
from django.core.files.uploadhandler import FileUploadHandler
from django.core.files.uploadedfile import *

#import string
#import random

#def gen_id:
#    """
#    Generate random id for temporary file name
#    """
#    chars_id = string.ascii_letters + string.digits
#    return "".join(random.choice(chars_id) for x in xrange(50))

#data={}

class ProgressBarUploadHandler(FileUploadHandler):
    """
    Tracks progress for file uploads.
    The http post request must contain a header or query parameter, 'X_Progress_ID'
    which should contain a unique string to identify the temporary file uploaded to be tracked.
    """

    def __init__(self, *args, **kwargs):
        super(ProgressBarUploadHandler, self).__init__(*args, **kwargs)
        self.progress_id = None

    def new_file(self,file_name, *args, **kwargs):
        """
        Create the file object to append to as data is coming in.
        """
        self.progress_id = self.request.GET['X-Progress-ID']
        super(ProgressBarUploadHandler, self).new_file(file_name, *args, **kwargs)
        self.file = ProgressUploadedFile(self.progress_id,self.file_name, self.content_type, 0, self.charset)

    def receive_data_chunk(self, raw_data, start):
        self.file.write(raw_data)
    
    def file_complete(self, file_size):
        self.file.seek(0)
        self.file.size = file_size
        return self.file

    def upload_complete(self):
        pass

    def get_file_path(self):
        return self.file.temporary_file_path()


from django.conf import settings
class ProgressUploadedFile(UploadedFile):
    """
    A file uploaded to a temporary location with a specified suffix (i.e. stream-to-disk).
    """
    def __init__(self, suf, name, content_type, size, charset):
        suf_id = "%s" % (suf)
        if settings.FILE_UPLOAD_TEMP_DIR:
            file = tempfile.NamedTemporaryFile(suffix='.%s_upload' % (suf_id),
                                               dir=settings.FILE_UPLOAD_TEMP_DIR)
        else:
            file = tempfile.NamedTemporaryFile(suffix='.%s_upload' % (suf_id))
        super(ProgressUploadedFile, self).__init__(file, name, content_type, size, charset)

    def temporary_file_path(self):
        """
        Returns the full path of this file.
        """
        return self.file.name

    def close(self):
        try:
            return self.file.close()
        except OSError, e:
            if e.errno != 2:
                # Means the file was moved or deleted before the tempfile
                # could unlink it.  Still sets self.file.close_called and
                # calls self.file.file.close() before the exception
                raise

