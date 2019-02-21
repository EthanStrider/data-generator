# DATA-GENERATOR

**Generates JSON data based on provided YAML config file(s).**

This is a very simple data generator.  It's not very intelligent, but it's relatively quick and can automatically upload all the generated data straight into elasticsearch (using @gingerwizard's `load_data.py` script).  The goal is simply to cut out a lot of the manual work and save people time when generating quick bits of data.  Enjoy, and feel free to add new data-types!

_________________________________________________________________

### Running the script

```
./generate_data.sh
```

For convenience, inside `generate_data.sh`, there are several parameters:
```
DG_DIRECTORY_PATH="./examples"
DG_ELASTICSEARCH_HOST="my_elasticsearch_instance.us-central1.gcp.cloud.es.io:9243"
DG_ELASTICSEARCH_USER="elastic"
DG_ELASTICSEARCH_PASS="super_secure"
UPLOAD_TO_ELASTICSEARCH=false
```

Configure these parameters if you would like to automatically upload all generated data to your elasticsearch instance.

_________________________________________________________________

## Basic yaml config example

```
- index: "name-of-index"
  config:
    cycles: 12                  # Number of days, weeks, months (i.e. loops)
    entries_per_cycle: 500      # Number of JSON entries per loop
    entry_variance: 270         # Variance +/- in the number of entries per loop
    final_orientation: column   # Can be used to transpose colums (explained later)
  dataset:
  - datatype: date
    field: "@timestamp"
    format: "%Y-%m-%d"
    increment_by: month
    increment_factor: 1
```

## How are the dates/timestamps calculated?

For the `basic-yaml-config` example shown above, the script would do the following:
It will subtract 12 months (cycles) from the current date, and then iterate by month up to the current date.

*Right now, it's a very simple process, but it could be better.
It really should support a custom start and end date, but for now, that's how it works.*

## How are the other data values calculated?

Right now, every data value is calculated once per cycle per entry.  There is no correlation between datatypes.  In other words, each datatype is calculated individually and randomly.

## DATA TYPES CURRENTLY SUPPORTED:

### date
```
  - datatype: date
    field: name_of_field
    format: "%Y-%m-%d"
    increment_by: months        # Valid input: year, month, week, day, hour, minute
    increment_factor: 1         # Incrementing by 2 months ==> Jan, March, May, etc
```

### boolean
```
  - datatype: boolean
    field: name_of_field
    percentage_true: 50
    variance: 25                # The "percentage_true" value will randomly vary +/- this amount
```

### distribution
**distribution-items**
Chooses a item/value based on the provided "frequency" distribution
```
  - datatype: "distribution-items"
    field: name_of_field
    distribution:
      value1: 6                 # "value1" will appear in the data with a frequency of 6/(6 + 3 + 2) = 6/11
      value2: 3                 # "value2" will appear in the data with a frequency of 3/(6 + 3 + 2) = 3/11
      value3: 2                 # "value3" will appear in the data with a frequency of 2/(6 + 3 + 2) = 2/11
```
**distribution-normal**
Chooses a number from a normal distribution based on the min/max values
```
  - datatype: "distribution-normal"
    field: name_of_field
    distribution:
      min: 1                    # Minimum possible value in the normal distribution
      max: 100                  # Maximum possible value in the normal distribution
      size: 100                 # The number of values to choose from (i.e. the "coarseness" of the distribution)
      rounding_decimal_place: 0
    anomolies:                  # If you want anomolies in your distribution, you can set them here
      min: 500
      max: 1000
      frequency: 0.0005         # Or, set the frequency to 0 for no anomolies
```
**distribution-hours**
Chooses a time of day based on the provided "frequency" distribution
```
  - datatype: "distribution-hours"
    field: name_of_field
    format: "%Y-%m-%dT%H:%M:%S.%fZ"
    variance: 90                # The maximum number of minutes this timestamp can vary +/- by
    distribution:
      23: 1                     # Any value between 0-24 (hours) is valid.
      21: 3
      19: 5
      17: 8
      15: 5
      13: 4
      11: 4
      9: 5
      7: 8
      5: 3
      3: 1
      1: 1
```

### email
```
  - datatype: email
    field: name_of_field
    name_length: 9              # The number of characters in the email name
    variance: 3                 # The maximum number of characters this email name can vary +/- by
```

### ip_address
```
  - datatype: ip_address
    field: name_of_field
```

### percentage
```
  - datatype: percentage
    field: name_of_field
    min: 0.001
    max: 0.999
```

### range
```
  - datatype: range
    field: name_of_field
    max: 10
    min: 0
    absolute: True              # If "True", the number will never be negative (affects the distribution)
    divisor: 1                  # Divide the resulting number by this value (affects the distribution)
    rounding_decimal_place: 0
```

### vector
**linear**
```
  - datatype: vector
    field: linear_start_finish_vector
    start: 0
    finish: 100                 # Can be set to "calculate" if the "growth_rate" is explicitly set
    growth_rate: calculate      # If this value is set, it will always override the "finish" value
    growth_type: linear
    variance: 0                 # Creates random turbulence in the data instead of a perfect line
```
**compound**
```
  - datatype: vector
    field: compound_vector
    start: 10
    finish: 1000                # Can be set to "calculate" if the "growth_rate" is explicitly set
    growth_rate: calculate      # If this value is set, it will always override the "finish" value
    growth_type: compound
    variance: 0                 # Creates random turbulence in the data instead of a perfect line
```
**exponential**
```
  - datatype: vector
    field: exponential_vector
    start: 10
    finish: 1000                # Can be set to "calculate" if the "growth_rate" is explicitly set
    growth_rate: calculate      # If this value is set, it will always override the "finish" value
    growth_type: exponential
    variance: 0                 # Creates random turbulence in the data instead of a perfect line
```
**per_cycle**
Only changes once per cycle.  So, all entries in a given cycle will have the same value
```
  - datatype: vector
    field: per_cycle_vector
    start: 1
    finish: calculate            # Can be set to "calculate" if the "growth_rate" is explicitly set
    growth_rate: 1               # If this value is set, it will always override the "finish" value
    growth_type: per_cycle
    variance: 0                 # Creates random turbulence in the data instead of a perfect line
```

_________________________________________________________________
## Transposing columns

The transposing function is pretty hacky at this point...  You can look at the `vectors-transposed.yml` example in the `examples` folder.

First, set the `final_orientation` value to be "doc".

Then, in the "master config" section, set the field that you want to remap along with the name of the new field that each old field is going to be mapped into.

```
    final_orientation: doc
    remap_fields:
      existing_field_name_1: transposed_field_name
      existing_field_name_2: transposed_field_name
```

If all goes well, the data will be transposed from this...

| existing_field_name_1 | existing_field_name_2 |
|-----------------------|-----------------------|
| value1_A              | value2_A              |
| value1_B              | value2_B              |

Into this...

| transposed_field_name | value                 |
|-----------------------|-----------------------|
| existing_field_name_1 | value1_A              |
| existing_field_name_2 | value2_A              |
| existing_field_name_1 | value1_B              |
| existing_field_name_2 | value1_B              |

The really hacky bit is that the name of the second field is hard-coded to "value" right now.  Haven't gotten a chance to make it more robust. :\

_________________________________________________________________

## Adding new data-types

It's pretty easy to add new data-types.  Simply go to the `generate_data_from_yaml.py` script and write the function that you need.  Then, add your "data-type name" and your "function name" to the `FUNCTION_MAP`.