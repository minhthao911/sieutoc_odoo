# -*- coding: utf-8 -*-
import re
import uuid
from odoo import models, fields, _


class EmployeeAttendance(models.Model):
    _inherit = "hr.attendance"
    _description = " Employee Attendance"

    checkin_location = fields.Char(string="Check In Location")
    ckeckin_ipaddress = fields.Char(string="Check In IP Address")
    checkin_mask = fields.Char(string="Check In Mac Address")
    checkout_location = fields.Char(string="Check Out Location")
    ckeckout_ipaddress = fields.Char(string="Check Out Ip Address")
    checkout_mask = fields.Char(string="Check Out Mac Address")


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def attendance_manual(self, next_action, entered_pin=None, ipaddress=None, location=None):
        self.ensure_one()
        can_check_without_pin = not self.env.user.has_group('hr_attendance.group_hr_attendance_use_pin') or (self.user_id == self.env.user and entered_pin is None and entered_pin)
        if can_check_without_pin or entered_pin is not None and entered_pin == self.sudo().pin:
            return self.with_context(ipaddress=ipaddress, location=location)._attendance_action(next_action)
        return {'warning': _('Wrong PIN')}

    def _attendance_action_change(self):
        res = super(HrEmployee, self)._attendance_action_change()
        if self._context.get('ipaddress') or self._context.get('location'):
            ipaddress = self._context.get('ipaddress')
            location = self._context.get('location')
            macaddress = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
            if self.attendance_state == 'checked_in':
                res['ckeckin_ipaddress'] = ipaddress
                res['checkin_location'] = location
                res['checkin_mask'] = macaddress
            else:
                res['ckeckout_ipaddress'] = ipaddress
                res['checkout_location'] = location
                res['checkout_mask'] = macaddress
        return res
