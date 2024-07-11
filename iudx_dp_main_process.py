# import statements
import scripts.medicalPipeline as medpipe
import scripts.spatioTemporalPipeline as stpipe
import scripts.utilities as utils
import json

# for testing
medicalFileList = ["data/syntheticMedicalChunks/medical_data_split_file_0.json",
                    "data/syntheticMedicalChunks/medical_data_split_file_1.json",
                    "data/syntheticMedicalChunks/medical_data_split_file_2.json",
                    "data/syntheticMedicalChunks/medical_data_split_file_3.json",
                    "data/syntheticMedicalChunks/medical_data_split_file_4.json"
                    ]


spatioTemporalFileList = ['data/spatioTemporalChunks/split_file_0.json',
            'data/spatioTemporalChunks/split_file_1.json',
            'data/spatioTemporalChunks/split_file_2.json',
            'data/spatioTemporalChunks/split_file_3.json',
            'data/spatioTemporalChunks/split_file_4.json',
]


# function to handle dataset choice
def dataset_handler(config):
    if config["data_type"] == "medical":
        config = config["medical"] # for testing only
        dataset = "medical"
        fileList = medicalFileList
    elif config["data_type"] == "spatioTemporal":
        config = config["spatioTemporal"] # for testing only 
        dataset = "spatioTemporal"
        fileList = spatioTemporalFileList
    return dataset, config, fileList


def main_process(config, operations):
    # checking the dataset order of operations selected
    dataset, config, fileList = dataset_handler(config)
    print(dataset, operations)

    # selecting appropriate pipeline
    if dataset == "medical": 
        try:
            data = medpipe.medicalPipeline(config, operations, fileList)
        except Exception as e:
            print("Error: ", e)
            data = []
    if dataset == "spatioTemporal":
        try:
            data = stpipe.spatioTemporalPipeline(config, operations, fileList)
        except Exception as e:
            print("Error: ", e)
            data = []
    return data

    # TODO: Add output format handling (json dumps)
    # mods.output_handler(data, config)




# formatted_data = utils.output_handler(data)
