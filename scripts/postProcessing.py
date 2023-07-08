import numpy as np

def postProcessing(dfNoise, configDict):
    #postprocessing ITMSQuery1
    globalMaxValue = configDict['globalMaxValue']
    globalMinValue = configDict['globalMinValue']
    dfFinalITMSQuery1 = dfNoise
    dfFinalITMSQuery1['queryNoisyOutput'].clip(globalMinValue, globalMaxValue, inplace = True)
    # if configDict['optimized'] == False:
    #     dfFinalITMSQuery1.drop(['queryOutput'], axis = 1, inplace = True)        
    # #postprocessing ITMS Query 2
    # dfFinalITMSQuery2 = dfNoiseITMSQuery2
    # dfFinalITMSQuery2['query2NoisyOutput'].clip(0, np.inf, inplace = True)
    # dfFinalITMSQuery2.drop(['query2Output'], axis = 1, inplace = True)
    
    return dfFinalITMSQuery1

def signalToNoise(snrAverage,configDict):
    # SNR Threshold
    snrUpperLimit = configDict['snrUpperLimit']
    snrLowerLimit = configDict['snrLowerLimit']

    if snrAverage < snrLowerLimit :
        print("Your Signal to Noise Ratio of " + str(round(snrAverage,3)) + " is below the bound.")
    elif snrAverage > snrUpperLimit:
        print("Your Signal to Noise Ratio of " + str(round(snrAverage,3)) + " is above the bound.")
    else:
        print("Your Signal to Noise Ratio of " + str(round(snrAverage,3)) + " is within the bounds.")
    return snrAverage

def cumulativeEpsilon(configDict):

    privacyLossBudgetQuery1 = configDict['privacyLossBudgetEpsQuery'][0]
    privacyLossBudgetQuery2 = configDict['privacyLossBudgetEpsQuery'][1]
    cumulativeEpsilon = privacyLossBudgetQuery1 + privacyLossBudgetQuery2
    print('\nYour Cumulative Epsilon for the displayed queries is: ' + str(cumulativeEpsilon))
    return cumulativeEpsilon

def outputFile(dfFinal, dataframeName):
    dfFinal.to_csv('../pipelineOutput/' + dataframeName + '.csv')
    return
