odoo.define('hr_attendance_location_ip_mac_address.attendance', function(require) {
    'use strict';
    var Attendance = require('hr_attendance.my_attendances');
    var Kiosk = require('hr_attendance.kiosk_confirm');

    Attendance.include({
        update_attendance: function() {
            var ipaddress;
            var location;
            var location_address;
            var self = this;

            function set_ipaddress_location(ipaddress, location_address) {
                location = location_address.toString();
                self._rpc({
                    model: 'hr.employee',
                    method: 'attendance_manual',
                    args: [
                        [self.employee.id],
                        'hr_attendance.hr_attendance_action_my_attendances', false,
                        ipaddress, location,
                    ],
                })
                .then(function(result) {
                    if (result.action) {
                        self.do_action(result.action);
                    } else if (result.warning) {
                        self.do_warn(result.warning);
                    }
                });
            };
            if (window.location.protocol == "https:") {
                $.get('https://api.ipgeolocation.io/ipgeo?apiKey=16ff66fcc37b4c3f881052a9f4a5745f', function(data) {
                    ipaddress = data.ip
                    location_address = [data.city, data.state_prov, data.zipcode, data.country_name]
                    set_ipaddress_location(ipaddress, location_address)
                });
            } else {
                $.get('http://ip-api.com/json', function(data) {
                    ipaddress = data.query
                    location_address = [data.city, data.regionName, data.zip, data.country]
                    set_ipaddress_location(ipaddress, location_address)
                });
            }
        },
    });

    Kiosk.include({
        events: _.extend({}, Kiosk.prototype.events, {
            "click .o_hr_attendance_sign_in_out_icon": _.debounce(function () {
                var self = this;
                var ipaddress;
                var location;
                var location_address;
                function set_ipaddress_location(ipaddress, location_address) {
                    location = location_address.toString();
                    self._rpc({
                        model: 'hr.employee',
                        method: 'attendance_manual',
                        args: [[self.employee_id], self.next_action, false, ipaddress, location],
                    })
                    .then(function(result) {
                        if (result.action) {
                            self.do_action(result.action);
                        } else if (result.warning) {
                            self.do_warn(result.warning);
                        }
                    });
                };

                if (window.location.protocol == "https:") {
                    $.get('https://api.ipgeolocation.io/ipgeo?apiKey=16ff66fcc37b4c3f881052a9f4a5745f', function(data) {
                        ipaddress = data.ip
                        location_address = [data.city, data.state_prov, data.zipcode, data.country_name]
                        set_ipaddress_location(ipaddress, location_address)
                    });
                } else {
                    $.get('http://ip-api.com/json', function(data) {
                        ipaddress = data.query
                        location_address = [data.city, data.regionName, data.zip, data.country]
                        set_ipaddress_location(ipaddress, location_address)
                    });
                }
            }, 200, true),
            'click .o_hr_attendance_pin_pad_button_ok': _.debounce(function() {
                var self = this;
                var ipaddress;
                var location;
                var location_address;
                this.$('.o_hr_attendance_pin_pad_button_ok').attr("disabled", "disabled");

                function set_ipaddress_location(ipaddress, location_address) {
                    location = location_address.toString();
                    self._rpc({
                        model: 'hr.employee',
                        method: 'attendance_manual',
                        args: [[self.employee_id], self.next_action, self.$('.o_hr_attendance_PINbox').val(), ipaddress, location],
                    })
                    .then(function(result) {
                        if (result.action) {
                            self.do_action(result.action);
                        } else if (result.warning) {
                            self.do_warn(result.warning);
                            self.$('.o_hr_attendance_PINbox').val('');
                            setTimeout( function() { self.$('.o_hr_attendance_pin_pad_button_ok').removeAttr("disabled"); }, 500);
                        }
                    });
                };
                if (window.location.protocol == "https:") {
                    $.get('https://api.ipgeolocation.io/ipgeo?apiKey=16ff66fcc37b4c3f881052a9f4a5745f', function(data) {
                        ipaddress = data.ip
                        location_address = [data.city, data.state_prov, data.zipcode, data.country_name]
                        set_ipaddress_location(ipaddress, location_address)
                    });
                } else {
                    $.get('http://ip-api.com/json', function(data) {
                        ipaddress = data.query
                        location_address = [data.city, data.regionName, data.zip, data.country]
                        set_ipaddress_location(ipaddress, location_address)
                    });
                }
            }, 200, true),
        }),
    });
});