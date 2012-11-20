from openPLM.plmapp.tests.views import CommonViewTest

class CalendarTestCase(CommonViewTest):

    def test_history(self):
        " Assert that the template ``history_cal.html`` is used."
        response = self.get(self.base_url + "history/")
        self.assertTemplateUsed(response, "history_cal.html")
        # history_cal.html inherits from history.html
        self.assertTemplateUsed(response, "history.html")

    def test_calendar_part(self):
        response = self.get(self.base_url + "history/calendar/")
        self.assertEqual("", response.context["prefix_url"])
        calendar = response.context["calendar"]
        # TODO: check calendar
        # checks months
        previous_month = response.context["previous_month"]
        current_month = response.context["current_month"]
        next_month = response.context["next_month"]
        self.assertTrue(previous_month < current_month < next_month)
        self.assertNotEqual(previous_month.month, current_month.month)
        self.assertNotEqual(next_month.month, current_month.month)
        # get calendar of next month
        response_next = self.get(self.base_url + "history/calendar/%d/%d/" % 
                (next_month.year, next_month.month))
        self.assertEqual("../../", response_next.context["prefix_url"])
        calendar_next = response_next.context["calendar"]
        self.assertNotEqual(calendar, calendar_next)
        self.assertEqual(current_month.year, response_next.context["previous_month"].year)
        self.assertEqual(current_month.month, response_next.context["previous_month"].month)
        # get calendar of previous month
        response_previous = self.get(self.base_url + "history/calendar/%d/%d/" % 
                (previous_month.year, previous_month.month))
        self.assertEqual("../../", response_previous.context["prefix_url"])
        calendar_previous = response_previous.context["calendar"]
        self.assertNotEqual(calendar, calendar_previous)
        self.assertEqual(current_month.year, response_previous.context["next_month"].year)
        self.assertEqual(current_month.month, response_previous.context["next_month"].month)

    def test_calendar_user(self):
        response = self.get("/user/%s/history/calendar/" % self.user.username)
        calendar = response.context["calendar"]

    def test_calendar_group(self):
        response = self.get("/group/%s/history/calendar/" % self.group.name)
        calendar = response.context["calendar"]

    def test_calendar_timeline(self):
        response = self.get("/timeline/calendar/")
        calendar = response.context["calendar"]

