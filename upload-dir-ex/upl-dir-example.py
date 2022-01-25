#!/usr/bin/env python
# coding: utf-8

# Suppose you have some custom modules, named pipeline and external_fns, and want to use them on a coiled cluster.
# And, further suppose that these are contained in folders within your current working directory for Python. 
# 
# These will work automatically with a Local.Cluster, as your system already knows to look for them in the current
# active directory.  However, for these functions to work on a Coiled Cluster, the Dask workers need to know how to
# find those modules.  
# 
# The following sample code shows how to do this.

# Code based on input from Kelsey Skvoretz (https://github.com/skvorekn; 
# https://github.com/skvorekn/repr-coiled-upl-dir) and 
# James Bourbeau (https://github.com/jrbourbeau)

# In[1]:

# Imports you will need

# In addition to your custom modules, your current environment will need to include 
# dask & distributed, with all of their depenencies.  These will already be in a 
# coiled default environment.

# Standard Packages
import os

# Specialty Packages
from dask.distributed import Client, LocalCluster
from distributed.diagnostics.plugin import UploadDirectory

# Coiled
import coiled

# Your custom modules.
from external_fns.misc import get_prefix
from pipeline.functions.item_level import runner

# In[2]:

# Create a Cluster

get_prefix()
cluster = coiled.Cluster(
            name='upload-directory-test',
            n_workers=1,
            worker_cpu=1,
            worker_class='distributed.Nanny'  #  Need to test if this is required.
        )
client = Client(cluster)
client.wait_for_workers(n_workers=1)
print("Created client")

# In[3]:

# Function to update paths on workers & code to upload modules. 

def update_path(dask_worker):
        import pathlib
        import sys
        path = str(pathlib.Path(dask_worker.local_directory).parent)
        if path not in sys.path:
            sys.path.insert(0, path)

client.run(update_path)

plugin = UploadDirectory('pipeline', update_path=False, restart=False)
client.register_worker_plugin(plugin) 

print("Client Path Updated")

# In[4]:

# See what the directory structure looks like
def test_func():
    dirs = []
    for d in os.walk('dask-worker-space'):
        dirs.append(d)
    return dirs

job = client.submit(test_func)
print(job.result())

# Example output:
# [
#     (
#         'dask-worker-space',
#         ['worker-pvqyc2yh', 'pipeline'],
#         ['worker-pvqyc2yh.dirlock', 'purge.lock', 'global.lock']
#     ),
#     ('dask-worker-space/worker-pvqyc2yh', ['storage'], []),
#     ('dask-worker-space/worker-pvqyc2yh/storage', [], []),
#     ('dask-worker-space/pipeline', ['functions'], ['__init__.py', 'errors.py']),
#     ('dask-worker-space/pipeline/functions', [], ['__init__.py', 'item_level.py'])
# ]

# In[5]:

# Show that all works. 
runner(client)

# In[6]:

# Clean up

client.close()
cluster.close()

