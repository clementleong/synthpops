"""
Modeling Seattle Metro Long Term Care Facilities

"""
import sciris as sc
import synthpops as sp
import numpy as np
import pandas as pd
import os
import math
from copy import deepcopy
import matplotlib as mplt
import matplotlib.pyplot as plt
from collections import Counter


do_save = True
do_plot = False
verbose = False
write = True
return_popdict = True
use_default = False

datadir = sp.datadir
country_location = 'usa'
state_location = 'Washington'
location = 'seattle_metro'
sheet_name = 'United States of America'

school_enrollment_counts_available = True

part = 2


# Customized age resampling method
def resample_age_uk(exp_age_distr, a):
    """
    Resampling ages for UK data

    Args:
        single_year_age_distr (dict) : age distribution
        age (int)                    : age as an integer
    Returns:
        Resampled age as an integer.
    """
    a = sp.resample_age(exp_age_distr, a)
    if a == 7:
        if np.random.binomial(1, p=0.25):
            a = sp.resample_age(exp_age_distr, a)
    if a == 6:
        if np.random.binomial(1, p=0.25):
            a = sp.resample_age(exp_age_distr, a)
    if a == 5:
        if np.random.binomial(1, p=0.2):
            a = sp.resample_age(exp_age_distr, a)
    if a == 0:
        if np.random.binomial(1, p=0.0):
            a = sp.resample_age(exp_age_distr, a)
    if a == 1:
        if np.random.binomial(1, p=0.0):
            a = sp.resample_age(exp_age_distr, a)
    if a == 2:
        if np.random.binomial(1, p=0.0):
            a = sp.resample_age(exp_age_distr, a)
    if a == 4:
        if np.random.binomial(1, p=0.0):
            a = sp.resample_age(exp_age_distr, a)
    return a


# Customized household construction methods
def generate_larger_households(size, hh_sizes, hha_by_size_counts, hha_brackets, age_brackets, age_by_brackets_dic, contact_matrix_dic, single_year_age_distr):
    """
    Generate ages of those living in households of greater than one individual. Reference individual is sampled conditional on the household size.
    All other household members have their ages sampled conditional on the reference person's age and the age mixing contact matrix
    in households for the population under study.

    Args:
        size (int)                   : The household size.
        hh_sizes (array)             : The count of household size s at index s-1.
        hha_by_size_counts (matrix)  : A matrix in which each row contains the age distribution of the reference person for household size s at index s-1.
        hha_brackets (dict)          : The age brackets for the heads of household.
        age_brackets (dict)          : A dictionary mapping age bracket keys to age bracket range.
        age_by_brackets_dic (dict)   : A dictionary mapping age to the age bracket range it falls within.
        contact_matrix_dic (dict)    : A dictionary of the age-specific contact matrix for different physical contact settings.
        single_year_age_distr (dict) : The age distribution.

    Returns:
        An array of households for size ``size`` where each household is a row and the values in the row are the ages of the household members.
        The first age in the row is the age of the reference individual.
    """
    ya_coin = 0.15  # This is a placeholder value. Users will need to change to fit whatever population you are working with

    homes = np.zeros((hh_sizes[size-1], size))

    for h in range(hh_sizes[size-1]):

        hha = sp.generate_household_head_age_by_size(hha_by_size_counts, hha_brackets, size, single_year_age_distr)

        homes[h][0] = hha

        b = age_by_brackets_dic[hha]
        b_prob = contact_matrix_dic['H'][b, :]

        for n in range(1, size):
            bi = sp.sample_single(b_prob)
            ai = sp.sample_from_range(single_year_age_distr, age_brackets[bi][0], age_brackets[bi][-1])

            """ The following is an example of how you may resample from an age range that is over produced and instead
                sample ages from an age range that is under produced in your population. This kind of customization may
                be necessary when your age mixing matrix and the population you are interested in modeling differ in
                important but subtle ways. For example, generally household age mixing matrices reflect mixing patterns
                for households composed of families. This means household age mixing matrices do not generally cover
                college or university aged individuals living together. Without this customization, this algorithm tends
                to under produce young adults. This method also has a tendency to underproduce the elderly, and does not
                explicitly model the elderly living in nursing homes. Customizations like this should be considered in
                context of the specific population and culture you are trying to model. In some cultures, it is common to
                live in non-family households, while in others family households are the most common and include
                multi-generational family households. If you are unsure of how to proceed with customizations please
                take a look at the references listed in the overview documentation for more information.
            """
            if ai > 5 and ai <= 20:  # This a placeholder range. Users will need to change to fit whatever population you are working with
                if np.random.binomial(1, ya_coin):
                    ai = sp.sample_from_range(single_year_age_distr, 25, 32)  # This is a placeholder range. Users will need to change to fit whatever populaton you are working with

            ai = resample_age_uk(single_year_age_distr, ai)

            homes[h][n] = ai

    return homes


def generate_all_households(N, hh_sizes, hha_by_size_counts, hha_brackets, age_brackets, age_by_brackets_dic, contact_matrix_dic, single_year_age_distr):
    """
    Generate the ages of those living in households together. First create households of people living alone, then larger households.
    For households larger than 1, a reference individual's age is sampled conditional on the household size, while all other household
    members have their ages sampled conditional on the reference person's age and the age mixing contact matrix in households
    for the population under study.

    Args:
        N (int)                      : The number of people in the population.
        hh_sizes (array)             : The count of household size s at index s-1.
        hha_by_size_counts (matrix)  : A matrix in which each row contains the age distribution of the reference person for household size s at index s-1.
        hha_brackets (dict)          : The age brackets for the heads of household.
        age_brackets (dict)          : The dictionary mapping age bracket keys to age bracket range.
        age_by_brackets_dic (dict)   : The dictionary mapping age to the age bracket range it falls within.
        contact_matrix_dic (dict)    : The dictionary of the age-specific contact matrix for different physical contact settings.
        single_year_age_distr (dict) : The age distribution.

    Returns:
        An array of all households where each household is a row and the values in the row are the ages of the household members.
        The first age in the row is the age of the reference individual. Households are randomly shuffled by size.
    """

    homes_dic = {}
    homes_dic[1] = sp.generate_living_alone(hh_sizes, hha_by_size_counts, hha_brackets, single_year_age_distr)
    # remove living alone from the distribution to choose from!
    for h in homes_dic[1]:
        single_year_age_distr[h[0]] -= 1.0/N

    # generate larger households and the ages of people living in them
    for s in range(2, 8):
        homes_dic[s] = generate_larger_households(s, hh_sizes, hha_by_size_counts, hha_brackets, age_brackets, age_by_brackets_dic, contact_matrix_dic, single_year_age_distr)

    homes = []
    for s in homes_dic:
        homes += list(homes_dic[s])

    np.random.shuffle(homes)
    return homes_dic, homes


def write_age_by_uid_dic(datadir, location, state_location, country_location, age_by_uid_dic):
    """
    Write the dictionary of ID mapping to age for each individual in the population.

    Args:
        datadir (string)          : The file path to the data directory.
        location (string)         : The name of the location.
        state_location (string)   : The name of the state the location is in.
        country_location (string) : The name of the country the location is in.
        age_by_uid_dic (dict)     : A dictionary mapping ID to age for each individual in the population.

    Returns:
        None
    """

    file_path = os.path.join(datadir, 'demographics', 'contact_matrices_152_countries', country_location, state_location, 'contact_networks_facilities')
    os.makedirs(file_path, exist_ok=True)

    age_by_uid_path = os.path.join(file_path, location + '_' + str(len(age_by_uid_dic)) + '_age_by_uid.dat')

    f_age_uid = open(age_by_uid_path, 'w')

    uids = sorted(age_by_uid_dic.keys())
    for uid in uids:
        f_age_uid.write(uid + ' ' + str(age_by_uid_dic[uid]) + '\n')
    f_age_uid.close()


def write_groups_by_age_and_uid(datadir, location, state_location, country_location, age_by_uid_dic, group_type, groups_by_uids, secondary_groups_by_uids=None):
    """
    Write groups to file with both ID and their ages.

    Args:
        datadir (string)          : The file path to the data directory.
        location (string)         : The name of the location.
        state_location (string)   : The name of the state the location is in.
        country_location (string) : The name of the country the location is in.
        groups_by_uids (list)      : The list of lists, where each sublist represents a household and the IDs of the household members.
        age_by_uid_dic (dict)     : A dictionary mapping ID to age for each individual in the population.

    Returns:
        None
    """

    file_path = os.path.join(datadir, 'demographics', 'contact_matrices_152_countries', country_location, state_location, 'contact_networks')
    os.makedirs(file_path, exist_ok=True)

    groups_by_age_path = os.path.join(file_path, location + '_' + str(len(age_by_uid_dic)) + '_synthetic_' + group_type + '_with_ages.dat')
    groups_by_uid_path = os.path.join(file_path, location + '_' + str(len(age_by_uid_dic)) + '_synthetic_' + group_type + '_with_uids.dat')

    fg_age = open(groups_by_age_path, 'w')
    fg_uid = open(groups_by_uid_path, 'w')

    for n, ids in enumerate(groups_by_uids):

        group = groups_by_uids[n]

        for uid in group:

            fg_age.write(str(age_by_uid_dic[uid]) + ' ')
            fg_uid.write(str(uid) + ' ')
        fg_age.write('\n')
        fg_uid.write('\n')
    fg_age.close()
    fg_uid.close()


def make_contacts_with_facilities_from_microstructure_objects(age_by_uid_dic, homes_by_uids, schools_by_uids, workplaces_by_uids, facilities_by_uids, facilities_staff_uids, workplaces_by_industry_codes=None):

    popdict = {}
    for uid in age_by_uid_dic:
        popdict[uid] = {}
        popdict[uid]['age'] = age_by_uid_dic[uid]
        popdict[uid]['sex'] = np.random.randint(2)
        popdict[uid]['loc'] = None
        popdict[uid]['contacts'] = {}
        popdict[uid]['snf_res'] = None
        popdict[uid]['snf_staff'] = None
        for k in ['H', 'S', 'W', 'C', 'LTCF']:
            popdict[uid]['contacts'][k] = set()

    homes_by_uids = homes_by_uids[len(facilities_by_uids):]  # only regular homes

    for nf, facility in enumerate(facilities_by_uids):
        facility_staff = facilities_staff_uids[nf]
        for uid in facility:
            popdict[uid]['contacts']['LTCF'] = set(facility)
            popdict[uid]['contacts']['LTCF'] = popdict[uid]['contacts']['LTCF'].union(set(facility_staff))
            popdict[uid]['contacts']['LTCF'].remove(uid)
            popdict[uid]['snf_res'] = 1

        for uid in facility_staff:
            popdict[uid]['contacts']['W'] = set(facility)
            popdict[uid]['contacts']['W'] = popdict[uid]['contacts']['W'].union(set(facility_staff))
            popdict[uid]['contacts']['W'].remove(uid)
            popdict[uid]['snf_staff'] = 1

    for nh, household in enumerate(homes_by_uids):
        for uid in household:
            popdict[uid]['contacts']['H'] = set(household)
            popdict[uid]['contacts']['H'].remove(uid)

    for ns, school in enumerate(schools_by_uids):
        for uid in school:
            popdict[uid]['contacts']['S'] = set(school)
            popdict[uid]['contacts']['S'].remove(uid)

    for nw, workplace in enumerate(workplaces_by_uids):
        for uid in workplace:
            popdict[uid]['contacts']['W'] = set(workplace)
            popdict[uid]['contacts']['W'].remove(uid)

    return popdict

def generate_microstructure_with_faciities(datadir, location, state_location, country_location, gen_pop_size, sheet_name, school_enrollment_counts_available, do_save, do_plot, verbose, write, return_popdict, use_default):

    # Grab Long Term Care Facilities data
    ltcf_df = sp.get_usa_long_term_care_facility_data(datadir, state_location, part)

    # ltcf_df keys
    ltcf_age_bracket_keys = ['Under 65', '65–74', '75–84', '85 and over']
    facility_keys = ['Hospice', 'Nursing home', 'Residential care community']

    # state numbers
    facillity_users = {}
    for fk in facility_keys:
        facillity_users[fk] = {}
        facillity_users[fk]['Total'] = int(ltcf_df[ltcf_df.iloc[:, 0] == 'Number of users2, 5'][fk].values[0].replace(',', ''))
        for ab in ltcf_age_bracket_keys:
            facillity_users[fk][ab] = float(ltcf_df[ltcf_df.iloc[:, 0] == ab][fk].values[0].replace(',', ''))/100.

    total_facility_users = np.sum([facillity_users[fk]['Total'] for fk in facillity_users])

    # Census Bureau numbers 2016
    state_pop_2016 = 7288000
    state_age_distr_2016 = {}
    state_age_distr_2016['60-64'] = 6.3
    state_age_distr_2016['65-74'] = 9.0
    state_age_distr_2016['75-84'] = 4.0
    state_age_distr_2016['85-100'] = 1.8

    # Census Bureau numbers 2018
    state_pop_2018 = 7535591
    state_age_distr_2018 = {}
    state_age_distr_2018['60-64'] = 6.3
    state_age_distr_2018['65-74'] = 9.5
    state_age_distr_2018['75-84'] = 4.3
    state_age_distr_2018['85-100'] = 1.8

    for a in state_age_distr_2016:
        state_age_distr_2016[a] = state_age_distr_2016[a]/100.
        state_age_distr_2018[a] = state_age_distr_2018[a]/100.

    num_state_elderly_2016 = 0
    num_state_elderly_2018 = 0
    for a in state_age_distr_2016:
        num_state_elderly_2016 += state_pop_2016 * state_age_distr_2016[a]
        num_state_elderly_2018 += state_pop_2018 * state_age_distr_2018[a]

    expected_users_2018 = total_facility_users * num_state_elderly_2018/num_state_elderly_2016

    if verbose:
        print('number of elderly',num_state_elderly_2016, num_state_elderly_2018)
        print('growth in elderly', num_state_elderly_2018/num_state_elderly_2016)
        print('users in 2016',total_facility_users, '% of elderly', total_facility_users/num_state_elderly_2016)
        print('users in 2018', expected_users_2018)

    # location age distribution
    age_distr_16 = sp.read_age_bracket_distr(datadir, country_location=country_location, state_location=state_location, location=location)
    age_brackets_16 = sp.get_census_age_brackets(datadir, state_location, country_location)
    age_by_brackets_dic_16 = sp.get_age_by_brackets_dic(age_brackets_16)

    # current King County population size
    pop = 2.25e6

    # local elderly population estimate
    local_elderly_2018 = 0
    for ab in range(12, 16):
        local_elderly_2018 += age_distr_16[ab] * pop

    if verbose:
        print('number of local elderly', local_elderly_2018)

    growth_since_2016 = num_state_elderly_2018/num_state_elderly_2016
    local_perc_elderly_2018 = local_elderly_2018/num_state_elderly_2018

    if verbose:
        print('local users in 2018?', total_facility_users * local_elderly_2018/num_state_elderly_2018 * num_state_elderly_2018/num_state_elderly_2016)
    seattle_users_est_from_state = total_facility_users * local_perc_elderly_2018 * growth_since_2016

    est_seattle_users_2018 = dict.fromkeys(['60-64', '65-74', '75-84', '85-100'], 0)

    for fk in facillity_users:
        for ab in facillity_users[fk]:
            if ab != 'Total':
                print(fk, ab, facillity_users[fk][ab], facillity_users[fk][ab] * facillity_users[fk]['Total'], facillity_users[fk][ab] * facillity_users[fk]['Total'] * pop/state_pop_2018)
                if ab == 'Under 65':
                    b = '60-64'
                elif ab == '65–74':
                    b = '65-74'
                elif ab == '75–84':
                    b = '75-84'
                elif ab == '85 and over':
                    b = '85-100'
                est_seattle_users_2018[b] += facillity_users[fk][ab] * facillity_users[fk]['Total'] * pop/state_pop_2018

    for ab in est_seattle_users_2018:
        print(ab, est_seattle_users_2018[ab], est_seattle_users_2018[ab]/(state_age_distr_2018[ab] * pop))
    print(np.sum([est_seattle_users_2018[b] for b in est_seattle_users_2018]))

    # for pop of 2.25 million of Seattle
    est_ltcf_user_by_age_brackets_perc = {}
    for b in est_seattle_users_2018:
        est_ltcf_user_by_age_brackets_perc[b] = est_seattle_users_2018[b]/state_age_distr_2018[b]/pop

    est_ltcf_user_by_age_brackets_perc['65-69'] = est_ltcf_user_by_age_brackets_perc['65-74']
    est_ltcf_user_by_age_brackets_perc['70-74'] = est_ltcf_user_by_age_brackets_perc['65-74']
    est_ltcf_user_by_age_brackets_perc['75-79'] = est_ltcf_user_by_age_brackets_perc['75-84']
    est_ltcf_user_by_age_brackets_perc['80-84'] = est_ltcf_user_by_age_brackets_perc['75-84']

    est_ltcf_user_by_age_brackets_perc.pop('65-74', None)
    est_ltcf_user_by_age_brackets_perc.pop('75-84', None)

    # # If not using hospice, need to include 55-59 year olds
    # est_ltcf_user_by_age_brackets_perc['55-59'] = 0.0098
    # est_ltcf_user_by_age_brackets_perc['60-64'] = 0.0098
    # est_ltcf_user_by_age_brackets_perc['65-69'] = 0.0098
    # est_ltcf_user_by_age_brackets_perc['70-74'] = 0.0098
    # est_ltcf_user_by_age_brackets_perc['75-79'] = 0.0546
    # est_ltcf_user_by_age_brackets_perc['80-84'] = 0.0546
    # est_ltcf_user_by_age_brackets_perc['85-100'] = 0.1779

    age_distr_18_fp = os.path.join(datadir, 'demographics', 'contact_matrices_152_countries', country_location, state_location, 'age distributions', 'seattle_metro_age_bracket_distr_18.dat')
    age_distr_18 = sp.read_age_bracket_distr(datadir, file_path=age_distr_18_fp)
    age_brackets_18_fp = os.path.join(datadir, 'demographics', 'contact_matrices_152_countries', country_location, state_location, 'age distributions', 'census_age_brackets_18.dat')
    age_brackets_18 = sp.get_census_age_brackets(datadir, file_path=age_brackets_18_fp)
    age_by_brackets_dic_18 = sp.get_age_by_brackets_dic(age_brackets_18)

    # gen_pop_size = 2.25e5
    # gen_pop_size = 20e3
    gen_pop_size = int(gen_pop_size)

    expected_users_by_age = {}

    for a in range(60, 101):
        if a < 65:
            b = age_by_brackets_dic_18[a]

            expected_users_by_age[a] = gen_pop_size * age_distr_18[b]/len(age_brackets_18[b])
            expected_users_by_age[a] = expected_users_by_age[a] * est_ltcf_user_by_age_brackets_perc['60-64']
            expected_users_by_age[a] = int(math.ceil(expected_users_by_age[a]))

        elif a < 75:
            b = age_by_brackets_dic_18[a]

            expected_users_by_age[a] = gen_pop_size * age_distr_18[b]/len(age_brackets_18[b])
            expected_users_by_age[a] = expected_users_by_age[a] * est_ltcf_user_by_age_brackets_perc['70-74']
            expected_users_by_age[a] = int(math.ceil(expected_users_by_age[a]))

        elif a < 85:
            b = age_by_brackets_dic_18[a]

            expected_users_by_age[a] = gen_pop_size * age_distr_18[b]/len(age_brackets_18[b])
            expected_users_by_age[a] = expected_users_by_age[a] * est_ltcf_user_by_age_brackets_perc['80-84']
            expected_users_by_age[a] = int(math.ceil(expected_users_by_age[a]))

        elif a < 101:
            b = age_by_brackets_dic_18[a]

            expected_users_by_age[a] = gen_pop_size * age_distr_18[b]/len(age_brackets_18[b])
            expected_users_by_age[a] = expected_users_by_age[a] * est_ltcf_user_by_age_brackets_perc['85-100']
            expected_users_by_age[a] = int(math.ceil(expected_users_by_age[a]))

    print(np.sum([expected_users_by_age[a] for a in expected_users_by_age]))

    # KC facilities reporting cases - should account for 70% of all facilities
    KC_snf_df = pd.read_csv(os.path.join('/home', 'dmistry', 'Dropbox (IDM)', 'dmistry_COVID-19', 'secure_King_County', 'IDM_CASE_FACILITY.csv'))
    d = KC_snf_df.groupby(['FACILITY_ID']).mean()

    # print(sorted(d['RESIDENT_TOTAL_COUNT'].values), d['RESIDENT_TOTAL_COUNT'].values.mean(), np.median(d['RESIDENT_TOTAL_COUNT'].values))
    KC_ltcf_sizes = list(d['RESIDENT_TOTAL_COUNT'].values)
    KC_staff_sizes = list(d['STAFF_TOTAL_COUNT'].values)

    # don't make staff numbers smaller here. instead cluster workers into smaller groups
    KC_resident_staff_ratios = [KC_ltcf_sizes[i]/(KC_staff_sizes[i]) for i in range(len(KC_ltcf_sizes))]
    KC_resident_staff_ratios = [KC_resident_staff_ratios[k] for k in range(len(KC_resident_staff_ratios))]
    # KC_resident_staff_ratios = np.array([int(math.ceil(k)) for k in KC_resident_staff_ratios])
    # KC_resident_staff_ratios = KC_resident_staff_ratios[KC_resident_staff_ratios < 75] # remove outliers
    print(KC_resident_staff_ratios)
    print(np.mean(KC_resident_staff_ratios))

    # Imagine Aegis Care are not included because they didn't have outbreaks
    # Aegis facility resident sizes
    # KC_ltcf_sizes += [
    #                   35., 43., 45., 46.,
    #                   46., 47., 47., 50.,
    #                   50., 53., 55., 59.,
    #                   59., 63., 66., 68.,
    #                   69., 71., 72., 73.,
    #                   73., 75., 76., 76.,
    #                   78., 78., 79., 81.,
    #                   87., 90., 111., 119.,
    #                   ]
    all_residents = []
    for a in expected_users_by_age:
        all_residents += [a] * expected_users_by_age[a]
    np.random.shuffle(all_residents)

    # place residents in facilities
    facilities = []
    print(len(all_residents), len(all_residents)/np.mean(KC_ltcf_sizes))
    while len(all_residents) > 0:
        size = int(np.random.choice(KC_ltcf_sizes))
        new_facility = all_residents[0:size]
        facilities.append(new_facility)
        all_residents = all_residents[size:]
    print(len(facilities))

    max_age = 100

    expected_age_distr = dict.fromkeys(np.arange(max_age+1), 0)
    expected_age_count = dict.fromkeys(np.arange(max_age+1), 0)

    # adjust age distribution for those already created
    for a in expected_age_distr:
        expected_age_distr[a] = age_distr_16[age_by_brackets_dic_16[a]]/len(age_brackets_16[age_by_brackets_dic_16[a]])
        expected_age_count[a] = int(gen_pop_size * expected_age_distr[a])

    ltcf_adjusted_age_count = deepcopy(expected_age_count)
    for a in expected_users_by_age:
        ltcf_adjusted_age_count[a] -= expected_users_by_age[a]
    ltcf_adjusted_age_distr = sp.norm_dic(ltcf_adjusted_age_count)

    # build rest of the population
    n = gen_pop_size - np.sum([len(f) for f in facilities])  # remove those placed in care homes

    household_size_distr = sp.get_household_size_distr(datadir, location, state_location, country_location, use_default=use_default)
    hha_by_size = sp.get_head_age_by_size_distr(datadir, state_location, country_location, use_default=use_default)
    hh_sizes = sp.generate_household_sizes_from_fixed_pop_size(n, household_size_distr)
    hha_brackets = sp.get_head_age_brackets(datadir, country_location=country_location, use_default=use_default)
    hha_by_size = sp.get_head_age_by_size_distr(datadir, country_location=country_location, use_default=use_default)

    contact_matrix_dic = sp.get_contact_matrix_dic(datadir, sheet_name=sheet_name)

    homes_dic, homes = generate_all_households(n, hh_sizes, hha_by_size, hha_brackets, age_brackets_16, age_by_brackets_dic_16, contact_matrix_dic, deepcopy(expected_age_distr))
    homes = facilities + homes

    homes_by_uids, age_by_uid_dic = sp.assign_uids_by_homes(homes)
    new_ages_count = Counter(age_by_uid_dic.values())

    facilities_by_uids = homes_by_uids[0:len(facilities)]

    if do_plot:

        fig = plt.figure(figsize=(7, 5))
        ax = fig.add_subplot(111)
        x = np.arange(max_age+1)
        y_exp = np.zeros(max_age+1)
        y_sim = np.zeros(max_age+1)
        for a in x:
            y_exp[a] = expected_age_distr[a]
            y_sim[a] = new_ages_count[a]/n
        ax.plot(x, y_exp, color='k', label='Expected')
        ax.plot(x, y_sim, color='teal', label='Simulated')
        leg = ax.legend(fontsize=18)
        leg.draw_frame(False)
        ax.set_xlim(0, max_age+1)
        for a in range(6):
            ax.axvline(x=a, ymin=0, ymax=1)
        plt.show()

    # Make a dictionary listing out uids of people by their age
    uids_by_age_dic = sp.get_ids_by_age_dic(age_by_uid_dic)

    # Generate school sizes
    school_sizes_count_by_brackets = sp.get_school_size_distr_by_brackets(datadir, location=location, state_location=state_location, country_location=country_location, counts_available=school_enrollment_counts_available, use_default=use_default)
    school_size_brackets = sp.get_school_size_brackets(datadir, location=location, state_location=state_location, country_location=country_location, use_default=use_default)

    # Figure out who's going to school as a student with enrollment rates (gets called inside sp.get_uids_in_school)
    uids_in_school, uids_in_school_by_age, ages_in_school_count = sp.get_uids_in_school(datadir, n, location, state_location, country_location, age_by_uid_dic, homes_by_uids, use_default=use_default)  # this will call in school enrollment rates

    # Get school sizes
    gen_school_sizes = sp.generate_school_sizes(school_sizes_count_by_brackets, school_size_brackets, uids_in_school)

    # Assign students to school
    gen_schools, gen_school_uids = sp.send_students_to_school(gen_school_sizes, uids_in_school, uids_in_school_by_age, ages_in_school_count, age_brackets_16, age_by_brackets_dic_16, contact_matrix_dic, verbose)

    # Get employment rates
    employment_rates = sp.get_employment_rates(datadir, location=location, state_location=state_location, country_location=country_location, use_default=use_default)

    # Find people who can be workers (removing everyone who is currently a student)
    potential_worker_uids, potential_worker_uids_by_age, potential_worker_ages_left_count = sp.get_uids_potential_workers(gen_school_uids, employment_rates, age_by_uid_dic)
    workers_by_age_to_assign_count = sp.get_workers_by_age_to_assign(employment_rates, potential_worker_ages_left_count, uids_by_age_dic)

    # Assign teachers and update school lists
    gen_schools, gen_school_uids, potential_worker_uids, potential_worker_uids_by_age, workers_by_age_to_assign_count = sp.assign_teachers_to_work(gen_schools, gen_school_uids, employment_rates, workers_by_age_to_assign_count, potential_worker_uids, potential_worker_uids_by_age, potential_worker_ages_left_count, verbose=verbose)

    # Assign facilities care staff from 20 to 59

    facilities_staff = []
    facilities_staff_uids = []
    staff_age_range = np.arange(20, 60)
    for nf, fc in enumerate(facilities):
        n_residents = len(fc)
        resident_staff_ratio = np.random.choice(KC_resident_staff_ratios)

        n_staff = int(math.ceil(n_residents/resident_staff_ratio))

        new_staff, new_staff_uids = [], []

        for i in range(n_staff):
            a_prob = np.array([workers_by_age_to_assign_count[a] for a in staff_age_range])
            a_prob = a_prob/np.sum(a_prob)
            aindex = np.random.choice(a=staff_age_range, p=a_prob)

            uid = potential_worker_uids_by_age[aindex][0]
            potential_worker_uids_by_age[aindex].remove(uid)
            potential_worker_uids.pop(uid, None)
            workers_by_age_to_assign_count[aindex] -= 1

            new_staff.append(aindex)
            new_staff_uids.append(uid)

        facilities_staff.append(new_staff)
        facilities_staff_uids.append(new_staff_uids)

    if verbose:
        print(len(facilities_staff_uids))
        for nf, fc in enumerate(facilities):
            print(fc, facilities_staff[nf], len(fc)/len(facilities_staff[nf]))

    # Generate non-school workplace sizes needed to send everyone to work
    workplace_size_brackets = sp.get_workplace_size_brackets(datadir, state_location=state_location, country_location=country_location, use_default=use_default)
    workplace_size_distr_by_brackets = sp.get_workplace_size_distr_by_brackets(datadir, state_location=state_location, country_location=country_location, use_default=use_default)
    workplace_sizes = sp.generate_workplace_sizes(workplace_size_distr_by_brackets, workplace_size_brackets, workers_by_age_to_assign_count)

    # Assign all workers who are not staff at schools to workplaces
    gen_workplaces, gen_workplace_uids, potential_worker_uids, potential_worker_uids_by_age, workers_by_age_to_assign_count = sp.assign_rest_of_workers(workplace_sizes, potential_worker_uids, potential_worker_uids_by_age, workers_by_age_to_assign_count, age_by_uid_dic, age_brackets_16, age_by_brackets_dic_16, contact_matrix_dic, verbose=verbose)

    # group uids to file
    if write:
        write_groups_by_age_and_uid(datadir, location, state_location, country_location, age_by_uid_dic, 'households', homes_by_uids)
        write_groups_by_age_and_uid(datadir, location, state_location, country_location, age_by_uid_dic, 'schools', gen_school_uids)
        write_groups_by_age_and_uid(datadir, location, state_location, country_location, age_by_uid_dic, 'workplaces', gen_workplace_uids)
        write_groups_by_age_and_uid(datadir, location, state_location, country_location, age_by_uid_dic, 'facilities', facilities_by_uids)
        write_groups_by_age_and_uid(datadir, location, state_location, country_location, age_by_uid_dic, 'facilities_staff', facilities_staff_uids)

    if return_popdict:
        popdict = make_contacts_with_facilities_from_microstructure_objects(age_by_uid_dic, homes_by_uids, gen_school_uids, gen_workplace_uids, facilities_by_uids, facilities_staff_uids)
        # return popdict

    if verbose:
        uids = popdict.keys()
        uids = [uid for uid in uids]
        np.random.shuffle(uids)

        for i in range(50):
            uid = uids[i]
            person = popdict[uid]
            print(uid, person['age'], person['contacts']['H'], person['contacts']['S'], person['contacts']['W'], person['contacts']['LTCF'])
            print(person['snf_res'], person['snf_staff'])


gen_pop_size = 6e3
popdict = generate_microstructure_with_faciities(datadir, location, state_location, country_location, gen_pop_size, sheet_name, school_enrollment_counts_available, do_save, do_plot, verbose, write, return_popdict, use_default)
