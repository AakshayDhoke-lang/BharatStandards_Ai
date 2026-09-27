from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from app.bis_intelligence_service import build_model_query,get_bis_intelligence
p={'product':{'name':'Centrifugal Water Pump','category':'Pump','subcategory':'Centrifugal'},'application':{'useCase':'clean water transfer','environment':'institutional water supply'},'materials':[],'technicalProperties':{},'performance':{'head':'required','discharge':'required'},'testing':{'performance':'required'},'safety':{}}
q=build_model_query(p);assert 'Centrifugal Water Pump' in q;assert 'IS ' not in q
r=get_bis_intelligence().recommend_standard(p);assert r['decision'] in {'MODEL_UNAVAILABLE','MATCH','NEEDS_REVIEW','NO_MATCH'}
print('PASS',r['decision'])
