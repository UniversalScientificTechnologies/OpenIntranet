import calendar
import functools
import json
from datetime import datetime, timedelta

import bson.json_util
from dateutil.relativedelta import relativedelta
from tornado.web import HTTPError

from plugins import BaseHandler, get_dpp_params
from plugins.helpers import database_attendance as adb
from plugins.helpers import database_user as udb
from plugins.helpers import str_ops
from plugins.helpers.exceptions import BadInputError
from plugins.helpers.finance import calculate_tax
from plugins.helpers.math_utils import floor_to_half
from plugins.helpers.mdoc_ops import compile_user_month_info, get_user_days_of_vacation_in_year


def make_handlers(plugin_name, plugin_namespace):
    return [
        (r'/{}/u/(.*)/date/(.*)'.format(plugin_name), plugin_namespace.UserAttendanceHandler),
        (r'/{}/u/(.*)'.format(plugin_name), plugin_namespace.UserAttendanceHandler),
        (r'/{}/api/u/(.*)/workspans'.format(plugin_name), plugin_namespace.ApiAddWorkspanHandler),
        (r'/{}/api/u/(.*)/workspans/month'.format(plugin_name), plugin_namespace.ApiMonthWorkspansHandler),
        (r'/{}/api/u/(.*)/calendar/date/(.*)'.format(plugin_name), plugin_namespace.ApiCalendarHandler),
        (r'/{}/api/u/(.*)/monthinfo/date/(.*)'.format(plugin_name), plugin_namespace.ApiMonthInfoHandler),
        (r'/{}/api/u/(.*)/workspans/delete'.format(plugin_name), plugin_namespace.ApiDeleteWorkspanHandler),
        (r'/{}/api/u/(.*)/vacations'.format(plugin_name), plugin_namespace.ApiAddVacationHandler),
        (r'/{}/api/u/(.*)/vacations/interrupt'.format(plugin_name), plugin_namespace.ApiInterruptVacationHandler),
        (r'/{}/api/month_table/(.*)'.format(plugin_name), plugin_namespace.ApiAdminMonthTableHandler),
        (r'/{}/api/year_table/(.*)'.format(plugin_name), plugin_namespace.ApiAdminYearTableHandler),
        (r'/{}'.format(plugin_name), plugin_namespace.HomeHandler),
        (r'/{}/'.format(plugin_name), plugin_namespace.HomeHandler),
    ]


def plug_info():
    return {
        "module": "attendance",
        "name": "Docházka",
        "icon": 'icon_users.svg',
        # "role": ['user-sudo', 'user-access', 'user-read', 'economy-read', 'economy-edit'],
    }


class HomeHandler(BaseHandler):

    def get(self):
        me = self.actual_user

        if self.is_authorized(['users-editor', 'sudo-users']):
            self.render('attendance.home-sudo.hbs')
        else:
            self.redirect(f"/attendance/u/{me['_id']}")


class AttendanceCalculator:

    def __init__(self, database, user_id, date: datetime):
        self.database = database
        self.user_id = user_id
        self.month = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self.year = self.month.replace(month=1)

        self.dpp_params = get_dpp_params(self.database)
        self.year_max_hours = self.dpp_params["year_max_hours"]
        self.month_max_gross_wage = self.dpp_params["month_max_gross_wage"]
        self.tax_rate = self.dpp_params["tax_rate"]
        self.tax_deduction = self.dpp_params["tax_deduction"]
        self.tax_deduction_student = self.dpp_params["tax_deduction_student"]

        self._month_hours_worked = None
        self._month_gross_wage = None
        self._month_tax_amount = None

        self._month_hour_rate = None

        self._year_hours_worked = None
        self._year_gross_wage = None
        self._year_tax_amount = None

    def _calculate_this_month(self):
        hours_worked, gross_wage, tax_amount = self._calculate_given_month(self.month)

        self._month_hours_worked = hours_worked
        self._month_gross_wage = gross_wage
        self._month_tax_amount = tax_amount

    def _calculate_given_month(self, month: datetime):
        print("_calculate_given_month", month)
        if month == self.month and self._month_hours_worked is not None:
            print("tento měsíc je už spočítaný")
            return self._month_hours_worked, self._month_gross_wage, self.month_tax_amount

        next_month = month + relativedelta(months=1)

        workspans = adb.get_user_workspans(self.database, self.user_id, month, next_month)

        has_study_certificate = self._month_has_study_certificate(month)
        has_tax_declaration = self._month_has_tax_declaration(month)

        contract = None

        hours_worked = 0
        for workspan in workspans:
            if workspan["contract"]:
                if not contract:
                    contract = udb.get_user_contract_by_id(self.database, self.user_id, workspan["contract"])

            else:
                print(f"Pro tuto práci neexistuje platná smlouva: {workspan}")
                continue  # TODO vyřešit hlášení do frontendu

            hours_worked += workspan["hours"]

        if not hours_worked or not contract:
            return 0, 0, 0

        gross_wage = contract["hour_rate"] * hours_worked

        tax_amount = calculate_tax(gross_wage, self.tax_rate,
                                   self.tax_deduction if has_tax_declaration else 0,
                                   self.tax_deduction_student if has_study_certificate else 0)

        return hours_worked, gross_wage, tax_amount

    def _calculate_this_year(self):
        hours_worked = 0
        gross_wage = 0
        tax_amount = 0
        for month in range(12):
            start_of_month = datetime(self.year.year, month + 1, 1)
            month_hours_worked, month_gross_wage, month_tax_amount = self._calculate_given_month(start_of_month)

            hours_worked += month_hours_worked
            gross_wage += month_gross_wage
            tax_amount += month_tax_amount

        self._year_hours_worked = hours_worked
        self._year_gross_wage = gross_wage
        self._year_tax_amount = tax_amount

    def _month_has_study_certificate(self, month):
        return bool(udb.get_user_active_documents(self.database, self.user_id, "study_certificate",
                                                  month, month + relativedelta(months=1)))

    def _month_has_tax_declaration(self, month):
        return bool(udb.get_user_active_documents(self.database, self.user_id, "tax_declaration",
                                                  month, month + relativedelta(months=1)))

    @property
    def month_hours_worked(self):
        if self._month_hours_worked is None:
            self._calculate_this_month()

        return self._month_hours_worked

    @property
    def month_gross_wage(self):
        if self._month_gross_wage is None:
            self._calculate_this_month()

        return self._month_gross_wage

    @property
    def month_tax_amount(self):
        if self._month_tax_amount is None:
            self._calculate_this_month()

        return self._month_tax_amount

    @property
    def year_hours_worked(self):
        if self._year_hours_worked is None:
            self._calculate_this_year()

        return self._year_hours_worked

    @property
    def year_gross_wage(self):
        if self._year_gross_wage is None:
            self._calculate_this_year()

        return self._year_gross_wage

    @property
    def year_tax_amount(self):
        if self._year_tax_amount is None:
            self._calculate_this_year()

        return self._year_tax_amount

    @property
    def month_hour_rate(self):
        if self._month_hour_rate is None:
            self._calculate_this_month()

        month_contracts = udb.get_user_active_contracts(self.database, self.user_id, self.month,
                                                        self.month + relativedelta(months=1))
        if month_contracts:
            return month_contracts[0]["hour_rate"]
        else:
            return None

    @property
    def month_net_wage(self):
        return self.month_gross_wage - self.month_tax_amount

    @property
    def year_net_wage(self):
        return self.year_gross_wage - self.year_tax_amount

    @property
    def month_max_hours(self):
        if self.month_hour_rate is None:
            return None
        return floor_to_half(self.month_max_gross_wage / self.month_hour_rate)

    @property
    def month_available_hours(self):
        if self.month_max_hours is None:
            return None
        return self.month_max_hours - self.month_hours_worked

    @property
    def year_available_hours(self):
        return self.year_max_hours - self.year_hours_worked


class ApiAdminMonthTableHandler(BaseHandler):

    def get(self, date):
        date = str_ops.datetime_from_iso_str(date)
        rows = []

        users = udb.get_users(self.mdb.users)
        for user in users:
            calculator = AttendanceCalculator(self.mdb, user["_id"], date)

            row = {
                "id": user["_id"],
                "name": user.get("name", {}),
                "hours_worked": calculator.month_hours_worked,
                "hour_rate": calculator.month_hour_rate,
                "month_closed": user.get("month_closed", False),  # TODO tak jak nyní month_closed funguje nedává smysl,
                # v db je reprezentován bool hodnotou, ale to znamená že ta bude skákat každý měsíc. Větší smysl dává
                # mít pole months_closed or closed_months a do něj přidávat uzavřené měsíce (třeba data prvních dnů
                # v měsíci v iso tvaru.
                "gross_wage": calculator.month_gross_wage,
                "tax_amount": calculator.month_tax_amount,
                "net_wage": calculator.month_net_wage,
            }
            rows.append(row)

        self.write(bson.json_util.dumps(rows))


class ApiAdminYearTableHandler(BaseHandler):

    def get(self, date):
        date = str_ops.datetime_from_iso_str(date)

        rows = []

        users = udb.get_users(self.mdb.users)
        for user in users:
            calculator = AttendanceCalculator(self.mdb, user["_id"], date)

            row = {
                "id": user["_id"],
                "name": user.get("name", {}),
                "hours_worked": calculator.year_hours_worked,
                "gross_wage": calculator.year_gross_wage,
                "tax_amount": calculator.year_tax_amount,
                "net_wage": calculator.year_net_wage,
            }
            rows.append(row)

        self.write(bson.json_util.dumps(rows))


class UserAttendanceHandler(BaseHandler):

    def get(self, user_id, date_str=None):
        date = str_ops.datetime_from_iso_str(date_str)
        if not date:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        user_document = udb.get_user(self.mdb.users, user_id)

        day_workspans = adb.get_user_workspans(self.mdb, user_id, date, date + timedelta(days=1))
        print("day_workspans", day_workspans)
        print("date", date)
        for ws in day_workspans:
            ws["to"] = str_ops.date_to_time_str(ws["from"] + timedelta(minutes=round(ws["hours"] * 60)))
            ws["from"] = str_ops.date_to_time_str(ws["from"])

        current_and_future_vacations = adb.get_user_vacations(self.mdb, user_id, date)
        is_vacation_day = current_and_future_vacations and current_and_future_vacations[0]["from"] <= date

        for vacation in current_and_future_vacations:
            vacation["from"] = str_ops.date_to_str(vacation["from"])
            vacation["to"] = str_ops.date_to_str(vacation["to"])

        template_params = {
            "_id": user_id,
            "name": str_ops.name_to_str(user_document.get("name", {})),
            "date": str_ops.date_to_iso_str(date),
            "date_pretty": str_ops.date_to_str(date),
            "workspans": day_workspans,
            "vacations": current_and_future_vacations,
            "is_vacation_day": is_vacation_day,
        }

        self.render("attendance.home.hbs", **template_params)


class ApiCalendarHandler(BaseHandler):

    def post(self, user_id, date):
        # TODO je potřeba v kalendáři mít přístup i k assignmentům
        month = str_ops.datetime_from_iso_str(date).replace(day=1)
        num_days_in_month = calendar.monthrange(month.year, month.month)[1]

        vacations = adb.get_user_vacations(self.mdb,
                                           user_id,
                                           month - relativedelta(months=1),
                                           month + relativedelta(months=2))
        print(vacations)
        vacation_days = []
        for vacation in vacations:
            vacation_length = (vacation["to"] - vacation["from"]).days + 1
            vacation_days += [str_ops.date_to_iso_str(vacation["from"] + timedelta(days=i))
                              for i in range(vacation_length)]

        workspans = adb.get_user_workspans(self.mdb,
                                           user_id,
                                           month - relativedelta(months=1),
                                           month + relativedelta(months=2))
        workspan_days_hours = {}
        for workspan in workspans:
            iso_date = str_ops.date_to_iso_str(workspan["from"])

            if iso_date in workspan_days_hours:
                workspan_days_hours[iso_date] += workspan["hours"]
            else:
                workspan_days_hours[iso_date] = workspan["hours"]

        data = {
            "vacations": vacation_days,
            "workdays": workspan_days_hours,
        }

        self.write(bson.json_util.dumps(data))


class ApiMonthInfoHandler(BaseHandler):

    def post(self, user_id, date):
        month = str_ops.datetime_from_iso_str(date).replace(day=1)

        calculator = AttendanceCalculator(self.mdb, user_id, month)

        data = {
            "month_hours_worked": calculator.month_hours_worked,
            "year_hours_worked": calculator.year_hours_worked,
            "hour_rate": calculator.month_hour_rate,
            "year_max_hours": calculator.year_max_hours,
            "month_max_hours": calculator.month_max_hours,
            "month_available_hours": calculator.month_available_hours,
            "year_available_hours": calculator.year_available_hours,
            "month_gross_wage": calculator.month_gross_wage,
            "month_tax_amount": calculator.month_tax_amount,
            "month_net_wage": calculator.month_net_wage,
            "year_days_of_vacation": get_user_days_of_vacation_in_year(self.mdb, user_id, month),
        }

        self.write(bson.json_util.dumps(data))


class WorkspanBaseHandler(BaseHandler):

    def check_vacations_conflicts(self, user_id, workspan):
        """ returns true if there is no conflict """
        # z databáze dostaneme dovolené končící dnes nebo později seřazené podle data konce.
        # první dovolená je nejblíž, stačí tedy zkontrolovat, jestli začíná dnes nebo dříve.
        today = workspan["from"].replace(hour=0, minute=0, second=0, microsecond=0)
        vacations = adb.get_user_vacations(self.mdb, user_id, today)
        if vacations and vacations[0]["from"] <= workspan["from"]:
            return False

        return True

    def check_workspans_conflicts(self, user_id, workspan):
        today = workspan["from"].replace(hour=0, minute=0, second=0, microsecond=0)
        tomorow = today + relativedelta(days=1)

        todays_workspans = adb.get_user_workspans(self.mdb, user_id, today, tomorow)
        workspan_end = workspan["from"] + relativedelta(minutes=int(workspan["hours"] * 60))

        for other_ws in todays_workspans:
            latest_start = max(workspan["from"], other_ws["from"])
            earliest_end = min(workspan_end, other_ws["from"] + relativedelta(minutes=int(other_ws["hours"]) * 60))

            if latest_start < earliest_end:
                return False

        return True


class ApiAddWorkspanHandler(WorkspanBaseHandler):

    def post(self, user_id):
        req = self.request.body.decode("utf-8")
        form_data = bson.json_util.loads(req)

        today = str_ops.datetime_from_iso_str(form_data["date"])

        workspan = {}
        workspan["from"] = str_ops.datetime_from_iso_string_and_time_string(form_data["date"], form_data["from"])
        workspan["hours"] = float(form_data["hours"])
        workspan["assignment"] = form_data["assignment"]

        contract_mdoc = udb.get_user_active_contract(self.mdb.users, user_id, today)
        workspan["contract"] = contract_mdoc["_id"] if contract_mdoc else None

        if not self.check_vacations_conflicts(user_id, workspan):
            raise BadInputError("Na dovolené se nepracuje.")

        if not self.check_workspans_conflicts(user_id, workspan):
            raise BadInputError("Časový konflikt s jinou prací.")

        print("ukladam workspan", workspan)

        adb.add_user_workspan(self.mdb, user_id, workspan)


class ApiMonthWorkspansHandler(BaseHandler):

    def post(self, user_id):
        req = self.request.body.decode("utf-8")
        form_data = bson.json_util.loads(req)

        for day_dict in form_data:
            today = str_ops.datetime_from_iso_str(day_dict["date"])
            tomorow = today + relativedelta(days=1)

            workspan = {}
            workspan["from"] = today
            workspan["hours"] = float(day_dict["hours"])
            workspan["assignment"] = day_dict["assignment"]

            contract_mdoc = udb.get_user_active_contract(self.mdb.users, user_id, today)
            workspan["contract"] = contract_mdoc["_id"] if contract_mdoc else None

            todays_workspans = adb.get_user_workspans(self.mdb, user_id, today, tomorow)

            for today_workspan in todays_workspans:
                adb.delete_user_workspan(self.mdb, user_id, today_workspan["_id"])

            if workspan["hours"] > 0:
                adb.add_user_workspan(self.mdb, user_id, workspan)


class ApiAddVacationHandler(BaseHandler):

    def post(self, user_id):
        # TODO hlídat aby nové dovolené byly v budoucnosti, nelze přidat dovolenou zpětně
        req = self.request.body.decode("utf-8")
        data = bson.json_util.loads(req)

        vacation = {
            "from": str_ops.datetime_from_iso_str(data["from"]),
            "to": str_ops.datetime_from_iso_str(data["to"])
        }

        if vacation["from"] > vacation["to"]:
            raise BadInputError("Dovolená skončila dříve než začala.")

        other_vacations = adb.get_user_vacations(self.mdb, user_id, vacation["from"])
        for other_vac in other_vacations:
            latest_start = max(vacation["from"], other_vac["from"])
            earliest_end = min(vacation["to"], other_vac["to"])

            if latest_start <= earliest_end:
                raise BadInputError("Časový konflikt s jinou dovolenou.")

        adb.add_user_vacation(self.mdb, user_id, vacation)


class ApiInterruptVacationHandler(BaseHandler):

    def post(self, user_id):
        req = self.request.body.decode("utf-8")
        data = json.loads(req)

        interruption_date = str_ops.datetime_from_iso_str(data["date"])
        vacation_mdoc = adb.get_user_vacation_by_id(self.mdb, user_id, data["_id"])

        if not (vacation_mdoc["from"] <= interruption_date <= vacation_mdoc["to"]):
            raise BadInputError("Datum přerušení musí být mezi začátkem a koncem dovolené!")

        adb.interrupt_user_vacation(self.mdb, user_id, data["_id"], interruption_date)


class ApiDeleteWorkspanHandler(BaseHandler):

    def post(self, user_id):
        workspan_id = self.request.body.decode("utf-8")
        adb.delete_user_workspan(self.mdb, user_id, workspan_id)
