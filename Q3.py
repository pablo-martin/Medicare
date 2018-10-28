import pandas as pd
import matplotlib.pyplot as plt

idx = pd.IndexSlice


partB = 'DATA/spending_part_b_2011to2015_tidy.csv'
partD = 'DATA/spending_part_d_2011to2015_tidy.csv'
lobby = 'DATA/lobbying_keyed.csv'
drugs = 'DATA/manufacturers_drugs_cleaned.csv'

B = pd.read_csv(partB)

LOBBY = pd.read_csv(lobby)
DRUGS = pd.read_csv(drugs)


'''
Get list of opiates
'''
drug_classification = pd.read_csv('DATA/usp_drug_classification.csv')
analgesic_filter = (drug_classification['usp_category'] == 'Analgesics')
opiod_filter = drug_classification['usp_class'].map(lambda x: x.find('Opioid') >= 0)
combined_filter = pd.concat([analgesic_filter, opiod_filter], axis=1).all(axis=1)
OPIATE_LIST = drug_classification.loc[combined_filter, :]
OPIATE_LIST.loc[OPIATE_LIST['usp_class'] == 'Opioid Analgesics, Long-acting' , 'Details'] = 'Opioid Analgesics, Long-acting'
OPIATE_LIST.loc[OPIATE_LIST['usp_class'] == 'Opioid Analgesics, Short-acting' , 'Details'] = 'Opioid Analgesics, Short-acting'
opiates = list(set(OPIATE_LIST['usp_drug']))


'''
Linking opiate to companies
'''
fields = ['hcpcs_code','ndc','labeler_name','company_key']
OPIATES_INFO = []
DRUG_COMPANIES = pd.read_csv('DATA/companies_drugs_keyed.csv')
#look in drug_name and short_description for match
for med in opiates:
    drug_filter1 = (DRUG_COMPANIES['drug_name'].map(lambda x: x.lower().find(med.lower())>= 0))
    drug_filter2 = (DRUG_COMPANIES['short_description'].map(lambda x: x.lower().find(med.lower())>= 0))
    filter = pd.concat([drug_filter1, drug_filter2], axis=1).any(axis=1)
    mindx = pd.MultiIndex.from_product([[med],range(sum(filter))])
    OPIATES_tmp = pd.DataFrame(index = mindx, columns=fields)
    for field in fields:
        OPIATES_tmp.loc[med, field] = DRUG_COMPANIES.loc[filter, field].values
    OPIATES_INFO.append(OPIATES_tmp)
OPIATES_INFO = pd.concat(OPIATES_INFO, axis=0)

'''
Linking Opiates to Spending for Part B
use hcpcs code
'''



'''
Link Opiates to Spending for Part D
'''
PRESCRIPTION = pd.read_csv(partD)
PRESCRIPTION_OPIATES = []
for med in opiates:
    drug_filter1 = (PRESCRIPTION['brand_name'].map(lambda x: x.lower().find(med.lower())>= 0))
    drug_filter2 = (PRESCRIPTION['generic_name'].map(lambda x: x.lower().find(med.lower())>= 0))
    filter = pd.concat([drug_filter1, drug_filter2], axis=1).any(axis=1)
    mindx = pd.MultiIndex.from_product([[med],range(sum(filter))])
    PRESCRIPTION_tmp = pd.DataFrame(index = mindx, columns=PRESCRIPTION.columns)
    PRESCRIPTION_tmp.loc[:,:] = PRESCRIPTION.loc[filter,:].values
    PRESCRIPTION_OPIATES.append(PRESCRIPTION_tmp)
PRESCRIPTION_OPIATES = pd.concat(PRESCRIPTION_OPIATES, axis=0)
PRESCRIPTION_OPIATES.sort_index(axis=0, inplace = True)

'''
Let's calculate total spending per type of opiate over the last 6 years. simple.
that will be the first plot
'''
spending = {med: {} for med in opiates}
for med in opiates:
    for year_label, year_data in PRESCRIPTION_OPIATES.loc[idx[med,:]].groupby('year'):
        spending[med][year_label] = year_data['total_spending'].sum()

fig, ax = plt.subplots(figsize=(20,12))
for med, vals in spending.items():
    plt.plot(vals.values(), label=med)

plt.title('Prescription Opioid Expenditure for Medicare', fontSize=24)
plt.xticks(range(5),['2011','2012','2013','2014','2015'], fontSize=14)
plt.yticks(np.linspace(0,2,9) * 1e9, [str(w) for w in np.linspace(0,2,9)], fontSize=14)
plt.yticks()
plt.xlabel('Year', fontSize=16)
plt.ylabel('$US Dollars (Billions)', fontSize=16)
plt.legend()
plt.show()
