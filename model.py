# model.py

# model.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import pickle

# Create Training Data
data = {
    "text": [
        "Road is damaged near school",
        "Big pothole in main road",
        "Road problem in village",
        "Road is broken",
        "Street light not working",
        "Electric pole problem",
        "Electricity problem in village",
        "No power supply",
        "Water not coming for 2 days",
        "Water pipe leakage",
        "No water supply",
        "Garbage near temple",
        "Waste not collected",
        "Garbage problem",
        "Drainage problem in village",
        "Sewage water overflow"
    ],
    "label": [
        "Road Issue",
        "Road Issue",
        "Road Issue",
        "Road Issue",
        "Road Issue",
        "Electricity Issue",
        "Electricity Issue",
        "Electricity Issue",
        "Electricity Issue",
        "Water Issue",
        "Water Issue",
        "Water Issue",
        "Sanitation Issue",
        "Sanitation Issue",
        "Sanitation Issue",
        "Sanitation Issue",
]
}

df = pd.DataFrame(data)

#  Create ML Pipeline
model = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("classifier", MultinomialNB())
])

# Train Model
model.fit(df["text"], df["label"])

#  Save Model
pickle.dump(model, open("complaint_model.pkl", "wb"))

print("Model trained and saved successfully!")