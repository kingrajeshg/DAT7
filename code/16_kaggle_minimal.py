'''
CLASS: Kaggle Stack Overflow competition (minimal code file)
'''

import pandas as pd

# define a function that takes a CSV file and returns a DataFrame (with new or modified features)
def make_features(filename):
    df = pd.read_csv(filename, index_col=0)
    df.rename(columns={'OwnerUndeletedAnswerCountAtPostTime':'Answers'}, inplace=True)
    return df

# apply function to both training and testing files
train = make_features('train.csv')
test = make_features('test.csv')


'''
Create a model with two features
'''

# define X and y
feature_cols = ['ReputationAtPostCreation', 'Answers']
X = train[feature_cols]
y = train.OpenStatus

# fit a logistic regression model
from sklearn.linear_model import LogisticRegression
logreg = LogisticRegression(C=1e9)
logreg.fit(X, y)

# predict class probabilities for the actual testing data
X_oos = test[feature_cols]
oos_pred_prob = logreg.predict_proba(X_oos)[:, 1]


'''
Create a submission file
'''

# sample submission file indicates we need two columns: PostId and predicted probability
test.index      # PostId
oos_pred_prob   # predicted probability

# create a DataFrame that has 'id' as the index, then export to a CSV file
sub = pd.DataFrame({'id':test.index, 'OpenStatus':oos_pred_prob}).set_index('id')
sub.to_csv('sub1.csv')  # 0.694


'''
Update make_features and create another submission file
'''

# update the function
def make_features(filename):
    df = pd.read_csv(filename, index_col=0)
    df.rename(columns={'OwnerUndeletedAnswerCountAtPostTime':'Answers'}, inplace=True)
    df['TitleLength'] = df.Title.apply(len)
    df['BodyLength'] = df.BodyMarkdown.apply(len)
    df['NumTags'] = df.loc[:, 'Tag1':'Tag5'].notnull().sum(axis=1)
    df['OwnerCreationDate'] = pd.to_datetime(df.OwnerCreationDate)
    df['PostCreationDate'] = pd.to_datetime(df.PostCreationDate)
    df['OwnerAge'] = (df.PostCreationDate - df.OwnerCreationDate).dt.days
    return df

# apply function to both training and testing files
train = make_features('train.csv')
test = make_features('test.csv')

# train the model with OwnerAge
feature_cols = ['ReputationAtPostCreation', 'Answers', 'TitleLength', 'BodyLength', 'NumTags', 'OwnerAge']
X = train[feature_cols]
y = train.OpenStatus
logreg.fit(X, y)

# predict class probabilities for the actual testing data
X_oos = test[feature_cols]
oos_pred_prob = logreg.predict_proba(X_oos)[:, 1]

# create submission file
sub = pd.DataFrame({'id':test.index, 'OpenStatus':oos_pred_prob}).set_index('id')
sub.to_csv('sub3.csv')  # 0.637


'''
Build a document-term matrix from Title using CountVectorizer
'''

# build document-term matrix for the training data
from sklearn.feature_extraction.text import CountVectorizer
vect = CountVectorizer(stop_words='english')
dtm = vect.fit_transform(train.Title)

# build document-term matrix for the actual testing data and make predictions
oos_dtm = vect.transform(test.Title)
from sklearn.naive_bayes import MultinomialNB
nb = MultinomialNB()
nb.fit(dtm, train.OpenStatus)
oos_pred_prob = nb.predict_proba(oos_dtm)[:, 1]
sub = pd.DataFrame({'id':test.index, 'OpenStatus':oos_pred_prob}).set_index('id')
sub.to_csv('sub4.csv')  # 0.543


'''
BONUS: Dummy encoding of Tag1
'''

# convert Tag1 from strings to integers
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
train['Tag1_enc'] = le.fit_transform(train.Tag1)

# create a dummy column for each value of Tag1_enc (returns a sparse matrix)
from sklearn.preprocessing import OneHotEncoder
ohe = OneHotEncoder()
tag1_dummies = ohe.fit_transform(train[['Tag1_enc']])

# adjust Tag1 on testing set since LabelEncoder errors on new values during a transform
test['Tag1'] = test['Tag1'].map(lambda s: '<unknown>' if s not in le.classes_ else s)
import numpy as np
le.classes_ = np.append(le.classes_, '<unknown>')

# apply the same encoding to the actual testing data and make predictions
test['Tag1_enc'] = le.transform(test.Tag1)
oos_tag1_dummies = ohe.transform(test[['Tag1_enc']])
nb.fit(tag1_dummies, train.OpenStatus)
oos_pred_prob = nb.predict_proba(oos_tag1_dummies)[:, 1]
sub = pd.DataFrame({'id':test.index, 'OpenStatus':oos_pred_prob}).set_index('id')
sub.to_csv('sub5.csv')  # 0.649
