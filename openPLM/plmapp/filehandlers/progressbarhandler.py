######################################
# Author : Zahariri ALI
# Contact : zahariri.ali@gmail.com
######################################

from django.conf import settings
from django.core.files import temp as tempfile
from django.core.files.uploadhandler import FileUploadHandler
from django.core.files.uploadedfile import UploadedFile

def get_upload_suffix(progress_id):
    return ".%d_openplm_upload" % hash(progress_id)

class ProgressBarUploadHandler(FileUploadHandler):
    """
    Handle and tracks progress for multiple file uploads.
    The http post request must contain a query parameter for each file field,
    which should contain a unique string to identify the temporary file uploaded to be tracked.
    """

    def __init__(self, *args, **kwargs):
        super(ProgressBarUploadHandler, self).__init__(*args, **kwargs)
        self.progress_id = {}

    def new_file(self, file_name, *args, **kwargs):
        """
        Create the file object, identified by the corresponding query parameter,
        to append to as data is coming in.
        """
        self.progress_id[file_name] = self.request.GET[file_name]
        super(ProgressBarUploadHandler, self).new_file(file_name, *args, **kwargs)
        self.file = ProgressUploadedFile(self.progress_id[file_name], self.file_name,
                self.content_type, 0, self.charset)

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


class ProgressUploadedFile(UploadedFile):
    """
    A file uploaded to a temporary location with a specified suffix (i.e. stream-to-disk).
    """
    def __init__(self, progress_id, name, content_type, size, charset):
        suffix = get_upload_suffix(progress_id)
        if settings.FILE_UPLOAD_TEMP_DIR:
            file = tempfile.NamedTemporaryFile(suffix=suffix,
                                               dir=settings.FILE_UPLOAD_TEMP_DIR)
        else:
            file = tempfile.NamedTemporaryFile(suffix=suffix)
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

