****************************
Welcome to POUET's tutorial!
****************************

This section covers the basics of POUET usage.


Installation...
===============

...is currently not required. Simply clone/download the repository and move to its root.

Make sure you have all the requirements installed

::
    pip install docs/requirements.txt

.. note:: Compatibility with older version of the required modules has not been assessed, but might be working. If you find any backward compatibility, please `let us know <https://github.com/vbonvin/POUET>`_


Tree structure
==============

  * ``archives`` contains old pieces of code (will disappear in a future version)
  * ``cats`` contains the catalogs loaded/savec by POUET
  * ``docs`` contains the documentation and requirement files
  * ``misc`` contains stuff (will disappear in a future version)
  * ``pouet`` contains the source code
  * ``standalone`` contains standalone version of the plots (will disappear in a future version)
  * ``tests`` contains a series of tests to ensure smooth continuous integration


Basic usage
===========


Start-up
********

From the root directory:
::
  python pouet/main.py


This will launch POUET in a dedicated window.


Lots of buttons
***************

And they all serve a purpose. Here's what an open session of POUET looks like:


.. figure:: plots/POUET_mainwindow_colored.png
    :align: center
    :alt: POUET mainwindow
    :figclass: align-center

    A fresh POUET session, colored for the occasion


The red box at the top allows you to control the date and time.

The blue bow below allows you to display and check the properties of the targets in your catalog - from the ``Observations`` tab. The other tabs allow you to display observing site properties (``Station`` tab), POUET parameters (``Configuration`` tab) and see the log of the operations you performed so far (``View logs`` tab).

The inserted turquoise box allows a finer control of which targets are visible in the ``Observations`` tab.

The black box on the right contains the all sky display and visibility plots.


We will explore in more details these sections later on. For the moment, let's start by importing a bunch of targets into POUET.


Import a catalog
****************
POUET has been primarly designed to let you browse through a large list of targets (a catalog) and highligh/display only the targets of interest.

Thus, your targets need to be arranged in a catalog. A POUET catalog can be as simple as a tab separated file, where each line is a target and each column a property. The first line is a header and second line is a separator. The minimal required properties are the name, alpha (HH:MM:SS.sss) and delta coordinates (DD:MM:SS.sss). A minimal working catalog should look like this:
::
  name	alpha	delta
  ----	-----	-----
  HE0047-1756	00:50:27.83	-17:40:08.8
  J0158-4325	01:58:41.44	-43:25:04.1
  HE0230-2130	02:32:33.1	-21:17:26
  HE0435-1223	04:38:14.9	-12:17:14.4

The reading is done by :meth:`~obs.rdbimport()`, which is a simple wrapper around astropy.table.Table.read(). Whatever suits astropy should work with POUET as well.


To load your catalog in POUET, clic on ``Load catalog`` and chose your catalog. POUET will open it and read its header. You will then be prompted to associate the headers of your catalog with the ones POUET needs