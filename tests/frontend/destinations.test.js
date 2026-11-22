import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';
const source = readFileSync(new URL('../../dist/destinations.js', import.meta.url), 'utf8').split('window.addEventListener')[0];
test('Shared catalog refresh replaces browser arrays with server rows', async () => {
  const rows = [{ id: 'a', province_id: 1, kind: 'attractions', name: 'Điểm mới', description: 'Dùng chung', url: '/a.jpg', source: 'Nguồn', version: 2 }];
  const provinces = [{id:1, attractions:['Cũ'], specialties:['Cũ']}];
  const images = {};
  const context=vm.createContext({PROVINCES: provinces, IMAGE_MAP: images, fetch: async () => ({ok: true,json: async()=>({entries: rows})})});
  vm.runInContext(source,context);
  await vm.runInContext('refreshDestinations()',context);
  assert.equal(provinces[0].attractions[0], 'Điểm mới');
  assert.equal(provinces[0].specialties.length,0);
  assert.equal(images['Điểm mới'].description,'Dùng chung');
});
test('Failed refresh preserves the last readable catalog', async () => {
  const provinces=[{id:1, attractions:['Cũ'],specialties:[]}];
  const context=vm.createContext({PROVINCES:provinces,IMAGE_MAP:{},fetch:async()=>({ok:false})});
  vm.runInContext(source,context);
  await assert.rejects(vm.runInContext('refreshDestinations()',context));
  assert.equal(provinces[0].attractions[0],'Cũ');
});
test('Same named entries retain province-specific descriptions', () => {
  const app=readFileSync(new URL('../../dist/app.js',import.meta.url),'utf8');
  const fn=app.slice(app.indexOf('function destinationMetadata'),app.indexOf('function minis'));
  const context=vm.createContext({IMAGE_MAP:{},destinationEntries:[
    {province_id:1,kind:'specialties',name:'Món ăn',description:'Tỉnh 1'},
    {province_id:2,kind:'specialties',name:'Món ăn',description:'Tỉnh 2'},
  ]});
  vm.runInContext(fn,context);
  assert.equal(vm.runInContext("destinationMetadata('Món ăn',1,'specialties').description",context),'Tỉnh 1');
  assert.equal(vm.runInContext("destinationMetadata('Món ăn',2,'specialties').description",context),'Tỉnh 2');
});
