import pandas as pd

#create a pricing dataframe
pricing = pd.DataFrame([['Piping (per mm)', 0.04],['L Joint', 1], ['T Joint', 1.1]], columns=['Item', 'Price (per unit)'])

print(pricing.head())