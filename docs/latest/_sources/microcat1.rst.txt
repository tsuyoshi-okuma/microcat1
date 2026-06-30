module microcat1
================

.. automodule:: microcat1
   :members:
   :exclude-members: SEC_NONE, SEC_PAP, SEC_CHAP, STATE_INACTIVE, STATE_ACTIVE, STATE_ERROR, STATE_CONNECTING, STATE_CONNECTED

Constants
---------

Security types are re-exported from :class:`network.PPP`. The ``STATE_*`` values
name the PPP connection states reported by :meth:`modem.status`.

.. autodata:: microcat1.SEC_NONE

.. autodata:: microcat1.SEC_PAP

.. autodata:: microcat1.SEC_CHAP

.. autodata:: microcat1.STATE_INACTIVE

.. autodata:: microcat1.STATE_ACTIVE

.. autodata:: microcat1.STATE_ERROR

.. autodata:: microcat1.STATE_CONNECTING

.. autodata:: microcat1.STATE_CONNECTED
