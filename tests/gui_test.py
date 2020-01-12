"""
Testing script, v1
"""

import os, sys, threading, time, runpy

path = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), '../pouet')
sys.path.append(path)


import pouet.main as main
import unittest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

app = QApplication(sys.argv)



class PouetTest(unittest.TestCase):
	'''Test the pouet GUI'''


	def setUp(self):
		'''Create the GUI'''
		self.form = main.POUET()


	def test_load_catalog(self):

		pass

		"""
		# So far, I haven't found a way to test automatically the load import. The problem seems to be that the headerPopup is created as a modal window in the load_obs() function, because we execute it (.exec()) in order to force the user to make his choices and click on ok or cancel. 
		
		I bypass this behaviour by implementing an autotest_mode keyword, but this is by far not ideal...
		"""

		self.form.load_obs(filepath="../cats/example.cat", autotest_mode=True)


	def test_add_obs(self):
		self.form.add_obs()



	def test_obs_selection(self):
		self.form.toggleAlphaMinObs.setChecked(True)
		self.form.hide_observables()
		#self.form.ui.displaySelectedObs.clicked(True)


	"""
	def setFormToZero(self):
		'''Set all ingredients to zero in preparation for setting just one
		to a nonzero value.
		'''
		self.form.ui.tequilaScrollBar.setValue(0)
		self.form.ui.tripleSecSpinBox.setValue(0)
		self.form.ui.limeJuiceLineEdit.setText("0.0")
		self.form.ui.iceHorizontalSlider.setValue(0)

	def test_defaults(self):
		'''Test the GUI in its default state'''
		self.assertEqual(self.form.ui.tequilaScrollBar.value(), 8)
		self.assertEqual(self.form.ui.tripleSecSpinBox.value(), 4)
		self.assertEqual(self.form.ui.limeJuiceLineEdit.text(), "12.0")
		self.assertEqual(self.form.ui.iceHorizontalSlider.value(), 12)
		self.assertEqual(self.form.ui.speedButtonGroup.checkedButton().text(), "&Karate Chop")

		# Class is in the default state even without pressing OK
		self.assertEqual(self.form.jiggers, 36.0)
		self.assertEqual(self.form.speedName, "&Karate Chop")

		# Push OK with the left mouse button
		okWidget = self.form.ui.buttonBox.button(self.form.ui.buttonBox.Ok)
		QTest.mouseClick(okWidget, Qt.LeftButton)
		self.assertEqual(self.form.jiggers, 36.0)
		self.assertEqual(self.form.speedName, "&Karate Chop")

	def test_tequilaScrollBar(self):
		'''Test the tequila scroll bar'''
		self.setFormToZero()

		# Test the maximum.  This one goes to 11.
		self.form.ui.tequilaScrollBar.setValue(12)
		self.assertEqual(self.form.ui.tequilaScrollBar.value(), 11)

		# Test the minimum of zero.
		self.form.ui.tequilaScrollBar.setValue(-1)
		self.assertEqual(self.form.ui.tequilaScrollBar.value(), 0)

		self.form.ui.tequilaScrollBar.setValue(5)

		# Push OK with the left mouse button
		okWidget = self.form.ui.buttonBox.button(self.form.ui.buttonBox.Ok)
		QTest.mouseClick(okWidget, Qt.LeftButton)
		self.assertEqual(self.form.jiggers, 5)

	def test_tripleSecSpinBox(self):
		'''Test the triple sec spin box.
		Testing the minimum and maximum is left as an exercise for the reader.
		'''
		self.setFormToZero()
		self.form.ui.tripleSecSpinBox.setValue(2)

		# Push OK with the left mouse button
		okWidget = self.form.ui.buttonBox.button(self.form.ui.buttonBox.Ok)
		QTest.mouseClick(okWidget, Qt.LeftButton)
		self.assertEqual(self.form.jiggers, 2)

	def test_limeJuiceLineEdit(self):
		'''Test the lime juice line edit.
		Testing the minimum and maximum is left as an exercise for the reader.
		'''
		self.setFormToZero()
		# Clear and then type "3.5" into the lineEdit widget
		self.form.ui.limeJuiceLineEdit.clear()
		QTest.keyClicks(self.form.ui.limeJuiceLineEdit, "3.5")

		# Push OK with the left mouse button
		okWidget = self.form.ui.buttonBox.button(self.form.ui.buttonBox.Ok)
		QTest.mouseClick(okWidget, Qt.LeftButton)
		self.assertEqual(self.form.jiggers, 3.5)

	def test_iceHorizontalSlider(self):
		'''Test the ice slider.
		Testing the minimum and maximum is left as an exercise for the reader.
		'''
		self.setFormToZero()
		self.form.ui.iceHorizontalSlider.setValue(4)

		# Push OK with the left mouse button
		okWidget = self.form.ui.buttonBox.button(self.form.ui.buttonBox.Ok)
		QTest.mouseClick(okWidget, Qt.LeftButton)
		self.assertEqual(self.form.jiggers, 4)

	def test_liters(self):
		'''Test the jiggers-to-liters conversion.'''
		self.setFormToZero()
		self.assertAlmostEqual(self.form.liters, 0.0)
		self.form.ui.iceHorizontalSlider.setValue(1)
		self.assertAlmostEqual(self.form.liters, 0.0444)
		self.form.ui.iceHorizontalSlider.setValue(2)
		self.assertAlmostEqual(self.form.liters, 0.0444 * 2)

	def test_blenderSpeedButtons(self):
		'''Test the blender speed buttons'''
		self.form.ui.speedButton1.click()
		self.assertEqual(self.form.speedName, "&Mix")
		self.form.ui.speedButton2.click()
		self.assertEqual(self.form.speedName, "&Whip")
		self.form.ui.speedButton3.click()
		self.assertEqual(self.form.speedName, "&Puree")
		self.form.ui.speedButton4.click()
		self.assertEqual(self.form.speedName, "&Chop")
		self.form.ui.speedButton5.click()
		self.assertEqual(self.form.speedName, "&Karate Chop")
		self.form.ui.speedButton6.click()
		self.assertEqual(self.form.speedName, "&Beat")
		self.form.ui.speedButton7.click()
		self.assertEqual(self.form.speedName, "&Smash")
		self.form.ui.speedButton8.click()
		self.assertEqual(self.form.speedName, "&Liquefy")
		self.form.ui.speedButton9.click()
		self.assertEqual(self.form.speedName, "&Vaporize")
	"""


if __name__ == "__main__":

	unittest.main()
