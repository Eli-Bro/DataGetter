from pathlib import Path
import numpy as np

'''
Author(s): Created by Elijah Brown under the supervision of Dr. Kim
Date: June, 2022
Summary: The following program reads through all of the generated .txt files
found in the given directory, then compiles the data in a single .txt
file that resembles the desired features values and appropriate labels for
each gesture
'''

'''
Helper function that splits the given data into 3 stratified samples:
1. Training data with 80% of the total samples, and 8 occurrences of each gesture
2. Validation data with 10% of the total samples, and 1 occurrence of each gesture
3. Test data with 10% of the total samples, and 1 occurrence of each gesture
'''
def stratSplit(rawData):
    # Build the separated and shuffled list of arrays according to gesture number
    gestureList = []
    for gesture in range(8):
        startInd = gesture * 10
        endInd = startInd + 10
        gestureList.append(rawData[startInd:endInd, :])
        #Shuffle trials within a gesture
        np.random.shuffle(gestureList[gesture])

    stratTest = np.zeros((8, 13))
    stratVal = np.zeros((8, 13))
    stratTrain = np.zeros((64, 13))

    for num, array in enumerate(gestureList):
        stratTest[num, :] = array[0, :]

        stratVal[num, :] = array[1, :]

        startInd = num * 8
        endInd = startInd + 8
        stratTrain[startInd:endInd, :] = array[2:, :]

    #Shuffle each of the 3 sets to get rid of sequential ordering
    np.random.shuffle(stratTrain)
    np.random.shuffle(stratVal)
    np.random.shuffle(stratTest)

    #Overall data array begins with Train, then Validate, then Test
    finalData = np.vstack((stratTrain, stratVal, stratTest))

    # Normalize feature data (labels are left alone)
    finalX = finalData[:, 0:-1]
    finalXMean = np.mean(finalX, axis=0)
    finalXStd = np.mean(finalX, axis=0)
    finalX = finalX - finalXMean
    finalX = finalX / finalXStd

    finalData = np.c_[finalX, finalData[:, -1]]

    return finalData


#Set up file path variables
dirPath = 'C:/Users/Elijah Brown/SU2022RA/GestureData'
paths = Path(dirPath).glob('**/*.txt')

featureList = []
firstIter = True

#Loop through all gesture data files
for path in paths:
    #Load raw data from single trial
    trial = np.loadtxt(path)

    #Conduct feature engineering
    #TODO: Note - To add another feature, append new 6 element 1-d array to featureList
    featureList.append(np.std(trial, axis=0))
    #featureList.append(np.var(trial, axis=0))

    rms = np.sqrt(np.mean(trial**2, axis=0))
    #TODO: Took out 2.4 for normalization
    #rms = rms - 2.4
    featureList.append(rms)

    trialData = featureList[0]
    for feature in featureList[1:]:
        trialData = np.hstack((trialData, feature))

    #Add data label based on gesture
    path = str(path)
    gestureInd = path.find('trial') - 1
    gestureNum = int(path[gestureInd])
    trialData = np.append(trialData, gestureNum)

    #On first iteration, set up empty totalData array to start stack
    if firstIter:
        totalData = np.zeros((1, (len(featureList) * 6) + 1))
        firstIter = False

    #Add new feature array to total data
    totalData = np.vstack((totalData, trialData))

    #Reset feature list for next trial
    featureList = []

#Get rid of top blank line, spilt, normalize, and reorder data
totalData = np.delete(totalData, 0, 0)
totalData = stratSplit(totalData)

#Save file
fileName = input("Data File Name?\n")
if fileName == '':
    fileName = 'GDProcess(Untitled)'
np.savetxt(fileName, totalData, fmt='%.6e', delimiter='\t')
print('Final data array shape:\n' + str(totalData.shape))
