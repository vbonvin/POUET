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


If the wind blows really too hard, then the telescope should be closed for safety measures. Most modern telescopes have automatic closing procedures (either a closing signal sent to the telescope, or a human operator forcing you to close it) but just in case you are all alone and don't pay too much attention to your official weather report, POUET displays a visual reminder in both the visibility and all-sky views.

  .. figure:: plots/POUET_strongwind.png
    :align: center
    :alt: POUET pointing limit
    :figclass: align-center

    When the wind blows really too hard, POUET reminds you that no observations are possible.

POUET closing limit is 20m/s, and as the pointing limit can be changed (see :ref:`customsite`). As an extra warning, note that in both cases the ``Station`` tab changed color (yellow for pointing limit, red for closing limit)


Clouds detection
****************

The approach chosen in POUET to detect clouds is very straightforward: small boxes are drawn on the all sky image and a peak detection algorithm counts how many stars are visible. If that number is large enough, then POUET assumes the sky is clear and paint the all-sky in green. A Gaussian filtering is also applied to reduce the false cloud detection due to the presence of the moon.

The number of stars per box has been optimized to match a visual detection from the `Danish telescope AllSky Camera <http://allsky-dk154.asu.cas.cz>`_. If you plan to use another all-sky (see :ref:`customsite`), the cloud detection algorithm might need some adaptation.


A target behind the clouds will have its cloud flag ``C`` in the list view painted in red with a value of 0, and, of course, appears in a correspondingly red region in the all-sky display. The yellow regions corresponds to areas with a cloud density between thin and thick; you can still hope for some flux if you do e.g. spectroscopy of bright objects, but don't even attempt to do photometric observations, unless you are really desperate (The "I'm-a-PhD-student-whose-thesis-can-be-awarded-only-if-I-get-these-observations-done-tonight" kind of desperate).


  .. figure:: plots/POUET_cloudswarning.png
    :align: center
    :alt: POUET clouds limit
    :figclass: align-center

    When everyone else is closed because of bad weather, the smart POUET user knows he can still observe WFI2033.



Moon distance
*************

In a similar fashion than the wind limit or cloud coverage, a target too close to the moon will have its ``M`` box in the list view painted in red. The default minimum moon distance is 30 degree, but can of course be changed (see :ref:`qol`)


  .. figure:: plots/POUET_moonwarning.png
    :align: center
    :alt: POUET moon warning
    :figclass: align-center

    HE0047-1743 is too close to the moon.

The same warning flag exists for the distance to the Sun, ``S``.


No internet connexion
*********************

Observatories are remote places, whose network connections are sometimes hectic. POUET works as best as it could in offline mode. Of course, the all-sky view will be disabled, similarly to the finding charts