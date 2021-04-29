import sys
import os
import uuid 
import pickle

class TrackingClient():
    def __init__(self, run_id=None):
        self.id = run_id
        self.params = {}
        self.metrics = {}
        self.model = {}
    
    def log_params(self, params):
        self.params = {
            **self.params, 
            **params
        }
        
    def log_metrics(self, metrics):
        self.metrics = {
            **self.metrics, 
            **metrics
        }

    def log_model(self, model_type, model):
        self.model = {
            **self.model, 
            **{'type': model_type, 'fitted_model': model}
        }

    def save_tracking(self):
        try: 
            self.id = sys.argv[1]
        except IndexError:
            self.id = input("WARNING: To save the tracked metadata, please assign a unique ID for this training run: ")
        md_file = 'src/models/tracking/metadata/{}.pkl'.format(self.id) 
        metadata = {}
        for attr, value in self.__dict__.items():
            if attr != 'id' and value:
                metadata[attr] = value
        print("Tracking completed. The following metadata was tracked during training: {} \n".format(list(metadata.keys())) \
            + "Metadata will be saved in 'src/models/tracking/metadata' as '{}.pkl'.".format(self.id))
        try:
            with open(md_file, 'wb') as metadata_file:
                pickle.dump(metadata, metadata_file, pickle.HIGHEST_PROTOCOL)
        except Exception as e: # Should catch more specific error here
            print("Error")    
