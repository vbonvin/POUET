.. _warningmessages:

Understand the warning messages
===============================

There are two kinds of warning messages. The ones that tell you something is wrong with POUET's code (bad ones, report them `here <https://github.com/vbonvin/POUET/issues>`_) and the ones that tell you to pay attention to what's happening. In this page, we focus on the latter.


General status of POUET
***********************

At the center top of the main window is a small box. POUET uses this box to print all kind of messages

  .. figure:: plots/POUET_green.png
    :align: center
    :alt: POUET all good display
    :figclass: align-center

  .. figure:: plots/POUET_yellow.png
    :align: center
    :alt: POUET loading display
    :figclass: align-center

    Examples of status messages

You can see it as a simplified log to let you know the status of the most recent task performed by POUET. A green message tells you that things happened as expected (catalog successfully loaded, all-sky image successfully downloaded) , a yellow message tells you that a task is currently being processed by POUET (retrieving a finding chart, refreshing the weather display...) and a red message tells you that something went wrong (loading catalog does not comply with POUET's import standards, no connexion to the weather service, etc...). To each of these simplified messages corresponds one or more detailed entries in the ``Log`` tab.



Pointing limit
**************

Usually, when the wind blows above a certain limit, you will want to avoid pointing the telescope in the wind direction (+- 90 degree from the wind). The pointing limit is defined as 15m/s, but can be changed by the user before launching POUET (see :ref:`customsite`). When the measured speed exceed this threshold, a hatched grid will appear on the all-sky and visibility views to indicate which regions are not accessible. The targets in the list view will have their respective Wind cells paint in red.

  .. figure:: plots/POUET_pointinglimit.png
    :align: center
    :alt: POUET pointing limit
    :figclass: align-center

    When the wind blows too hard, a pointing limit grid appears on the displays.


If the wind blows really too hard, then the telescope should be closed for safety measures. Most modern telescopes have automatic closing procedures (either a closing signal sent to the telescope, or a human operator forcing you to close it) but just in case you are all alone and don't pay too much attention to your official weather report, POUET sends you a visual reminder.

  .. figure:: plots/POUET_strongwind.png
    :align: center
    :alt: POUET pointing limit
    :figclass: align-center

    When the wind blows really too hard, POUET reminds you that no observations are possible.

POUET closing limit is 20m/s, and as the pointing limit can be changed (see :ref:`customsite`). As an extra warning, note that in both cases the ``Station`` tab changed color (yellow for pointing limit, red for closing limit)