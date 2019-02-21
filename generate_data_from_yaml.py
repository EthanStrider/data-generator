from dateutil.relativedelta import relativedelta
from datetime import date, datetime, timedelta
from math import log, exp
import argparse
import string
import random
import numpy
import json
import yaml
import time
import os

parser = argparse.ArgumentParser()
parser.add_argument('--folder', dest='folder', required=True)

#-------------------------------------------------------------------
# GLOBAL VARIABLES
#-------------------------------------------------------------------

DATA_CONFIG = {}
DATA_MAP = {}
DIRECTORY = ""
ENTRIES = 0
CYCLES = 0
ENTRY = 0
CYCLE = 0

def reset_global_vars():
  global DATA_CONFIG
  global DIRECTORY
  global CYCLES
  global ENTRIES
  global ENTRY
  global CYCLE
  DATA_CONFIG = {}
  DATA_MAP = {}
  ENTRIES = 0
  CYCLES = 0
  ENTRY = 0
  CYCLE = 0

EMAIL_DOMAINS = [ "hotmail.com", "gmail.com", "aol.com", "mail.com" , "mail.kz", "yahoo.com"]
LETTERS = string.ascii_lowercase[:12]

#-------------------------------------------------------------------
# FUNCTIONS
#-------------------------------------------------------------------

def get_yaml_file_paths(folder):
  file_paths = []
  try:
    for subdir, dirs, files in os.walk(folder):
      for file in files:
        if ".yml" in file or ".yaml" in file:
          full_filename = os.path.join(subdir, file)
          file_paths.append(full_filename)
  except:
    print('Unexpected error:', sys.exc_info()[0],flush=True)
    raise
  return file_paths

def create_data_map(yaml_file):
  global DATA_CONFIG
  global DIRECTORY
  global CYCLES
  global ENTRIES
  with open(yaml_file) as config_file:
    DATA_CONFIG = yaml.safe_load(config_file)[0]
    CYCLES = DATA_CONFIG['config']['cycles']
    ENTRIES = DATA_CONFIG['config']['entries_per_cycle']
    for data_object in DATA_CONFIG['dataset']:
      if "distribution" in data_object['datatype']:
        expand_distribution(data_object)
      if "vector" in data_object['datatype']:
        expand_vector(data_object)
    index_name = DATA_CONFIG['index'] + "-" + datetime.today().strftime("%Y-%m-%d")
    DIRECTORY = create_directory(index_name, args.folder)
    # return data_config

def expand_distribution(data_object):
  global DATA_MAP
  field = data_object['field']
  distribution = data_object['distribution']
  if "normal" in data_object['datatype']:
    DATA_MAP[field] = numpy.linspace(distribution['min'], distribution['max'], CYCLES*ENTRIES)
  else:
    item_list = []
    for item in data_object['distribution']:
      item_list += ([item] * data_object['distribution'][item])
    DATA_MAP[field] = item_list

def expand_vector(data_object):
  field = data_object['field']
  start = data_object['start']
  finish = data_object['finish']
  growth_rate = data_object['growth_rate']
  growth_type = data_object['growth_type']
  DATA_MAP[field] = {}
  DATA_MAP[field]['value'] = data_object['start']
  if growth_rate == "calculate":
    if growth_type == "linear":
      DATA_MAP[field]['growth_rate'] = (finish-start)/CYCLES
      # print("linear " + str(DATA_MAP[field]['growth_rate']))
    elif growth_type == "compound":
      DATA_MAP[field]['growth_rate'] = 1-(start/finish)**(1/CYCLES)
      # print("compound " + str(DATA_MAP[field]['growth_rate']))
    elif growth_type == "exponential":
      DATA_MAP[field]['growth_rate'] = log(finish/start)/CYCLES
      # print("exponential " + str(DATA_MAP[field]['growth_rate']))
  else:
    DATA_MAP[field]['growth_rate'] = growth_rate
    # print(DATA_MAP[field]['growth_rate'])

def generate_json():
  json_object = {}
  for data_object in DATA_CONFIG['dataset']:
      json_item = FUNCTION_MAP[data_object['datatype']](data_object)
      json_object[data_object['field']] = json_item
  return json_object

def distribution_normal(data_object):
  anomoly = data_object['anomolies']
  if random.randrange(100) < anomoly['frequency']:
    return random.randint(anomoly['min'],anomoly['max'])
  rounding_place = data_object['distribution']['rounding_decimal_place']
  random_number = random.choice(DATA_MAP[data_object['field']])
  if rounding_place == 0:
    return int(round(random_number, rounding_place))
  return round(random.choice(DATA_MAP[data_object['field']]),rounding_place)

def distribution_items(data_object):
  return random.choice(DATA_MAP[data_object['field']])

def distribution_hours(data_object):
  hour = (random.choice(DATA_MAP[data_object['field']]) * 60)
  hour += random.randint((-1) * data_object['variance'],data_object['variance'])
  final_hour = (datetime.today() + timedelta(minutes=hour)).time()
  final_date = datetime.today() - timedelta(CYCLE)
  return datetime.combine(final_date, final_hour).strftime(data_object['format'])

def ip_address(data_object):
  return "%s.%s.%s.%s" % (random.randint(0,255),random.randint(0,255),random.randint(0,255),random.randint(0,255))

def boolean(data_object):
  variance = random.uniform((-1) * data_object['variance'],data_object['variance'])
  return random.randrange(100) < data_object['percentage_true'] + variance

def numerical_range(data_object):
  rounding_place = data_object['rounding_decimal_place']
  random_number = random.uniform(data_object['min'],data_object['max'])/data_object['divisor']
  if data_object['absolute']:
    random_number = abs(random_number)
  if rounding_place == 0:
    return int(round(random_number, rounding_place))
  return round(random_number, rounding_place)

def percentage(data_object):
  return random.uniform(data_object['min'],data_object['max'])

def vector(data_object):
  field = data_object['field']
  variance = random.randint((-1) * data_object['variance'], data_object['variance'])
  if data_object['growth_type'] == 'linear':
    DATA_MAP[field]['value'] += DATA_MAP[field]['growth_rate']
  elif data_object['growth_type'] == 'compound':
    DATA_MAP[field]['value'] += DATA_MAP[field]['value'] * DATA_MAP[field]['growth_rate']
  elif data_object['growth_type'] == 'exponential':
    DATA_MAP[field]['value'] *= exp(DATA_MAP[field]['growth_rate'])
  elif data_object['growth_type'] == 'per_cycle':
    return CYCLE * DATA_MAP[field]['growth_rate']
  DATA_MAP[field]['value'] += variance

  return int(round(DATA_MAP[field]['value'],0))

def email(data_object):
  variance = random.randint((-1) * data_object['variance'], data_object['variance'])
  length = data_object['name_length'] + variance
  return str(''.join(random.choice(LETTERS) for i in range(length)) + \
             '@' + random.choice(EMAIL_DOMAINS))

def date(data_object):
  increment_by = data_object['increment_by']
  increment_factor = data_object['increment_factor']
  if increment_by == "minute":
    return (datetime.today() - timedelta(minutes=+(CYCLE*increment_factor))).strftime(data_object['format'])
  if increment_by == "hour":
    return (datetime.today() - timedelta(hours=+(CYCLE*increment_factor))).strftime(data_object['format'])
  if increment_by == "day":
    return (datetime.today() - timedelta(days=+(CYCLE*increment_factor))).strftime(data_object['format'])
  if increment_by == "week":
    return (datetime.today() - timedelta(weeks=+(CYCLE*increment_factor))).strftime(data_object['format'])
  if increment_by == "month":
    return (datetime.today() - relativedelta(months=+(CYCLE*increment_factor))).strftime(data_object['format'])
  if increment_by == "year":
    return (datetime.today() - relativedelta(years=+(CYCLE*increment_factor))).strftime(data_object['format'])

def transpose_axes(input_file):
  output_file = DIRECTORY + "data_transposed.json"
  if os.path.isfile(output_file):
      os.remove(output_file)
  with open(input_file, 'r') as data_file:
    with open (output_file, 'w') as reorient_file:
      data_config = DATA_CONFIG['config']
      if data_config['final_orientation'] == "doc":
        for line in data_file:
          remap_data = []
          static_data = {}
          json_entry = json.loads(line)
          for key in json_entry:
            transpose = {}
            if key in data_config['remap_fields']:
              transpose[data_config['remap_fields'][key]] = key
              transpose["value"] = json_entry[key]
              remap_data.append(transpose)
            else:
              static_data[key] = json_entry[key]
          for item in remap_data:
            for key in static_data:
              item[key] = static_data[key]
              reorient_file.write(json.dumps(item) + "\n")

def create_directory(index, folder):
  directory = folder + "/" + index + "/_doc/"
  print("Create directory: " + directory)
  try:
      os.makedirs(directory)
  except FileExistsError:
      print("Directory already exists. Skipping...")
      pass
  return directory

FUNCTION_MAP = {
  'distribution-normal': distribution_normal,
  'distribution-items': distribution_items,
  'distribution-hours': distribution_hours,
  'percentage': percentage,
  'ip_address': ip_address,
  'boolean': boolean,
  'range': numerical_range,
  'vector': vector,
  'email': email,
  'date': date
}

#-------------------------------------------------------------------
# MAIN
#-------------------------------------------------------------------
if __name__ == '__main__':
  args = parser.parse_args()

  for yaml_file in get_yaml_file_paths(args.folder):
    reset_global_vars()
    create_data_map(yaml_file)
    start = time.time()

    entry_variance = DATA_CONFIG['config']['entry_variance']
    output_file_path = DIRECTORY  + "data.json"
    if os.path.isfile(output_file_path):
      os.remove(output_file_path)

    with open(output_file_path, 'w') as data_file:
      print("Generating data...")

      for cycle in range(CYCLES, 0, -1):
        random_entry_variance = random.randint((-1)*entry_variance,entry_variance)
        for entry in range(0, ENTRIES + random_entry_variance):
          CYCLE = cycle
          json_entry = json.dumps(generate_json())
          data_file.write(json_entry + "\n")

    if DATA_CONFIG['config']['final_orientation'] == "doc":
      transpose_axes(output_file_path)
      os.remove(output_file_path)

    print('DONE with %s\nGenerated %s documents in %.2f seconds' % (
          yaml_file, CYCLES*ENTRIES, time.time() - start
        ),flush=True)

  print("Done!")