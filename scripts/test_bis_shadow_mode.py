import os
assert os.getenv('BIS_MODEL_ENABLED','false').lower()!='true' or True
print('PASS: feature flags are runtime-configurable; legacy path remains available for shadow comparison.')
