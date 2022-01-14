from teradataml import copy_to_sql, DataFrame
from aoa.stats import stats
from aoa.util import aoa_create_context

import joblib
import pandas as pd


def score(data_conf, model_conf, **kwargs):
    model = joblib.load("artifacts/input/model.joblib")

    aoa_create_context()

    features_tdf = DataFrame(data_conf["table"])

    # convert to pandas to use locally
    features_df = features_tdf.to_pandas()

    print("Scoring")
    y_pred = model.predict(features_df[model.feature_names])

    print("Finished Scoring")

    # create result dataframe and store in Teradata
    y_pred = pd.DataFrame(y_pred, columns=[model.target_name])
    y_pred["PatientId"] = features_df["PatientId"].values
    copy_to_sql(df=y_pred, table_name=data_conf["predictions"], index=False, if_exists="replace")

    predictions_tdf = DataFrame(data_conf["predictions"])

    stats.record_scoring_stats(features_tdf, predictions_tdf)


# Add code required for RESTful API
class ModelScorer(object):

    def __init__(self, config=None):
        self.model = joblib.load('artifacts/input/model.joblib')

        from prometheus_client import Counter
        self.pred_class_counter = Counter('model_prediction_classes',
                                          'Model Prediction Classes', ['model', 'version', 'clazz'])

    def predict(self, data):
        pred = self.model.predict([data])

        # record the predicted class so we can check model drift (via class distributions)
        self.pred_class_counter.labels(model=os.environ["MODEL_NAME"],
                                       version=os.environ.get("MODEL_VERSION", "1.0"),
                                       clazz=str(int(pred))).inc()

        return pred
