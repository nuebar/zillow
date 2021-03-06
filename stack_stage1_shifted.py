import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler, Imputer
from sklearn.model_selection import LeaveOneGroupOut, cross_val_predict
from zillow import modelling
import pickle as pkl
import dask.dataframe as dd

train_df = pd.concat([
    #dd.read_hdf("input/train2.*.hdf", "data").compute(),
    dd.read_hdf("input/train_20172.*.hdf", "data").compute(),
])
month = train_df["yearmonth"]

train_y = train_df['logerror']
train_df = train_df.drop(["logerror", "transactiondate",
                          "year", "month", "yearmonth",
                          "error_last_month", "error_2ndlast_month", "error_3rdlast_month",
                          "error_last_3months"], axis=1)
feat_names = train_df.columns.values
with open("input/feat_names.pkl", "wb") as f:
    pkl.dump(feat_names, f)

encoders = {}
for c in train_df.columns:
    if train_df[c].dtype == 'object':
        encoders[c] = LabelEncoder()
        train_df[c] = encoders[c].fit_transform(list(train_df[c].values))

#for col in train_df:
#    if train_df[col].mean() > train_df[col].median()*1.1:
#        print(col, train_df[col].mean(), train_df[col].median())
#        train_df.loc[:, col] = np.log(train_df[col]+1)

train_df = train_df.replace(np.inf, np.nan).replace(-np.inf, np.nan)

with open("input/encoders.pkl", "wb") as f:
    pkl.dump(encoders, f)

tolerance = 0.1
y = np.clip(train_y, np.median(train_y)-tolerance, np.median(train_y)+tolerance)

cv = LeaveOneGroupOut()

preds = {}
for n, model in modelling.stage1_models.items():
    name = "clip_" + n
    print(name)
    preds[name] = cross_val_predict(model, train_df, y, cv=cv, groups=month)
    print(name, np.abs((train_y - preds[name])).mean())
    model.fit(train_df, y)
    with open("models/{}.py".format(name), "wb") as f:
        pkl.dump(model, f)

del train_df

train_df = pd.DataFrame(preds)
train_df.to_csv("stack_stage1.csv")
