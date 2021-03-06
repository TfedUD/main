#
# IDF2PHPP: A Plugin for exporting an EnergyPlus IDF file to the Passive House Planning Package (PHPP). Created by blgdtyp, llc
# 
# This component is part of IDF2PHPP.
# 
# Copyright (c) 2020, bldgtyp, llc <info@bldgtyp.com> 
# IDF2PHPP is free software; you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published 
# by the Free Software Foundation; either version 3 of the License, 
# or (at your option) any later version. 
# 
# IDF2PHPP is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
# GNU General Public License for more details.
# 
# For a copy of the GNU General Public License
# see <http://www.gnu.org/licenses/>.
# 
# @license GPL-3.0+ <http://spdx.org/licenses/GPL-3.0+>
#
"""
Inputs for 'Verification', 'Climate' and 'Ventilation | Airtightness' worksheet items
-
EM August 1, 2020
    Args:
        numResUnits_: <Optional, Default=1> Number of residential dwelling units in the building. For any non-residential, set to '1'
        mechCooling_: <Optional, Default='No'> Use mechanical cooling? 'x'=Yes, ' '=No
        thermalMass_: <Optional, Default=60>  Average Specific Heat Capacity (Wh/k-m2 TFA) of the building. Lightweight=60, Mixed=132, Heavy=204
        certification_: <Optional>
        buildingType_: <Optional> Input either: "1-Residential building" or "2-Non-residential building"
        ihgType_: <Optional> Internal Heat Gains Type. Input either: "10-Dwelling", "11-Nursing home / students", "12-Other", "20-Office / Admin. building", "21-School", or "22-Other"
        ighValues_: <Optional> Internal Heat Gains Source. 
        For Residential, Input either: "2-Standard" or "3-PHPP calculation ('IHG' worksheet)"
        For Non-Residential, input either: "2-Standard" or "4-PHPP calculation ('IHG non-res' worksheet)"
        occupancy_: <Optional> Only input for Non-Residential buildings or in special circumstances.
        epw_: <Optional, Default=None> The epw file path. Not used for anything yet.
        climateDataSet_: <Optional, Default='DE-9999-PHPP-Standard'> The name of the PHPP climate data set to use. Just type in for now. Maybe a value-list someday...
        altitude_: <Optional, Default='=J23'> Altitude adjustment factor (m) for the climate dataset. Default links to the weather station altidue loaded in the PHPP.
        exposure_E_: <Optional, Default=0.07> Wind Exposure Coefficient 'F'
        exposure_F_: <Optional, Default=15> Wind Exposure Coefficient 'F'
        ach50_: <Optional, Default=0.6ACH@50> A value (number) representing the tested ACH@50 envelope airtightness value. Passive House new construction max 0.6ACH@50, EnerPHit max 1.0ACH@50. Only input here if you want to overwrite the values input from the 'Airtightness' component or the values used by the Honeybee model.
        vn50_: <Optional, Default= Vv x 130%> Either input a list of values (numbers) or a list of geometry (Breps) representing the net-interior clear volume of the space (finish-to-finish). Only input here if you want to overwrite the values input from the 'Create PHPP Rooms' component(s) or the values used by the Honeybee model.
    Returns:
        verification_: Connect to the 'verification_' input on the 'Create Excel Obj - Setup' Component
        climate_: Connect to the 'climate_' input on the 'Create Excel Obj - Setup' Component
        airtightness_: Connect to the 'airtightness_' input on the 'Create Excel Obj - Setup' Component.
NOTE: only connect this if you want to overwrite the values automatically determined from the Honeybee / PHPP-Rooms values input earlier. Otherwise, leave unconnected.
"""

ghenv.Component.Name = "BT_SetPHPPSetup"
ghenv.Component.NickName = "PHPP Setup"
ghenv.Component.Message = 'AUG_01_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "BT"
ghenv.Component.SubCategory = "02 | IDF2PHPP"

from datetime import datetime
import rhinoscriptsyntax as rs
import ghpythonlib.components as gh
import scriptcontext as sc
import Grasshopper.Kernel as ghK

# Classes and Defs
preview = sc.sticky['Preview']
PHPP_ClimateDataSet = sc.sticky['PHPP_ClimateDataSet']

class Verification:
    def __init__(self, _numResUnits, _cooling, _specCapacity, _bldgName, _bldgCountry, _cert, _bldgType, _ihgType, _ihgVals, _occupancy):
        self.NumResUnits = _numResUnits
        self.MechCooling = _cooling
        self.SpecCapacity = _specCapacity
        self.BldgName = _bldgName
        self.BldgCountry = _bldgCountry
        self.Certification = _cert
        self.BuildingType = _bldgType
        self.IHG_Type = _ihgType
        self.IHG_Values = _ihgVals
        self.Occupancy = _occupancy
    
        if self.Occupancy:
            self.OccupancyMethod = '2-User determined'
            self.NumResUnits = 1
        else:
            self.OccupancyMethod = '1-Standard (only for residential buildings)'
        
        self.checkNonRes()
    
    def checkNonRes(self):
        if 'Non' in self.BuildingType and '1' in self.OccupancyMethod:
            warning = "For Non-Residential buildings, please be sure to input\n"\
            "the occupancy for the building."
            ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
        
        if 'Non' in self.BuildingType and '10' in self.IHG_Type:
            warning = "For Non-Residential buildings, please select a valid\n"\
            "Utilization Pattern: '20-Office / Admin. buildin', '21-School', or '22-Other'"
            ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
    
        if 'Non' not in self.BuildingType and self.Occupancy:
            warning = "For Residential buildings, please leave the occupancy blank.\n"\
            "Occupancy will be determined by the PHPP automatically. Only input an occupancy if\n"\
            "you are certain and that the Certifier will allow it."
            ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, warning)
    
    
    def __repr__(self):
        str = ("A Verification Worksheet Parameters Object with:",
                ' > Building Name: {}'.format(self.BldgName),
                ' > Builing Country: {}'.format(self.BldgCountry),
                ' > Num Res Units: {}'.format(self.NumResUnits),
                ' > Cooling: {}'.format(self.MechCooling),
                ' > Spec Capacity: {} Wh/k-m2-TFA'.format(self.SpecCapacity)
                )
        
        return '\n'.join(str)

class Climate:
    def __init__(self, _dataSet, _alt):
        self.DataSet = _dataSet
        self.Altitude = _alt
    
    def __repr__(self):
        str = ("A Climate Parameters Object with:",
            ' > Climate Data: {}'.format(self.DataSet),
            ' > Altitude: {}'.format(self.Altitude)
            )
        return '\n'.join(str)

class Airtightness:
    def __init__(self, _e, _f, _n50, _vn50):
        self.ACH50 = _n50
        self.Coef_E = _e
        self.Coef_F = _f
        self.VN50 = _vn50
    
    def __repr__(self):
        str = ("An Airtightness Parameters Object with:",
            ' > n50: {} ACH@50'.format(self.ACH50),
            ' > Coeff E: {}'.format(self.Coef_E),
            ' > Coeff F: {}'.format(self.Coef_F),
            ' > Vn50: {} m3'.format(self.VN50)
            )
            
        return '\n'.join(str)

# Building Name from datetime
prefix = 'Bldg Data from Grasshopper'
suffix = datetime.now().strftime("%Y-%b-%d")
bldgName = '{} {}'.format(prefix, suffix)

### Verification Worksheet Items
verification_ = Verification(
    numResUnits_ if numResUnits_ else 1, # Number of Resi Units
    mechCooling_ if mechCooling_ else 'No', # Use Mechanical Cooling?
    thermalMass_ if thermalMass_ else 60, # Specific Heat Capacity (avg)
    bldgName,
    country_ if country_ else 'US-United States of America',
    certification_ if certification_ else None,
    buildingType_ if buildingType_ else '1-Residential building',
    ihgType_ if ihgType_ else '10-Dwelling',
    ighValues_ if ighValues_ else '2-Standard',
    occupancy_ if occupancy_ else '')

### Climate Worksheet Items
climate_ = PHPP_ClimateDataSet(
        climateDataSet_ if climateDataSet_ else 'DE-9999-PHPP-Standard',
        altitude_ if altitude_ else '=J23') # Creat the Class Objcet

if epw_:
    # Figure out how to get monthly data from the EPW
    # Temps are easy.... radiation is not...
    pass

## Airtightness (Ventilation) Worksheet Items
# Find vN50. Takes in either a list of numbers, or a list of Breps
vN50_Total = [0]
if vn50_:
    for each in vn50_:
        try:
            vN50_Total.append(float(each))
        except:
            try:
                vol =  gh.Volume(rs.coercebrep(each))[0]
                vN50_Total.append(float(vol))
            except:
                pass

airtightness_ = Airtightness(
        exposure_E_ if exposure_E_ else 0.07, # Wind Protection 'E'
        exposure_F_ if exposure_F_ else 15, # Wind Protection 'F'
        ach50_ if ach50_ else 0.6,  # Overall ACH @50 value
        sum(vN50_Total) if vn50_ else '=N9*1.2') # Default Vn50= 120% if the Vv (Ventilation Volume)

#Preview
print('----\nVerification:')
preview(verification_)
print('----\nClimate:')
preview(climate_)
print('----\nAirtightness:')
preview(airtightness_)



