.. _customsite:

POUET configuration files
=========================


Change the default configuration (general and Site)
***************************************************

The general POUET configuration file is found under ``pouet/config/settings.cfg``. This is a simple text file that is loaded when a POUET instance is launched. Simply edit the variables values to adapt POUET to your liking.

  .. figure:: plots/POUET_defaultconfig.png
    :align: center
    :alt: POUET settings
    :figclass: align-center


The default Site configuration file is found under ``pouet/config/LaSilla.cfg``. As above, the values of the parameters can be edited prior to launching a POUET instance.

  .. figure:: plots/POUET_siteconfig.png
    :align: center
    :alt: POUET site configuration
    :figclass: align-center


All these parameters are fully described in the config files. If you want to adjust the humidity and wind warning levels, you have to edit the ``windWarnLevel``, ``windLimitLevel``, ``humidityWarnLevel`` and ``humidityLimitLevel`` parameters of the ``LaSilla.cfg`` file.


Unless you work under very specific conditions, there should be no need to tweak the other parameters - we thus recommend you to go with the default settings.


.. note:: On-the-fly overriding of (most of) the default parameters from POUET's ``Configuration`` tab will be available in v0.4.


Adapt POUET to another observing site
*************************************

This feature, along with its tutorial, will be fully available in a future version of POUET (we target the official release version).

In the meantime, you can still change the default observing Site configuration, but beware that the allsky view will not be adapted anymore. You can deactivate it from the ``Configuration`` tab (see :ref:`alttabs`).


