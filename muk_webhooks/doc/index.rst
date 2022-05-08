=====================
MuK Webhooks for Odoo
=====================

Webhooks are user-defined HTTP callbacks that can be used to perform push notifications.
They are usually triggered by some event, such as creating a new partner or a comment
being posted to a blog. When that event occurs, Odoo makes an HTTP request to the URL
configured for the webhook. Webhooks can easily configured and customized in the backend.


Requirements
============

OAuthLib
-------------

A generic, spec-compliant, thorough implementation of the OAuth request-signinglogic
for Python. To install OAuthLib please follow the `instructions <https://pypi.org/project/oauthlib/>`_
or install the library via pip.

``pip install oauthlib``

Requests-OAuthlib
-----------------

Requests-OAuthlib uses the Python Requests and OAuthlib libraries to provide an
easy-to-use Python interface for building OAuth1 and OAuth2 clients. To install
Requests-OAuthlib please follow the `instructions <https://requests-oauthlib.readthedocs.io/>`_
or install the library via pip.

``pip install requests requests_oauthlib``


Installation
============

To install this module, you need to:

Download the module and add it to your Odoo addons folder. Afterward, log on to
your Odoo server and go to the Apps menu. Trigger the debug mode and update the
list by clicking on the "Update Apps List" link. Now install the module by
clicking on the install button.

Another way to install this module is via the package management for Python
(`PyPI <https://pypi.org/project/pip/>`_).

To install our modules using the package manager make sure
`odoo-autodiscover <https://pypi.org/project/odoo-autodiscover/>`_ is installed
correctly. Note that for Odoo version 11.0 and later this is not necessary anymore. 
Then open a console and install the module by entering the following command:

``pip install --extra-index-url https://nexus.mukit.at/repository/odoo/simple <module>``

The module name consists of the Odoo version and the module name, where
underscores are replaced by a dash.

**Module:**

``odoo<version>-addon-<module_name>``

**Example:**

``sudo -H pip3 install --extra-index-url https://nexus.mukit.at/repository/odoo/simple odoo13-addon-muk-utils``

Once the installation has been successfully completed, the app is already in the
correct folder. Log on to your Odoo server and go to the Apps menu. Trigger the
debug mode and update the list by clicking on the "Update Apps List" link. Now
install the module by clicking on the install button.

The biggest advantage of this variant is that you can now also update the app
using the "pip" command. To do this, enter the following command in your console:

``pip install --upgrade --extra-index-url https://nexus.mukit.at/repository/odoo/simple <module>``

When the process is finished, restart your server and update the application in
Odoo. The steps are the same as for the installation only the button has changed
from "Install" to "Upgrade".

You can also view available Apps directly in our `repository <https://nexus.mukit.at/#browse/browse:odoo>`_
and find a more detailed installation guide on our `website <https://mukit.at/page/open-source>`_.

For modules licensed under a proprietary license, you will receive the access data after you purchased
the module. If the purchase were made at the Odoo store please contact our `support <support@mukit.at>`_
with a confirmation of the purchase to receive the corresponding access data.

Upgrade
============

To upgrade this module, you need to:

Download the module and add it to your Odoo addons folder. Restart the server
and log on to your Odoo server. Select the Apps menu and upgrade the module by
clicking on the upgrade button.

If you installed the module using the "pip" command, you can also update the
module in the same way. Just type the following command into the console:

``pip install --upgrade --extra-index-url https://nexus.mukit.at/repository/odoo/simple <module>``

When the process is finished, restart your server and update the application in
Odoo, just like you would normally.


Configuration
=============

To configure this module, you need to:

#. Go to *Settings -> Webhooks -> Automation*.
#. Click on *Create* to create a new webhook and customize it to your needs. 


Usage
=====

After creating a webhook it is automatically triggered by the system.

Credit
======

Contributors
------------

* Mathias Markl <mathias.markl@mukit.at>

Images
------

Some pictures are based on or inspired by:

* `Prosymbols <https://www.flaticon.com/authors/prosymbols>`_
* `Smashicons <https://www.flaticon.com/authors/smashicons>`_


Author & Maintainer
-------------------

This module is maintained by the `MuK IT GmbH <https://www.mukit.at/>`_.

MuK IT is an Austrian company specialized in customizing and extending Odoo.
We develop custom solutions for your individual needs to help you focus on
your strength and expertise to grow your business.

If you want to get in touch please contact us via `mail <sale@mukit.at>`_
or visit our `website  <https://mukit.at>`_.
