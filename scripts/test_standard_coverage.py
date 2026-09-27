import json
from pathlib import Path
from app.coverage import evaluate_standard_coverage
from app.standards_repository import build_knowledge_evidence_bundle, build_matcher_cases

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'demo_data/complete_demo_database.json').read_text())
knowledge={k:v for k,v in data.items() if isinstance(v,list)}
cases=build_matcher_cases(knowledge)
prod=next(x for x in data['products'] if x['productId']=='electrical-appliances-1')
primary={'standardId':'IS-374-2019','isNumber':'IS 374 : 2019'}
bundle=build_knowledge_evidence_bundle(dataset='demo',knowledge=knowledge,canonical_product=prod,primary_standard=primary,matcher_cases=cases)
profile={
 'product':{'name':'Ceiling fan'},
 'application':{'useCase':'Air circulation','environment':'Indoor classrooms / offices'},
 'dimensions':{'sweep':'1200 mm'},
 'technicalProperties':{'voltage':'230 V AC','frequency':'50 Hz'},
 'performance':{'silent':'silent operation','air':'air performance','starting':'starting performance','endurance':'endurance'},
 'safety':{'electrical':'Electrical safety required'},
 'testing':{'air':'air performance testing','speed':'speed measurement','power':'power factor testing','endurance':'endurance testing'},
 'certification':{'requested':True,'details':'Determine BIS Product Certification applicability and mandatory status.'},
}
r=evaluate_standard_coverage(requirement_profile=profile,knowledge_bundle=bundle)
by={x['key']:x for x in r['requirements']}
assert r['evaluated'] is True
assert by['product']['status']=='COVERED'
assert by['application']['status'] in {'COVERED','PARTIAL'}
assert by['performance']['status'] in {'COVERED','PARTIAL'}
assert by['safety']['status']=='PARTIAL'
assert by['testing']['status'] in {'COVERED','PARTIAL'}
assert by['dimensions']['status']=='UNKNOWN'
assert by['technicalProperties']['status']=='UNKNOWN'
assert by['certification']['status']=='COVERED'
assert bundle['certifications'][0]['mandatory'] is True
assert bundle['qcos'][0]['effectiveDate'] is None
assert bundle['version']['reaffirmed'] is None
assert bundle['provenance']['productId']=='electrical-appliances-1'
assert bundle['provenance']['primaryStandardId']=='IS-374-2019'
assert 'rel-is-374-2019-1' in bundle['provenance']['relationshipIds']
assert 'cert-ceiling-fan' in bundle['provenance']['certificationIds']
assert 'qco-ceiling-fans-2023' in bundle['provenance']['qcoIds']
assert bundle['provenance']['versionRecordId']=='ver-is-374-2019'
assert by['product']['sourceRecordIds']
assert by['safety']['sourceRecordIds']
assert by['certification']['sourceRecordIds']
print('STANDARD COVERAGE + KNOWLEDGE BUNDLE REGRESSION TESTS: PASS')
print(r['summary'])
