"""
Launch the application, link POUET functions to the design
"""


from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import obs, meteo, run
import design
from astropy import units as u
from astropy.time import Time

class POUET(QtWidgets.QMainWindow, design.Ui_POUET):


    def __init__(self, parent=None):
        super(POUET, self).__init__(parent)
        self.setupUi(self)

        # add here all the connections to the functions below
        self.retrieveObs.clicked.connect(self.retrieve_obs)
        self.weatherRefresh.clicked.connect(self.weather_refresh)
        self.allSkyRefresh.clicked.connect(self.allsky_refresh)


        self.currentmeteo = run.startup(name='LaSilla', cloudscheck=True, debugmode=False)

        # testing stuff at startup...

        """
        filepath = '2m2lenses.rdb'
        self.observables = obs.rdbimport(filepath, obsprogram="lens")
        run.refresh_status(self.observables, self.currentmeteo)
        for o in self.observables:
            o.get_observability(self.currentmeteo, cloudscheck=True, verbose=False)
        """

    def retrieve_obs(self):

        #todo: there's propably a simpler way to do it. Update when knowledge has increased.
        model = QtGui.QStandardItemModel(self.listObs)

        self.listObs.clearSpans()
        filepath = QtWidgets.QFileDialog.getOpenFileName(self,
                                                "Select a file")[0]

        #todo: implement an obsprogram retrieve function
        self.observables = obs.rdbimport(filepath, obsprogram="lens")
        run.refresh_status(self.currentmeteo, self.observables)


        for o in self.observables:
            o.get_observability(self.currentmeteo, cloudscheck=True, verbose=False)

            name = QtGui.QStandardItem(o.name)
            alpha = QtGui.QStandardItem(o.alpha.to_string(unit=u.hour, sep=':'))
            delta = QtGui.QStandardItem(o.delta.to_string(unit=u.degree, sep=':'))
            observability = QtGui.QStandardItem(str(o.observability))

            name.setCheckable(True)
            model.appendRow([name, alpha, delta, observability])


        self.listObs.setModel(model)


    def weather_refresh(self, refresh_time="now"):
        #todo: link refresh_time to a button or widget on the interface ? Could be useful for update on future time.

        if refresh_time == "now":
            obs_time = Time.now()
        else:
            obs_time = Time.now()
            pass

        run.refresh_status(meteo=self.currentmeteo, minimal=False if refresh_time == "now" else True, obs_time=obs_time)
        self.weatherWindSpeedValue.setText(str('%f.2' % self.currentmeteo.windspeed))
        self.weatherWindDirectionValue.setText(str('%f.2' % self.currentmeteo.winddirection))
        self.weatherLastUpdateValue.setText(str(obs_time.value).split('.')[0])


    def allsky_refresh(self):

        #todo: I manage to display the image, but cannot resize it for some reason. Only the first refresh works, after that more refresh do not update nor the image neither the new date...

        run.refresh_status(meteo=self.currentmeteo, minimal=False)
        pixmap = QtGui.QPixmap(self.currentmeteo.allsky.fimage)
        #todo: for some reasons, this does not work... ?
        pixmap.scaled(461, 346)
        scene = QtWidgets.QGraphicsScene()
        scene.addPixmap(pixmap)
        self.allSkyView.setScene(scene)
        self.allSkyUpdateValue.setText(str(self.currentmeteo.time.value).split('.')[0])





def main():
    app = QtWidgets.QApplication(sys.argv)  # A new instance of QApplication
    form = POUET()                 # We set the form to be our ExampleApp (design)
    form.show()                         # Show the form
    app.exec_()                         # and execute the app



if __name__ == '__main__':
    main()