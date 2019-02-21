import csv
import json, os, sys, argparse, time
from elasticsearch import Elasticsearch
from elasticsearch.helpers import parallel_bulk

parser = argparse.ArgumentParser()
parser.add_argument('--folder', dest='folder', required=True)
parser.add_argument('--use_ssl', dest='use_ssl', action='store_true', default=False)
parser.add_argument('--es_host', dest='es_host', required=True)
parser.add_argument('--es_user', dest='es_user', required=False, default='elastic')
parser.add_argument('--es_password', dest='es_password', required=False, default='changeme')
parser.add_argument('--thread_count', dest='thread_count', required=False, default=4, type=int)
parser.add_argument('--chunk_size', dest='chunk_size', required=False, default=1000, type=int)
parser.add_argument('--timeout', dest='timeout', required=False, default=120,type=int)
parser.add_argument('--format', dest='format', required=False, default="json", choices=["json","csv"])
parser.add_argument('--pipeline', dest='pipeline', required=False)
parser.add_argument('--delete_existing', dest='delete_existing', action='store_true', default=False)

def handle_data_file(file_path, index, type, format):
    print('Indexing %s into index %s and type %s' % (file_path, index, type),flush=True)
    if format == "json":
        with open(file_path, 'r', encoding='utf8') as f:
            for line in f:
                doc = json.loads(line)
                doc['_index'] = index
                doc['_type'] = type
                yield doc
    else:
        with open(file_path, 'r', encoding='utf8') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                doc = dict(row)
                doc['_index'] = index
                doc['_type'] = type
                yield doc


def iterate_config_files(folder):
    f_depth = len(list(filter(None,folder.split(os.sep))))
    try:
        for subdir, dirs, files in os.walk(folder):
            for file in files:
                if file == "config.json" and f_depth == 2:
                    full_filename = os.path.join(subdir, file)
                    comps = os.path.split(subdir)
                    index = comps[len(comps)-1]
                    yield index, full_filename
    except:
        print('Unexpected error:', sys.exc_info()[0],flush=True)
        raise



def iterate_data_files(folder):
    f_depth = len(list(filter(None,folder.split(os.sep))))
    try:
        for subdir, dirs, files in os.walk(folder):
            for file in files:
                if not file == "config.json":
                    full_filename = os.path.join(subdir, file)
                    locations = list(filter(None, subdir.split(os.sep)))
                    if len(locations) - f_depth < 2:
                        print("Path depth %s"%(len(locations) - f_depth),flush=True)
                        print( 'Skipping location %s as insufficient path depth' % full_filename,flush=True)
                    else:
                        print('Processing file %s' % full_filename,flush=True)
                        index = locations[len(locations) - 2]
                        type = locations[len(locations) - 1]
                        yield index, type, full_filename
    except:
        print('Unexpected error:', sys.exc_info()[0],flush=True)
        raise

if __name__ == '__main__':
    args = parser.parse_args()
    es = Elasticsearch(hosts=[args.es_host], http_auth=(args.es_user, args.es_password), use_ssl=args.use_ssl, verify_certs=True, timeout=args.timeout)
    start = time.time()
    cnt = 0
    indices=set()

    for index, full_filename in iterate_config_files(args.folder):
        with open(full_filename,"r") as config_file:
            config = json.loads(config_file.read())
            if args.delete_existing:
                print("Deleting existing %s"%index)
                es.indices.delete(index=index, ignore=[400, 404])
            print("Creating index %s"%index)
            es.indices.create(index=index, body=config, ignore=[400, 404])

    for index, type, data_file in iterate_data_files(args.folder):
        indices.add(index)
        for success, info in parallel_bulk(
              es,
              handle_data_file(data_file, index, type, args.format),
              thread_count=args.thread_count,
              chunk_size=args.chunk_size,
              timeout='%ss'%args.timeout,
              pipeline=args.pipeline
        ):
          if success:
              cnt += 1
              if cnt % args.chunk_size == 0:
                  print('Indexed %s documents'%str(cnt),flush=True)
                  sys.stdout.flush()
          else:
              print('Doc failed', info)
        print('DONE\nIndexed %s documents in %.2f seconds' % (
          cnt, time.time() - start
        ),flush=True)
        print('INDEXING COMPLETE',flush=True)
    for index in indices:
        print('Refreshing index %s'%index,flush=True)
        es.indices.refresh(index=index)
        print('DATA LOAD COMPLETE',flush=True)
