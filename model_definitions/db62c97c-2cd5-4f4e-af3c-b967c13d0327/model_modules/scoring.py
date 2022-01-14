from teradataml import (
    valib,
    configure,
    DataFrame,
    remove_context,
    OneHotEncoder,
    Retain
)
from aoa.util import aoa_create_context


configure.val_install_location = "VAL"


def score(data_conf, model_conf, **kwargs):

    aoa_create_context()

    table_name = data_conf["data_table"]
    numeric_columns = data_conf["numeric_columns"]
    target_column = data_conf["target_column"]
    categorical_columns = data_conf["categorical_columns"]
    
    # feature encoding
    # categorical features to one_hot_encode using VAL transform
    cat_feature_values = {}
    for feature in categorical_columns:
        #distinct has a spurious behaviour so using Group by
        q = 'SELECT ' + feature + ' FROM ' + table_name + ' GROUP BY 1;'  
        df = DataFrame.from_query(q)
        cat_feature_values[feature] = list(df.dropna().get_values().flatten())

    one_hot_encode = []
    for feature in categorical_columns:
        ohe = OneHotEncoder(values=cat_feature_values[feature], columns=feature)
        one_hot_encode.append(ohe)

    # carried forward columns using VAL's Retain function
    retained_cols = numeric_columns+[target_column]
    retain = Retain(columns=retained_cols)    

    data = DataFrame(data_conf["data_table"])
    tf = valib.Transform(data=data, one_hot_encode=one_hot_encode, retain=retain)
    df_eval = tf.result    
        
    score = valib.LinRegPredict(data=df_eval,
                        model=DataFrame(kwargs.get("model_table")),
                        accumulate=target_column
                        )
    df = score.result
   
    df.to_sql(table_name=data_conf["result_table"], if_exists = 'replace')
    
    remove_context()
