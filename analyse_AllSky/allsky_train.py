import numpy as np
import util

import matplotlib.pyplot as plt
import matplotlib.cm as cm

from sklearn.ensemble import AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier

def compute_pca(data, n_components=None):
	"""
	Get the PCA decomposition according to:
	http://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html
	"""
	from sklearn.decomposition import FastICA
	
	pca = FastICA(n_components=n_components)
	pca.fit(data)
	
	return pca

id_im, coords, datas, labels = util.readpickle('db.pkl')
id_im = np.asarray(id_im)
labels = np.asarray(labels)

clabels = np.zeros(len(labels))
for ii, label in enumerate(labels):
	if label == 's':
		clabels[ii] = 0
	elif label == 'c':
		clabels[ii] = 1#0.25
	elif label == 'm':
		clabels[ii] = 0#0.5
	elif label == 'u':
		clabels[ii] = -1.#0.75

id_keep = np.where(clabels > -1)[0]
id_im = id_im[id_keep]
coords = coords[id_keep]
datas = datas[id_keep]
labels = labels[id_keep]
clabels = clabels[id_keep]

#idre = np.where(np.isnan(datas))
#datas[idre] = 0.
#exit()
#datas = np.log10(datas)

#datas = filters.gaussian_filter(datas,3)
pca = compute_pca(datas, n_components=100)
coeffs = pca.transform(datas)

fig1 = plt.figure()
ax = fig1.add_subplot(111)
stuff = ax.scatter(coeffs[:,0], coeffs[:,1], color=cm.jet(clabels))
plt.title('train')

# Create and fit an AdaBoosted decision tree
bdt = AdaBoostClassifier(DecisionTreeClassifier(max_depth=20),
                         algorithm="SAMME",
                         n_estimators=len(clabels))

bdt.fit(coeffs, clabels)


classifiedlabels = bdt.predict(coeffs)

fig1 = plt.figure()
ax = fig1.add_subplot(111)
stuff = ax.scatter(coeffs[:,0], coeffs[:,1], color=cm.jet(classifiedlabels))
plt.title('test')

classifier = bdt#logistic_classifier
util.writepickle([pca, classifier], 'cclas.pkl')
plt.show()
