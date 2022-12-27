# File created to store modules for Differential Privacy
# Modules:
# 1. Filter/Suppress
# 2. Generalization
# 3. Aggregation
# 4. Differential Privacy (noise addition)
import pandas as pd
import numpy as np
import json
import jsonschema
from pandas.io.json import json_normalize
import matplotlib.pyplot as plt
import h3

def categorize(dataframe, configFile,genType):
    if genType == "spatio-temporal":
        dataframe = spatioTemporalGeneralization(dataframe, configFile)
    elif genType == "numeric":
        dataframe = numericGeneralization(dataframe)
    # TODO: introduce new categories
    return dataframe

def spatioTemporalGeneralization(dataframe, configFile):
    # separating latitude and longitude from location
    lat_lon = dataframe[configFile['locationCol']]
    split_lat_lon = lat_lon.astype(str).str.strip('[]').str.split(', ')
    lon = split_lat_lon.apply(lambda x: x[0])
    lat = split_lat_lon.apply(lambda x: x[1])

    #assigning h3 index to the latitude and longitude coordinates in separate dataframe  
    dfLen = len(dataframe)
    h3index = [None] * dfLen
    resolution = configFile["h3Resolution"]
    for i in range(dfLen):
        h3index[i] = h3.geo_to_h3(lat=float(lat[i]), lng=float(lon[i]), resolution=resolution)
    dataframe["h3index"] = h3index

    # assigning date and time to separate dataframe and creating a timeslot column
    dataframe["Date"] = pd.to_datetime(dataframe[configFile["datetimeCol"]]).dt.date
    dataframe["Time"] = pd.to_datetime(dataframe[configFile["datetimeCol"]]).dt.time
    time = dataframe["Time"]
    dataframe["Timeslot"] = time.apply(lambda x: x.hour)

    # assigning HATs from H3index and timeslot
    dataframe["HAT"] = ( dataframe["Timeslot"].astype(str) + " " + dataframe["h3index"])

    # Filtering time slots by start and end time from config file
    startTime = configFile["startTime"]
    endTime = configFile["endTime"]
    groupByColumn = configFile["groupByCol"]
    dataframe = dataframe[(dataframe["Timeslot"] >= startTime) & (dataframe["Timeslot"] <= endTime) ]

    # Selecting h3 indices where a min number of events occur in all timeslots of the day
    f1 = (dataframe.groupby(["Timeslot", "Date", "h3index"]).agg({groupByColumn: "nunique"}).reset_index())
    f2 = f1.groupby(["Timeslot", "h3index"]).agg({groupByColumn: "sum"}).reset_index()
    date = dataframe["Date"].unique()
    minEventOccurences = int(configFile["minEventOccurences"])
    limit = len(date) * minEventOccurences
    f3 = f2[f2[groupByColumn] >= limit]
    f4 = f3.groupby("h3index").agg({"Timeslot": "count"}).reset_index()

    maxTimeslots = f4["Timeslot"].max()
    f5 = f4[f4["Timeslot"] == maxTimeslots]

    df = dataframe["h3index"].isin(f5["h3index"])
    dataframe = dataframe[df]
    return dataframe

def numericGeneralization(dataframe, configFile):
    #TODO
    return dataframe

def schemaValidator(schemaFile, configFile):
    schemaFile = '../config/' + schemaFile
    configFile = '../config/' + configFile

# Load the JSON schema
    with open(schemaFile, "r") as f:
        schema = json.load(f)

# Load the JSON document to validate
    with open(configFile, "r") as f:
        document = json.load(f)

# Validate the document against the schema
    jsonschema.validate(instance=document, schema=schema)
    return


def readFile(configFileName):
    #reading config
    configFile = '../config/' + configFileName
    with open(configFile, "r") as cfile:
        configDict = json.load(cfile)
    
    #reading datafile
    dataFileName = '../data/' + configDict['dataFile']
    with open(dataFileName, "r") as dfile:
        dataDict = json.load(dfile)
    
    #loading data
    dataframe = pd.json_normalize(dataDict)
    pd.set_option('mode.chained_assignment', None)
    print('The loaded file is: ' + dataFileName + ' with shape ' + str(dataframe.shape))
    
    genType = configDict['genType']
    configDict = configDict['spatio-temporal']

    #dropping duplicates based on config file parameters
    dupe1 = configDict['duplicateDetection'][0]
    dupe2 = configDict['duplicateDetection'][1]
    dfLen1 = len(dataframe)
    dfDrop = dataframe.drop_duplicates(subset = [dupe1, dupe2], inplace = False, ignore_index = True)
    dfLen2 = len(dfDrop)
    dupeCount = dfLen1 - dfLen2
    p1 = print(str(dupeCount) + ' duplicate rows have been removed.') 
    p2 = print(str(dfDrop.shape) + ' is the shape of the new dataframe.')
    dataframe = dfDrop  
    return dataframe, configDict, genType


def suppress(dataframe, configDict):
    dataframe = dataframe.drop(columns = configDict['suppressCols'])
    print("Dropping columns from configuration file...")
    print("The shape of the new dataframe is:")
    print(dataframe.shape)
    return dataframe
    
def aggregateStats1(dataframe, configDict):
    #output - average speed of bus passing through the specific H3index, TimeSlot and sensitivity

    #calculating locality factor from the config file
    localityFactor = 1 + configDict['localityFactor']

    #getting average speed for every license_plate in every HAT per day
    df = dataframe.groupby(['HAT','Date','license_plate']).agg({'speed':'mean'}).reset_index()
    
    #getting average of average speeds
    dfAgg = df.groupby('HAT').agg({'speed':'mean'}).reset_index()
    
    maxSpeed = dataframe['speed'].max() * localityFactor
    minSpeed = dataframe['speed'].min() * localityFactor
    
    #N is sum of number of unique license plates per HAT
    dfInter = dataframe.groupby(['HAT', 'Date']).agg({'license_plate':'nunique'}).reset_index()
    dfInter = dfInter.groupby(['HAT']).agg({'license_plate':'sum'}).reset_index()
    dfAgg['N'] = dfInter['license_plate']
    
    ############## DEPRECATED ################
    # calculating local sensitivity (value for each unique HAT)
    # localSensitivity = [None] * len(dfAgg)
    # localSensitivity = (maxSpeed - minSpeed)/dfAgg['N']
    # dfAgg['localSensitivity'] = localSensitivity
    ############## ########## ################

    #calculating global sensitivity (1 value)
    date = dataframe["Date"].unique()
    threshold = configDict['minEventOccurences'] * len(date)
    globalSensitivity = (configDict['globalMaxSpeed'] - configDict['globalMinSpeed'])/dfAgg['N'].min()

    dfAgg['globalSensitivity'] = globalSensitivity

    #finding 'K', the maximum number of HATs a bus passes through per day and delocalising using locality factor
    dfK = dataframe.groupby(['Date','license_plate']).agg({'HAT':'nunique'}).reset_index()
    K = dfK['HAT'].max()
    K = K * localityFactor

    #remove after testing
    # dfAgg.to_csv('test5.csv')
    return dfAgg, K
    
def variableNoiseAddition1(dataframe, configDict, K):
    #METHOD 1
    #calculating E' which is E/K where K is maximum number of HATs a bus passes through per day
    privacyLossBudgetEps = configDict['privacyLossBudgetEpsQuery1']
    epsPrime = privacyLossBudgetEps/K
    
    #calculating noise 'b' for each HAT based on sensitivity using b = E/S
    dfVariableNoise = dataframe
    b1 = dfVariableNoise['globalSensitivity']/epsPrime
    dfVariableNoise['b'] = np.random.laplace(0,b1, len(dfVariableNoise))
    dfVariableNoise['NoisySpeed'] = dfVariableNoise['speed'] + dfVariableNoise['b']
    dfVariableNoise['NoisySpeed'].clip(0, inplace = True)
    dfVariableNoise.to_csv('NoisySpeed.csv')

    # calculate SNR
    # compare the original query value to the noisy query
    snr1 = dfVariableNoise['speed'].mean()/((dfVariableNoise['speed']-dfVariableNoise['NoisySpeed']).mean())
    snr2 = dfVariableNoise['speed'].mean()/(np.abs(dfVariableNoise['speed'].mean()-dfVariableNoise['NoisySpeed']).mean())
    print(snr1, snr2)

    ############## DEPRECATED ################
    # #METHOD 2	
    # #calculating epsilon for b = 1, method applicable to global sensitivity
    # eps_b1 = K * dfVariableNoise['sensitivityFromConfig'].max()
    # # eps_b1 = dfVariableNoise['sensitivity'].sum()
    # print(eps_b1)
    
    # #computing required value of 'b' to meet the user-defined privacy budget
    # b_method2 = eps_b1/privacyBudgetEps
    # print(b_method2)
    # # print('For the chosen privacy loss budget (Epsilon) of: ' + str(eps) + ', the noise \'b\' to be added is: ' + str(b))
    
    # #adding noise 'b' to the average speed
    # dfVariableNoise['b_method2'] = np.random.laplace(0,b_method2, len(dfVariableNoise))		
    # dfVariableNoise['NoisySpeed2'] = dfVariableNoise['speed'] + dfVariableNoise['b_method2']
    # dfVariableNoise.to_csv('dfVariable.csv')
    ############## ########## ################
    return dfVariableNoise

    
def aggregateStats2(dataframe, configDict):
    #output - average number of instances a bus passes through a HAT over the input speed limit
    #dropping all records lower than the chosen speedLimit
    speedLimit = configDict['speedLimit']
    dataframe = dataframe[(dataframe['speed'] > speedLimit)]
    
    #getting maximum speed for every license_plate in every HAT per day
    df = dataframe.groupby(['HAT','license_plate','Date']).agg({'speed':'max'}).reset_index()
    
    #remove after testing
#	df.to_csv('statsTest2.csv')
    
    #N is number of unique license plates per HAT that meet speed limit requirement
    dfAgg = df.groupby(['HAT']).agg({'license_plate':'nunique'}).reset_index()
    dfAgg.rename(columns = {'license_plate':'N'}, inplace = True)
#	print(dfAgg)
    
    #calculating the number of days in the dataset
    startDay = df['Date'].min()
    endDay = df['Date'].max()
    timeRange = (endDay - startDay).days
    
    #Calculating the average number of buses per day
    dfAgg['avgNumBuses'] = dfAgg['N']/timeRange
    
    #Calculating the sensitivity
    sensitivity = 1/timeRange
    
    #remove after testing
#	dfAgg.to_csv('statsTest3.csv')
    return dfAgg, sensitivity


def plot(x, y):
    plt.xlabel('B')
    plt.ylabel('Worst Case Epsilon')
    xValues = x
    yValues = y
    plt.plot(x,y, marker = 'x')
#	plt.legend()
    plt.show()
    return