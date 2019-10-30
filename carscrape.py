#!/usr/bin/env python3

"""
Scrape car data from autotrader.co.uk  

Given CSV_FILE contains the list of cars to search for,
Build a list of Advertisement objects and print a sample.
Uses f-strings (assumes Python 3.7) 
"""


#imports
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import csv
import logging
from collections import namedtuple


#define constants
BASE_URL = 'https://www.autotrader.co.uk'
POSTCODE = 'PO16+7GZ'

CSV_FILE = 'atuk_makes_and_models.csv'


CarTup = namedtuple('CarTup', [
    'make',
    'model',
    'total',])


class Advertisement(object):
    """Class represents one used car advertisement

    Attributes
    ----------
    Most are self-explanatory str attributes of a car.
    hyperlink : str 
        the URL where the Advertisement was scraped.

    Methods
    -------
    to_string() 
        Builds a string for output to the console, using all attributes.
    """

    def __init__(self):
        self.hyperlink = ''
        self.description = ''
        self.seller_type = ''
        self.price = ''

        self.make = ''
        self.model = ''
        self.year = ''
        self.mileage = ''

        self.body_style = ''
        self.co2emission = ''
        self.doors = ''
        self.transmission = ''

        self.was_stolen = ''
        self.was_write_off = ''
        self.was_scrapped = ''

        self.engine_size = ''
        self.fuel_type = ''


    def to_string(self):
        """Builds a string for output to the console, using all attributes."""
        
        return (f'Hyperlink: {self.hyperlink}, Description: {self.description}, ' \
                f'Seller Type: {self.seller_type}, Price: {self.price}, ' \
                f'Make: {self.make}, Model: {self.model}, Year: {self.year}, ' \
                f'Mileage: {self.mileage}, Body Style: {self.body_style}, ' \
                f'Co2 Emissions: {self.co2emission}, Doors: {self.doors}, ' \
                f'Transmission: {self.transmission}, Was Stolen: {self.was_stolen}, ' \
                f'Was Write Off: {self.was_write_off}, ' \
                f'Was Scrapped: {self.was_scrapped}, Engine Size: {self.engine_size}, ' \
                f'Fuel Type: {self.fuel_type}')

#set up logging output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def check_exists_by_tag(parent, next_tag):
    """Return True if parent has a child of type next_tag."""

    try:
        parent.find_element_by_tag_name(next_tag)
    except NoSuchElementException:
        return False
    return True



def check_exists_by_class(parent, next_class):
    """Return True if parent has a child of type next_class."""

    try:
        parent.find_element_by_class_name(next_class)
    except NoSuchElementException:
        return False
    return True




def open_browser(next_url):
    """Open next_url and returns a (headless) Firefox browser."""

    logger.info(f'Opening page: {next_url} ...')

    opts = Options()
    opts.headless = True
    browser = Firefox(options=opts)

    try:
        browser.get(next_url)
        return browser
    except Exception as e:
        logger.error(f'Error retrieving {next_url}: {e}')
        return None



def clean_up(browser):
    """Close and quit the webdriver."""

    logger.info(f'Closing the browser ...')
    try:
        browser.close()
        browser.quit()
    except Exception as e:
        logger.error(f'Error closing {browser}: {e}')




def read_from_csv(next_csv):
    """
    Read first three columns of car data in from next_csv.

    Return a list of CarTup namedtuples, cars_in
    """

    cars_in = []

    logger.info(f'Reading car data in from {next_csv} ...')

    try:
        with open(next_csv, newline='') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader) #skip the header line
            cars_in = [CarTup._make(rec[0:3]) for rec in csv_reader]
            return cars_in

    except IOError as e:
        logger.error(f'Could not open {next_csv}: {e}')
        return None




def search_all_car_types(these_cars):
    """
    Multi car-type wrapper for search_one_car_type.

    Return alphabetically ordered list (of sets of car id numbers)
    """

    results_list = []

    for next_car in these_cars:
        next_set = search_one_car_type(next_car)

        #bundle together the make and model with the set of id numbers
        quick_tuple = (next_car.make, next_car.model, next_set)
        results_list.append(quick_tuple)

    return results_list
        



def search_one_car_type(next_car):
    """
    Search BASE_URL for all cars of type next_car.
    
    Expects next_car to be a CarTup (make, model, total)
    Return unordered set cars_found of URL id numbers
    """

    next_make = next_car.make
    next_model = next_car.model
    total_cars = int(next_car.total)
    cars_found = set()

    logger.info(f'Searching for {next_make + " " + next_model} ...')

    search_url = f'{BASE_URL}/car-search?' \
            f'advertising-location=at_cars&' \
            f'price-search-type=total-price&' \
            f'search-target=usedcars&' \
            f'postcode={POSTCODE}&' \
            f'make={next_make}&' \
            f'model={next_model}&'

    browser = open_browser(search_url)

    #retrieve website value for total number of advertisements matching next_car
    total_header = browser.find_element_by_class_name('search-form__count.js-results-count')
    actual_total_string = total_header.text.split(' ')[0]
    actual_total = int(actual_total_string)

    #uncomment next line to use website's total rather than CSV expected total
    #total_cars = actual_total

    #loop through all possible pages of results
    while True:
        if browser is not None:
            found_cars = browser.find_elements_by_class_name('search-page__result')
            for car in found_cars:
                cars_found.add(car.get_attribute('id'))
        else:
            logger.info(f'Got nothing back from {search_url}')
        
        #if we found all the expected cars, stop collecting ids
        if len(cars_found) >= total_cars:
            break

        #otherwise, move to the next page of cars
        logger.info(f'Added {len(cars_found)} so far.  Looking for {total_cars} ...')
        next_arrow = browser.find_element_by_class_name('pagination--right__active')
        browser.execute_script('arguments[0].click();', next_arrow)

        WebDriverWait(browser, 60).until(EC.staleness_of(next_arrow))
    

    clean_up(browser)

    return cars_found






def scrape_all_cars(these_cars):
    """
    Multi-car wrapper for scrape_one_car.
    
    Expects these_cars to be an ordered list of tuples
    Each tuple should be (make, model, set(car id #s))
    Return alphabetically ordered list of Advertisement objects 
    """

    all_ads = []

    #break each type of car (make, model) out of these_cars
    for each_tuple in these_cars:
        next_make = each_tuple[0]
        next_model = each_tuple[1]
        car_set = each_tuple[2]

        #scrape ads for all cars of this type
        for next_car in car_set:
            next_ad = scrape_one_car(next_car)
            next_ad.make = next_make
            next_ad.model = next_model

            all_ads.append(next_ad)

    return all_ads




def scrape_one_car(next_car):
    """
    Scrape one car worth of data for next_car.

    Expects next_car to be a 15-digit string id# identifying a unique ad page.
    Example: '201910012835451'
    Return an Advertisement object.
    Default value for all Advertisement attributes is 'Unknown'.
    (Not all ad pages will contain all desired values)
    """

    next_ad = Advertisement()
    next_url = BASE_URL + '/classified/advert/' + next_car

    browser = open_browser(next_url)

    logger.info(f'Scraping data for car# {next_car} ...')

    description_class_name = 'advert-heading__title.atc-type-insignia.atc-type-insignia--medium'
    next_description = browser.find_element_by_class_name(description_class_name).text

    price_class_name = 'advert-price__cash-price'
    next_price = browser.find_element_by_class_name(price_class_name).text

    #seller paragraphs with anchor elements are dealers, othewise private owners.
    seller_class_name = 'seller-name.atc-type-toledo.atc-type-toledo--medium'
    next_seller_para = browser.find_element_by_class_name(seller_class_name)
    if check_exists_by_tag(next_seller_para, 'a'):
        next_seller = 'Dealer'
    else:
        next_seller = 'Private'

    #basic specs are in an unordered HTML list element
    specs_list_class_name = 'key-specifications'
    car_specs = {
            'year' : 'Unknown',
            'body_style' : 'Unknown',
            'mileage' : 'Unknown',
            'engine_size' : 'Unknown',
            'transmission' : 'Unknown',
            'fuel_type' : 'Unknown',
            'doors' : 'Unknown' }

    if check_exists_by_class(browser, specs_list_class_name):
        specs_list = browser.find_element_by_class_name(specs_list_class_name)
        available_specs = specs_list.find_elements_by_tag_name('li')

        #not all specs are always present, have to match by icon type
        for each_spec in available_specs:
            #the type of spec is buried in the second half of the icon's URL
            spec_icon = each_spec.find_element_by_tag_name('use')
            icon_link = spec_icon.get_attribute('xlink:href')
            icon_type = icon_link.split('#')[1]

            if icon_type == 'ks-manufactured-year':
                car_specs['year'] = each_spec.text
            if icon_type == 'ks-body-type':
                car_specs['body_style'] = each_spec.text
            if icon_type == 'ks-mileage':
                car_specs['mileage'] = each_spec.text
            if icon_type == 'ks-engine-size':
                car_specs['engine_size'] = each_spec.text
            if icon_type == 'ks-transmission':
                car_specs['transmission'] = each_spec.text
            if icon_type == 'ks-fuel-type':
                car_specs['fuel_type'] = each_spec.text
            if icon_type == 'ks-doors':
                car_specs['doors'] = each_spec.text
        
    #co2 emissions are the last item in a seperate "tech specs" table
    next_emission = 'Unknown'
    tech_specs_class_name = 'info-list.tech-specs__info-list'

    if check_exists_by_class(browser, tech_specs_class_name):
        tech_specs_table = browser.find_element_by_class_name(tech_specs_class_name)
        tech_specs_items = tech_specs_table.find_elements_by_tag_name('li')
        emissions_spans = tech_specs_items[-1].find_elements_by_tag_name('span')
        #co2emissions value is considered HTML and not "text" ...
        next_emission = emissions_spans[1].get_attribute('innerHTML') 

    #get the Auto Trader vehicle check list
    next_was_stolen = 'Unknown'
    next_was_write_off = 'Unknown'
    next_was_scrapped = 'Unknown'

    vl_class_name = 'basic-check-m__check-list'

    if check_exists_by_class(browser, vl_class_name):
        vehicle_list = browser.find_element_by_class_name(vl_class_name)
        vlist_items = vehicle_list.find_elements_by_tag_name('li')

        #order in the HTML list element is: stolen, scrapped, write off
        #value will be "Clear" for a good result
        both_spans = vlist_items[0].find_elements_by_tag_name('span')
        next_was_stolen = both_spans[1].text

        both_spans = vlist_items[1].find_elements_by_tag_name('span')
        next_was_scrapped = both_spans[1].text

        both_spans = vlist_items[2].find_elements_by_tag_name('span')
        next_was_write_off = both_spans[1].text

    #at this point we have everything, so build the Advertisement object
    next_ad.hyperlink = next_url
    next_ad.description = next_description 
    next_ad.seller_type = next_seller 
    next_ad.price = next_price 
    next_ad.year = car_specs['year']
    next_ad.mileage = car_specs['mileage']
    next_ad.body_style = car_specs['body_style']
    next_ad.co2emission = next_emission
    next_ad.doors = car_specs['doors']
    next_ad.transmission = car_specs['transmission']
    next_ad.was_stolen = next_was_stolen
    next_ad.was_write_off = next_was_write_off
    next_ad.was_scrapped = next_was_scrapped
    next_ad.engine_size = car_specs['engine_size']
    next_ad.fuel_type = car_specs['fuel_type']

    clean_up(browser)

    return next_ad




def main():

    #get requested car types
    cars_in = read_from_csv(CSV_FILE)

    #just a subset of the csv file ... to test
    cars_found = search_all_car_types(cars_in[9:10]) 
    
    #for all cars found, scrape data
    ads_list = scrape_all_cars(cars_found)

    #output sample data
    print(ads_list[1].to_string())


if __name__ == '__main__':
    main()


