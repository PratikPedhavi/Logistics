# PALLETIZATION - Estimate the optimal size of the pallets where size of SKU and trucks is given

from http.server import executable
import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory
import numpy as np

def get_data_model():
    data = {}
    data['sku_area'] = 1          # in sq.mtr.
    data['sku_height'] = 1          # in cms
    data['sku_numbers'] = 100
    data['truck_base_area'] = 40    # in sq. mtr 
    data['truck_height'] = 3        # in mtr
    data['truck_numbers'] = 5
    return data

def main(palcount):
    data = get_data_model()
    sku_area = data['sku_area']
    sku_height = data['sku_height']
    sku_numbers = data['sku_numbers']
    truck_area = data['truck_base_area']
    truck_height = data['truck_height']
    truck_numbers = data['truck_numbers']
    stacked = int(truck_height//sku_height)
    PALLET_NUMBERS = palcount
    PALLET_SIZE_LIMIT = 20
    setP = range(PALLET_NUMBERS)

    # MODEL
    model = pyo.ConcreteModel()
    model.pallet_size = pyo.Var(within=Integers, bounds=(0,PALLET_SIZE_LIMIT))
    model.sku = pyo.Var(range(sku_numbers), range(PALLET_NUMBERS), within=Binary)
    model.pallet = pyo.Var(range(PALLET_NUMBERS),within=Integers,bounds=(0,1))
    model.used_pallet_count = pyo.Var(within=Integers, bounds=(0,PALLET_NUMBERS))
    model.obj1 = pyo.Var(bounds=(0,None))
    model.obj2 = pyo.Var(within=Integers, bounds=(0,None))
    model.skuPerPallet = pyo.Var(within=Integers, bounds=(0,None))

    # CONSTRAINTS
    # SKU volume in a pallet should be less than the pallet volume
    model.pal_vol = pyo.ConstraintList()
    sku_volume = sku_area*sku_height
    for j in setP:
        model.pal_vol.add(expr= sku_volume * model.skuPerPallet <= model.pallet[j] * model.pallet_size)

    # Used pallets are saved as another variable
    model.pallets_used = pyo.Constraint(expr = sum([model.pallet[k] for k in range(PALLET_NUMBERS)]) == model.used_pallet_count)

    # skus assigned to a pallet should be less than the variable skuPerPallet
    model.sku_pallet = pyo.ConstraintList()
    for k in range(PALLET_NUMBERS):
        model.sku_pallet.add(expr= sum([model.sku[(i,k)] for i in range(sku_numbers)]) <= model.pallet[k] * model.skuPerPallet)

    # Every SKU should be assigned to exactly one pallet
    model.sku_once = pyo.ConstraintList()
    for k in range(sku_numbers):
        model.sku_once.add(expr= sum([model.sku[(k,i)] for i in range(PALLET_NUMBERS)]) == 1)

    # Empty volume saved as obj1
    model.pal_vol_total = pyo.Constraint(expr= model.used_pallet_count * model.pallet_size - sku_volume*sku_numbers == model.obj1)

    pallet_use_penalty = sum([50*model.pallet[k] for k in range(PALLET_NUMBERS)])
    model.obj = pyo.Objective(expr=pallet_use_penalty, sense=minimize)
    
    # model.pprint()

    opt = SolverFactory('couenne', executable='C:\\couenne\\bin\\couenne.exe')
    opt.solve(model)

    print('Pallet Size: {}'.format(pyo.value(model.pallet_size)))
    print('Empty space: {}'.format(pyo.value(model.obj1)))
    print('SKU per pallet: {}'.format(pyo.value(model.skuPerPallet)))

    allocation = {}
    for i in range(sku_numbers):
        for j in range(PALLET_NUMBERS):
            if pyo.value(model.sku[(i,j)]):
                if j in allocation.keys():
                    allocation[j] = allocation[j] + [i]
                else:
                    allocation[j] = [i]
    print('Total Pallets used: {}'.format(len(allocation)))
    print('SKU allocation to pallets: {}'.format(allocation))
    return

if __name__ == '__main__':
    main(10)