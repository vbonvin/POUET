.. _qol:

Quality of Life Improvements
============================

POUET provides a bunch of interesting features that can make your life much more comfortable. Here is what you should know.

Save your catalogs in .pouet format
***********************************

Any catalog successfully imported can be saved in a .pouet format, using the ``Export selected`` button at the bottom left of the ``Observations`` tab.

  .. figure:: plots/POUET_export.png
    :align: center
    :alt: POUET export buttons
    :figclass: align-center

    Export-related widgets, located at the bottom of the ``Observations`` tab

The advantage of having your catalog in a .pouet format is that they can be loaded without prompting any import-related questions. Only the selected targets are written when you click on ``Export selected``, which allows you to trim down your list according to whichever criteria you find useful. The path is to be entered in the ``Save path`` field.


The ``Overwrite`` checkbox, checked by default, ensure that your fully replace any existing catalog when exporting. If unchecked, the selected OBs will be *added* to the existing catalog, thus allowing you to build .pouet catalogs combining targets from various other catalogs.

.. note:: A safer export function, warning you when you are about to erase an existing catalog as well as a rollback mode will be available in v0.4.


Export the list of selected names
*********************************

Say you know which targets from your catalog you plan to observe, and you would like to access the list of names quickly to copy/paste it somewhere. This can be done by clicking on the ``Show selected names`` at the bottom right of the ``Observations`` tab. This will prompt a pop-up with the names of all the selected targets from the list view.

  .. figure:: plots/POUET_selectednames.png
    :align: center
    :alt: POUET selected names
    :figclass: align-center

    The pop-up that appears after clicking on the ``Show selected names`` button.



Change the default obsprogram/create a new obsprogram file
**********************************************************

The default obsprogram parameters can be accessed in ``pouet/obsprogram/progdefault.py``. It can be accessed and modified with any text editor.

  .. figure:: plots/POUET_default_obsprogram.png
    :align: center
    :alt: POUET obsprogram default
    :figclass: align-center

This file contains a couple of functions we are still playing with (keep in mind that POUET is still under development) and that are currently not used. The only values of interest are the ``minangletomoon`` and ``maxairmass``, that define the observability of your targets once loaded in POUET. To change the default behaviour of POUET, simply edit these values.

If you work with multiple kind of targets that have various angle to moon and airmass requirements, you can also create new obsprogram files. Simply copy/paste the ``progdefault.py`` file, rename it as ``prog%YOUROBSPROGRAMNAME%.py`` and edit its value. When loading a new catalog in POUET, your new obspgrogram will appear in the obsgprogram popup selection.


.. note:: The obsprogram files are read each time you import a new catalog. If you have a POUET instance launched and edit the obsprogram files on the fly, you should reload your catalogs for the effects to take change, no choice.

