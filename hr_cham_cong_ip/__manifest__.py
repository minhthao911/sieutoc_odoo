# -*- coding: utf-8 -*-
{
    'name': 'Attendance Location, IP & Mac Address',
    'summary': "Get Attendance Check In/Out Location, IP & Mac Address",
    'description': "Get Attendance Check In/Out Location, IP & Mac Address",

    'author': 'iPredict IT Solutions Pvt. Ltd.',
    'website': 'http://ipredictitsolutions.com',
    'support': 'ipredictitsolutions@gmail.com',

    'category': 'Human Resources',
    'version': '15.0.0.1.1',
    'depends': ['hr_attendance'],

    'data': [
        'views/hr_attendance_view.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'hr_attendance_location_ip_mac_address/static/src/js/attendance.js',
        ],
    },

    'price': 25,
    'currency': "EUR",
    'license': "OPL-1",

    'auto_install': False,
    'installable': True,

    'images': ['static/description/banner.png'],
    'pre_init_hook': 'pre_init_check',
}
