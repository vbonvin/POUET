.. _qol:

Quality of Life Improvements
============================


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

