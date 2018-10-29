import pandas as pd
import matplotlib.pyplot as plt

idx = pd.IndexSlice


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
DRUGS = pd.read_csv('DATA/companies_drugs_keyed.csv')
DRUG_CO = pd.read_csv('DATA/manufacturers_drugs_cleaned.csv')
for DRUG_COMPANIES in [DRUGS, DRUG_CO]:
    #look in drug_name and short_description for match
    for med in opiates:
        drug_filter1 = (DRUG_COMPANIES['drug_name'].map(lambda x: x.lower().find(med.lower())>= 0))
        drug_filter2 = (DRUG_COMPANIES['short_description'].map(lambda x: x.lower().find(med.lower())>= 0))
        filter = pd.concat([drug_filter1, drug_filter2], axis=1).any(axis=1)
        mindx = pd.MultiIndex.from_product([[med],range(sum(filter))])
        OPIATES_tmp = pd.DataFrame(index = mindx, columns=fields)
        for field in fields:
            try:
                OPIATES_tmp.loc[med, field] = DRUG_COMPANIES.loc[filter, field].values
            except KeyError:
                pass
        OPIATES_INFO.append(OPIATES_tmp)
OPIATES_INFO = pd.concat(OPIATES_INFO, axis=0)
OPIATES_INFO.sort_index(axis=0, inplace = True)



'''
Linking Opiates to Spending for Part B
(use hcpcs code)
'''
partB = 'DATA/spending_part_b_2011to2015_tidy.csv'
CLINIC = pd.read_csv(partB)
opiate_filter = CLINIC['hcpcs_code'].map(lambda x: x in set(OPIATES_INFO['hcpcs_code']))
spending_PARTB = {}
for code_label, code_data in CLINIC[opiate_filter].groupby('hcpcs_code'):
    tmp = {}
    for year_label, year_data in code_data.groupby('year'):
        tmp[year_label] = year_data['total_spending'].sum()
    spending_PARTB[code_label] = tmp

hcpcs2drug = {}
for code in spending.keys():
    index_drug = list(set(OPIATES_INFO[OPIATES_INFO['hcpcs_code'] == code].index.labels[0]))[0]
    hcpcs2drug[code] = OPIATES_INFO.index.levels[0][index_drug]


'''
Link Opiates to Spending for Part D
'''
partD = 'DATA/spending_part_d_2011to2015_tidy.csv'
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
Let's calculate total spending per type of opiate over the last 6 years.
'''
def extract_info(field):
    spending = {med: {} for med in opiates}
    for med in opiates:
        for year_label, year_data in PRESCRIPTION_OPIATES.loc[idx[med,:]].groupby('year'):
            spending[med][year_label] = year_data[field].sum()
    return spending

'''
Let's gather lobbying information over the same time period
'''
lobby = 'DATA/lobbying_keyed.csv'
LOBBY = pd.read_csv(lobby)
spendingLOBBY = {}
for client, client_data in LOBBY.groupby('company_key'):
    tmp_client = {}
    for year_label, year_data in client_data.groupby('year'):
        tmp_client[year_label] = year_data['total'].sum()
    spendingLOBBY[client] = tmp_client
#let's only include pharma companies involved in opiates
OPIUM_PHARMA = set(spendingLOBBY.keys()).intersection(set(OPIATES_INFO['company_key']))
OP = {}
for comp_key in OPIUM_PHARMA:
    OP[comp_key] = list(set(OPIATES_INFO.loc[OPIATES_INFO['company_key']==comp_key,'labeler_name']))[0]



'''
--------------------------------------------------------------------------------
Let's plot our results so far
--------------------------------------------------------------------------------
'''
height = 10
length = 6
savefig = 1

fig, ax = plt.subplots(figsize=(height,length))
for med, vals in spending_PARTB.items():
    plt.plot(vals.values(), label=hcpcs2drug[med])
plt.title('Clinic Opioid Expenditure for Medicare', fontSize=24)
plt.xticks(range(5),['2011','2012','2013','2014','2015'], fontSize=14)
plt.yticks(np.array(range(6)) * 1e6, [str(w) for w in range(6)], fontSize=14)
plt.xlabel('Year', fontSize=16)
plt.ylabel('Total Expenditure in Millions of US Dollars', fontSize=16)
plt.legend()
if savefig==1: plt.savefig('pics/total_expenditure_clinic.jpg',dpi=800)
plt.show()


spending = extract_info('total_spending')
fig, ax = plt.subplots(figsize=(height,length))
for med, vals in spending.items():
    plt.plot(vals.values(), label=med)
plt.title('Prescription Opioid Expenditure for Medicare', fontSize=24)
plt.xticks(range(5),['2011','2012','2013','2014','2015'], fontSize=14)
plt.yticks(np.linspace(0,2,9) * 1e9, [str(w) for w in np.linspace(0,2,9)], fontSize=14)
plt.xlabel('Year', fontSize=16)
plt.ylabel('Total Expenditure in Billions of US Dollars', fontSize=16)
plt.legend()
if savefig==1: plt.savefig('pics/total_expenditure_prescription.jpg',dpi=800)
plt.show()



spending = extract_info('beneficiary_count')
fig, ax = plt.subplots(figsize=(height,length))
for med, vals in spending.items():
    plt.plot(vals.values(), label=med)
year_labels=['2011','2012','2013','2014','2015']
plt.title('Prescription Opioid Expenditure for Medicare', fontSize=24)
plt.yticks(np.array(range(6)) * 1e6,['0','1','2','3','4','5'],fontSize=14)
plt.xticks(range(5),year_labels, fontSize=14)
plt.xlabel('Year', fontSize=16)
plt.ylabel('# Of People Using Drug (Millions)', fontSize=16)
plt.legend()
if savefig==1: plt.savefig('pics/people_using.jpg',dpi=800)
plt.show()


fig, ax = plt.subplots(figsize=(height,length))
for comp_key, label in OP.items():
    tmp = spendingLOBBY[comp_key]
    vals = []
    for rel_year in year_labels:
        vals.append(tmp.get(int(rel_year)))
    plt.plot(range(5),vals, '-o', label=label)
plt.xticks(range(5),year_labels, fontSize=14)
plt.yticks(np.linspace(0,2500000,6),['0','0.5','1','1.5','2','2.5'],fontSize=14)
plt.ylabel('US Dollars (Millions)', fontSize=16)
plt.legend()
plt.title('Opioid Producing Big Pharma Contributions', fontSize=24)
if savefig==1: plt.savefig('pics/pharma_contributions.jpg',dpi=800)
plt.show()
