from openPLM.plmapp.tests.base import BaseTestCase

from openPLM.plmapp.models import PLMObject, get_all_plmobjects
from openPLM.plmapp.controllers.base import get_controller, Controller


_cache = {}

def init_cls():
    """
    Creates all mock models.
    """
    global Mock, Mock2, Mock3, Mock4, MockController, Mock2Ctrl, _cache
    class Mock(PLMObject):
        pass

    class Mock2(PLMObject):
        pass

    class Mock3(Mock):
        pass

    class Mock4(Mock2):
        pass

    class MockController(Controller):
        pass


    class Mock2Ctrl(Controller):

        MANAGED_TYPE = Mock2

    _cache = get_all_plmobjects._result
    if hasattr(get_all_plmobjects, "_result"):
        del get_all_plmobjects._result

def delete_cls():
    """
    Delete all mock models
    """

    global Mock, Mock2, Mock3, Mock4, MockController, Mock2Ctrl, _cache
    get_all_plmobjects._result = _cache        
    del Mock, Mock2, Mock3, Mock4

class MetaControllerTestCase(BaseTestCase):
    """
    TestCase for :meth:`.get_controller`
    """

    def setUp(self):
        init_cls()

    def tearDown(self):
        delete_cls()

    def test_get_mock(self):
        self.assertEqual(MockController, get_controller("Mock"))

    def test_get_mock2(self):
        self.assertEqual(Mock2Ctrl, get_controller("Mock2"))

    def test_get_mock3(self):
        self.assertEqual(MockController, get_controller("Mock3"))

    def test_get_mock4(self):
        self.assertEqual(Mock2Ctrl, get_controller("Mock4"))

