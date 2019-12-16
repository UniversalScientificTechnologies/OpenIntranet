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
from plugins.helpers.mdoc_ops import compile_user_month_info, get_user_days_of_vacation_in_year


def make_handlers(plugin_name, plugin_namespace):
    return [
        (r'/{}/u/(.*)/date/(.*)'.format(plugin_name), plugin_namespace.UserAttendanceHandler),
        (r'/{}/u/(.*)'.format(plugin_name), plugin_namespace.UserAttendanceHandler),
        (r'/{}/api/u/(.*)/workspans'.format(plugin_name), plugin_namespace.ApiAddWorkspanHandler),
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

        self._year_hours_worked = None
        self._year_gross_wage = None
        self._year_tax_amount = None

    def _calculate_this_month(self):
        hours_worked, gross_wage, tax_amount = self._calculate_given_month(self.month)

        self._month_hours_worked = hours_worked
        self._month_gross_wage = gross_wage
        self._month_tax_amount = tax_amount

    def _calculate_given_month(self, month: datetime):
        next_month = month + relativedelta(months=1)

        workspans = adb.get_user_workspans(self.database, self.user_id, month, next_month)

        has_study_certificate = bool(udb.get_user_active_documents(self.database, self.user_id, "study_certificate",
                                                                   month, next_month))
        has_tax_declaration = bool(udb.get_user_active_documents(self.database, self.user_id, "tax_declaration",
                                                                 month, next_month))
        contract = None

        hours_worked = 0
        gross_wage = 0
        for workspan in workspans:
            if not contract or contract["_id"] != workspan["contract"]:
                contract = udb.get_user_active_contract(self.database.users, self.user_id, workspan["from"])

            if not contract:
                raise ValueError("Pro některé zapsané hodiny uživatele nepřipadá platná smlouva.")

            hours_worked += workspan["hours"]
            gross_wage += workspan["hours"] * contract["hour_rate"]

        tax_amount = calculate_tax(gross_wage, self.tax_rate,
                                   self.tax_deduction if has_tax_declaration else 0,
                                   self.tax_deduction_student if has_study_certificate else 0)

        return hours_worked, gross_wage, tax_amount

    def _calculate_this_year(self):
        hours_worked = 0
        gross_wage = 0
        tax_amount = 0
        for month in range(12):
            start_of_month = datetime(self.year.year, month, 1)
            month_hours_worked, month_gross_wage, month_tax_amount = self._calculate_given_month(start_of_month)

            hours_worked += month_hours_worked
            gross_wage += month_gross_wage
            tax_amount += month_tax_amount

        self._year_hours_worked = hours_worked
        self._year_gross_wage = gross_wage
        self._year_tax_amount = tax_amount

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
            self._calculate_this_month()

        return self._year_hours_worked

    @property
    def year_gross_wage(self):
        if self._year_gross_wage is None:
            self._calculate_this_month()

        return self._year_gross_wage

    @property
    def year_tax_amount(self):
        if self._year_tax_amount is None:
            self._calculate_this_month()

        return self._year_tax_amount

    @property
    def month_hour_rate(self):
        return self.month_gross_wage / self.month_hours_worked

    @property
    def year_hour_rate(self):
        return self.year_gross_wage / self.year_hours_worked

    def month_net_wage(self):
        return self.month_gross_wage - self.month_tax_amount

    def year_net_wage(self):
        return self.year_gross_wage - self.year_tax_amount

    def month_available_hours(self):
        return


class ApiAdminMonthTableHandler(BaseHandler):

    def get(self, date):
        month = str_ops.datetime_from_iso_str(date).replace(day=1)
        next_month = month + relativedelta(months=1)

        rows = []

        users = udb.get_users(self.mdb.users)
        for user in users:
            # TODO tady je edge case: smlouva a dokumenty s kontrolují k prvnímu dnu v měsíci
            # a je předpoklad, že platí celý měsíc!
            active_contract = udb.get_user_active_contract(self.mdb.users, user["_id"], month)
            apply_deduction = bool(udb.get_user_active_tax_declaration(self.mdb.users, user["_id"], month))
            apply_deduction_student = bool(udb.get_user_active_study_certificate(self.mdb.users, user["_id"], month))

            hour_rate = active_contract["hour_rate"] if active_contract else 0
            month_workspans = adb.get_user_workspans(self.mdb, user["_id"], month, next_month)
            hours_worked = sum(ws["hours"] for ws in month_workspans)
            gross_wage = hours_worked * hour_rate
            tax_amount = calculate_tax(gross_wage,
                                       self.dpp_params["tax_rate"],
                                       self.dpp_params["tax_deduction"] if apply_deduction else 0,
                                       self.dpp_params["tax_deduction_student"] if apply_deduction_student else 0)
            net_wage = gross_wage - tax_amount

            row = {
                "id": user["_id"],
                "name": user.get("name", {}),
                "hours_worked": hours_worked,
                "hour_rate": hour_rate,
                "month_closed": user.get("month_closed", False),  # TODO tak jak nyní month_closed funguje nedává smysl,
                # v db je reprezentován bool hodnotou, ale to znamená že ta bude skákat každý měsíc. Větší smysl dává
                # mít pole months_closed or closed_months a do něj přidávat uzavřené měsíce (třeba data prvních dnů
                # v měsíci v iso tvaru.
                "gross_wage": gross_wage,
                "tax_amount": tax_amount,
                "net_wage": net_wage,
            }
            rows.append(row)

        self.write(bson.json_util.dumps(rows))


class ApiAdminYearTableHandler(BaseHandler):

    def get(self, date):
        year = str_ops.datetime_from_iso_str(date).replace(day=1, month=1)
        next_year = year + relativedelta(years=1)

        rows = []

        users = udb.get_users(self.mdb.users)
        for user in users:
            active_contract = udb.get_user_active_contract(self.mdb.users, user["_id"])
            hour_rate = active_contract["hour_rate"] if active_contract else 0
            year_workspans = adb.get_user_workspans(self.mdb, user["_id"], year, next_year)
            hours_worked = sum(ws["hours"] for ws in year_workspans)
            gross_wage = hours_worked * hour_rate
            tax_amount = 0
            net_wage = gross_wage - tax_amount

            row = {
                "id": user["_id"],
                "name": user.get("name", {}),
                "hours_worked": hours_worked,
                "hour_rate": hour_rate,
                "gross_wage": gross_wage,
                "tax_amount": tax_amount,
                "net_wage": net_wage,
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
            # "year_days_of_vacation": get_user_year_days_of_vacation(self.mdb.users, user_id, date)
        }
        # template_params.update(compile_user_month_info(self.mdb.users, user_id, datetime.now()))

        self.render("attendance.home.hbs", **template_params)


class ApiCalendarHandler(BaseHandler):

    def post(self, user_id, date):
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

        data = compile_user_month_info(self.mdb, user_id, month,
                                       self.dpp_params["year_max_hours"],
                                       self.dpp_params["month_max_gross_wage"])
        data["year_days_of_vacation"] = get_user_days_of_vacation_in_year(self.mdb, user_id, month)

        self.write(bson.json_util.dumps(data))


class ApiAddWorkspanHandler(BaseHandler):

    def post(self, user_id):
        req = self.request.body.decode("utf-8")
        form_data = bson.json_util.loads(req)

        today = str_ops.datetime_from_iso_str(form_data["date"])

        workspan = {}
        workspan["from"] = str_ops.datetime_from_iso_string_and_time_string(form_data["date"], form_data["from"])
        workspan["hours"] = float(form_data["hours"])
        workspan["assignment"] = form_data["assignment"]

        for doctype in ["study_certificate", "tax_declaration"]:
            document_mdoc = udb.get_user_active_document(self.mdb.users, user_id, doctype, today)
            workspan[doctype] = document_mdoc["_id"] if document_mdoc else None

        contract_mdoc = udb.get_user_active_contract(self.mdb.users, user_id, today)
        workspan["contract"] = contract_mdoc["_id"] if contract_mdoc else None

        self.check_vacations_conflicts(user_id, workspan)
        self.check_workspans_conflicts(user_id, workspan)

        print("ukladam workspan", workspan)

        adb.add_user_workspan(self.mdb, user_id, workspan)

    def check_vacations_conflicts(self, user_id, workspan):
        # z databáze dostaneme dovolené končící dnes nebo později seřazené podle data konce.
        # první dovolená je nejblíž, stačí tedy zkontrolovat, jestli začíná dnes nebo dříve.
        today = workspan["from"].replace(hour=0, minute=0, second=0, microsecond=0)
        vacations = adb.get_user_vacations(self.mdb, user_id, today)
        if vacations and vacations[0]["from"] <= workspan["from"]:
            raise BadInputError("Na dovolené se nepracuje.")

    def check_workspans_conflicts(self, user_id, workspan):
        today = workspan["from"].replace(hour=0, minute=0, second=0, microsecond=0)
        tomorow = today + relativedelta(days=1)

        todays_workspans = adb.get_user_workspans(self.mdb, user_id, today, tomorow)
        workspan_end = workspan["from"] + relativedelta(minutes=int(workspan["hours"] * 60))

        for other_ws in todays_workspans:
            latest_start = max(workspan["from"], other_ws["from"])
            earliest_end = min(workspan_end, other_ws["from"] + relativedelta(minutes=int(other_ws["hours"]) * 60))

            if latest_start < earliest_end:
                raise BadInputError("Časový konflikt s jinou prací.")


class ApiAddVacationHandler(BaseHandler):

    def post(self, user_id):
        # TODO hlídat aby nové dovolené byly v budoucnosti, nelze přidat dovolenou zpětně
        # TODO dovolené by měly jít v půlce přerušit aniž by musely být smazané
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
