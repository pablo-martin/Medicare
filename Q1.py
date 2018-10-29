import os
import re
import numpy as np
import pandas as pd
#first collect all 'details' CSV into a list
QUARTERS = {}
for quarter in os.listdir('house-office-expenditures-with-readme/'):
    if quarter.find('detail') >= 0:
        #special case
        if quarter.find('2015Q2') >= 0:
            if quarter.find('updated'):
                import_csv = files_dir + quarter
        else:
            import_csv = files_dir + quarter
        print('importing %s...' %import_csv)
        df = pd.read_csv(import_csv, thousands = ',')
        #process time fields into date objects
        for time_fields in ['START_DATE', 'END_DATE']:
            df[time_fields] = df[time_fields].str.strip()
            df[time_fields] = pd.to_datetime(df.loc[df[time_fields] != '',
                                                time_fields],
                                                infer_datetime_format=True)
        QUARTERS[quarter] = df
DATA = pd.concat(QUARTERS, axis = 0)
'''--------------------------------------------------------------------------'''
#rename columns so they can be called as fields
for char in ['.',')','(']:
    DATA.rename(columns=lambda x: x.replace(char,''), inplace=True)
DATA.rename(columns=lambda x: x.replace(' ','_'), inplace=True)
DATA.rename(columns=lambda x: x.upper(), inplace=True)
#drop entries where start date is after end date
DATA.drop(DATA.loc[DATA.loc[:,'START_DATE'] > DATA.loc[:,'END_DATE'],:].index,
                                                                inplace = True)
#replace all missing values with empty strings
DATA.BIOGUIDE_ID = DATA.BIOGUIDE_ID.fillna('')
DATA.CATEGORY = DATA.CATEGORY.fillna('')
DATA.OFFICE = DATA.OFFICE.fillna('')
DATA.PAYEE = DATA.PAYEE.fillna('')
DATA.PROGRAM = DATA.PROGRAM.fillna('')
DATA.PURPOSE = DATA.PURPOSE.fillna('')
DATA.QUARTER = DATA.QUARTER.fillna('')
DATA.SORT_SEQUENCE = DATA.SORT_SEQUENCE.fillna('')
DATA.TRANSCODE = DATA.TRANSCODE.fillna('')
DATA.TRANSCODELONG = DATA.TRANSCODE.fillna('')
DATA.RECORDID = DATA.RECORDID.fillna('')
DATA.RECIP_ORIG = DATA.RECIP_ORIG.fillna('')
DATA.YEAR = DATA.YEAR.fillna('')
#standarize the years and remove weird values
DATA['YEAR'] = DATA['YEAR'].astype(str)
DATA['YEAR'] = DATA['YEAR'].map(lambda x: x.replace('FISCAL YEAR ',''))
DATA['YEAR'] = DATA['YEAR'].map(lambda x: x.replace('#VALUE!',''))
DATA['PAYEE'] = DATA['PAYEE'].astype(str)
DATA['PAYEE'] = DATA['PAYEE'].map(lambda x: re.sub(r'[^\x00-\x7f]',r'', x))
DATA['PAYEE'] = DATA['PAYEE'].map(lambda x: x.replace('.',''))
DATA['PAYEE'] = DATA['PAYEE'].map(lambda x: x.replace(',',''))
DATA['PAYEE'] = DATA['PAYEE'].map(lambda x: x.upper())
DATA['PAYEE'] = DATA['PAYEE'].map(lambda x: ' '.join(x.split()))
DATA['OFFICE'] = DATA['OFFICE'].map(lambda x: x.replace('--',''))
DATA['OFFICE'] = DATA['OFFICE'].map(lambda x: x.replace('.',''))
for year in range(2000,2020):
    DATA['OFFICE'] = DATA['OFFICE'].map(lambda x: x.replace(str(year),''))
DATA['OFFICE'] = DATA['OFFICE'].map(lambda x: ' '.join(x.split()))
'''--------------------------------------------------------------------------'''
#do not include 'SUBTOTAL' AND 'GRAND TOTAL FOR ORGANIZATION'
total_payments = DATA.loc[DATA['SORT_SEQUENCE']=='DETAIL','AMOUNT'].sum() \
               + DATA.loc[DATA['SORT_SEQUENCE']=='','AMOUNT'].sum()
print('total of all payments: $%1.10f' %total_payments)
COVERAGE_PERIOD  = DATA.loc[DATA['AMOUNT'] > 0, 'END_DATE'] \
                 - DATA.loc[DATA['AMOUNT'] > 0, 'START_DATE']
print('st. dev. of coverage period is %1.10f' \
                            %np.nanstd([w.days for w in COVERAGE_PERIOD]))
start_time = pd.Timestamp(year = 2010, month = 1, day = 1, hour = 0)
end_time = pd.Timestamp(year = 2016, month = 12, day = 31, hour = 23)
#filter - start date between Jan1, 2010 and Dec31, 2016
date_filter = DATA.loc[:, 'START_DATE'].map(
                                    lambda x: x >= start_time and x <= end_time)
#filter strictly positive entries
positive_filter = (DATA['AMOUNT'] > 0)
#filter - do not include 'SUBTOTAL' AND 'GRAND TOTAL FOR ORGANIZATION'
details_filter = (DATA['SORT_SEQUENCE'] == 'DETAIL')
other_filter = (DATA['SORT_SEQUENCE'] == '')
summary_filter = pd.concat([details_filter, other_filter], axis=1).any(axis=1)
#all filters together
filtered_list = pd.concat([date_filter, positive_filter, summary_filter],
                                                            axis=1).all(axis=1)
#calculate how many years expenditure happened
EXPENDITURE_COVERAGE = DATA.loc[filtered_list, 'END_DATE'] \
                     - DATA.loc[filtered_list, 'START_DATE']
#we're gonna round up, since there were a lot of entries that were 0 days long
EXPENDITURE_COVERAGE = \
           EXPENDITURE_COVERAGE.map(lambda x: np.ceil(np.float(1 + x.days)/365))
AVERAGE_EXPENDITURE = np.nanmean(DATA.loc[filtered_list, 'AMOUNT']\
                                                        / EXPENDITURE_COVERAGE)
print('average annual expenditure was %1.10f' %AVERAGE_EXPENDITURE)
'''--------------------------------------------------------------------------'''
OFFICE_EXPENDITURES = {}
#again create a filter for the date
start_time = pd.Timestamp(year = 2016, month = 1, day = 1, hour = 0)
end_time = pd.Timestamp(year = 2016, month = 12, day = 31, hour = 23)
date_filter = DATA.loc[:, 'START_DATE'].map(
                                    lambda x: x >= start_time and x <= end_time)
#let's reuse our summary filter from above so we don't count expenditures twice
filtered_list = pd.concat([date_filter, summary_filter], axis=1).all(axis=1)
for office_label, office_data in DATA[filtered_list].groupby('OFFICE'):
   OFFICE_EXPENDITURES[office_label] = office_data['AMOUNT'].sum()
#sort results to find highest office
OFFICE_EXPENDITURES = sorted(OFFICE_EXPENDITURES.iteritems(), key= lambda (k,v): (v,k), reverse=True)
print('OFFICE "%s" spent the most ($%1.2f)' %OFFICE_EXPENDITURES[0])
#create new filter to include only the office with highest expenditure
max_office_filter = (DATA['OFFICE'] == 'GOVERNMENT CONTRIBUTIONS')
office_filtered_list = pd.concat([filtered_list, max_office_filter],axis=1).all(axis=1)
PURPOSE_EXPENDITURES = {}
for purp_label, purp_data in DATA[office_filtered_list].groupby('PURPOSE'):
    PURPOSE_EXPENDITURES[purp_label] = purp_data['AMOUNT'].sum()
PURPOSE_EXPENDITURES = sorted(PURPOSE_EXPENDITURES.iteritems(), key= lambda (k,v): (v,k), reverse=True)
print('Highest expenditures in this office are for "%s" ($%1.2f)' %PURPOSE_EXPENDITURES[0])
total_year = DATA.loc[filtered_list, 'AMOUNT'].sum()
print('This amounts to %1.10f of total expenditure' %(PURPOSE_EXPENDITURES[0][1] / total_year))
'''--------------------------------------------------------------------------'''
rep_filter = (DATA['BIOGUIDE_ID'] != '')
rep_combined_filter = pd.concat([rep_filter, summary_filter], axis=1).all(axis=1)
STAFF_SALARIES = {}
for rep_label, rep_data in DATA[rep_combined_filter].groupby('BIOGUIDE_ID'):
    salary_filter = (rep_data['CATEGORY'] == 'PERSONNEL COMPENSATION')
    staff = rep_data.loc[salary_filter, 'PAYEE']
    #there is so much name duplication, i needed this extra cleanup line
    staff_size = len(set([w.replace(' ','') for w in set(staff)]))
    total_salaries = rep_data.loc[salary_filter,'AMOUNT'].sum()
    if staff_size > 0:
        STAFF_SALARIES[rep_label] = np.float(total_salaries) / staff_size
STAFF_SALARIES = sorted(STAFF_SALARIES.iteritems(), key= lambda (k,v): (v,k), reverse=True)
print('Highest average staff salary is for office "%s" ($%1.10f)' %STAFF_SALARIES[0])
'''--------------------------------------------------------------------------'''
OFFICES_QUALIFY = []
for rep_label, rep_data in DATA[rep_combined_filter].groupby('BIOGUIDE_ID'):
    time_in_office = max(rep_data['END_DATE']) - min(rep_data['START_DATE'])
    #served for at least 4 years
    if time_in_office.days >= (365 * 4):
        staff_requirements = []
        for year_label, year_data in rep_data.groupby('YEAR'):
            salary_filter = (year_data['CATEGORY'] == 'PERSONNEL COMPENSATION')
            staff = year_data.loc[salary_filter, 'PAYEE']
            staff_size = len(set([w.replace(' ','') for w in set(staff)]))
            #staff size of at least 5 every year that they served
            staff_requirements.append(staff_size >= 5)
        if np.array(staff_requirements).all():
            OFFICES_QUALIFY.append(rep_label)
TURNOVER = []
for rep_index, rep_label in enumerate(OFFICES_QUALIFY):
    print('processing %i/%i' %(rep_index + 1, len(OFFICES_QUALIFY)))
    rep_filter = (DATA['BIOGUIDE_ID'] == rep_label)
    salary_filter = (DATA['CATEGORY'] == 'PERSONNEL COMPENSATION')
    years_available = list(set(set(DATA.loc[rep_filter, 'YEAR'])).intersection(
                            {'2010','2011','2012','2013','2014','2015','2016'}))
    years_available = sorted(years_available)
    for cYEAR in range(len(years_available) - 1):
        prev_year_filter = (DATA['YEAR'] == years_available[cYEAR])
        staff_filter = pd.concat([rep_filter, salary_filter, prev_year_filter], axis=1).all(axis=1)
        prev_staff = DATA.loc[staff_filter, 'PAYEE']
        prev_staff = set([w.replace(' ','') for w in set(prev_staff)])
        curr_year_filter = (DATA['YEAR'] == years_available[cYEAR+1])
        staff_filter = pd.concat([rep_filter, salary_filter, curr_year_filter], axis=1).all(axis=1)
        curr_staff = DATA.loc[staff_filter, 'PAYEE']
        curr_staff = set([w.replace(' ','') for w in set(curr_staff)])
        staff_survived = len(prev_staff.intersection(curr_staff))
        turnover = (len(prev_staff) - np.float(staff_survived)) /len(prev_staff)
        assert turnover <= 1 and turnover >= 0
        TURNOVER.append(turnover)
median = sorted(TURNOVER)[int(np.floor(len(TURNOVER)/2))]
print('median annual turnover is %1.10f' %median)
