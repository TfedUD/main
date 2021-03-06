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
Takes inputs from the GH Scene and creates all the Excel-ready objects for writing to the PHPP
Each 'excel-ready' object has a Value, a Cell Range ('A4', 'BB56', etc...) and a Sheet Name
-
EM August 20, 2020
    Args:
        verification_: <Optional> 'Verification' Worksheet Items. Connect to the 'verification_' output from the 'PHPP Setup' Component
        climate_:  <Optional> 'Climate' Worksheet Items. Connect to the 'climate_' output from the 'PHPP Setup' Component
        airtightness_: <Optional> Envelope airtightness values for the 'Ventilation' Worksheet . Connect to the 'airtightness_' output from the 'PHPP Setup' Component
        ventilationSingle_: <Optional> Attach a single 'PHPP | Ventilation' components. Items for a simple fresh-air ventilation system for the 'Ventilation' worksheet. Connect to the 'ventilation_' output of the 'Ventilation' Component
        Heating_Cooling_: <Optional> Items for simple heating and cooling systems inputs. Connect to the 'Heating_Cooling_' output on the 'Heating / Cooling Equipment' Component
        summerVent_: <Optional> Set to 'True' to use the default values for a modest amount of summer ventilation, or leave empty to leave the worksheet blank. If True, will set both daytime and nightime window ventilation to be +50% the HRV/ERV winter value. 
----
If you prefer, simply enter a number here for the ACH (Air changes per hour) of window ventilation to enter. Note that if you only enter a single value, the daytime and nightime values will be set to this value. If you pass in 2 values in a multiline entry, the first value will be use for the daytime ACH and the second will be used for the nightime ACH.
        dhw_: <Optional>
    Returns:
        toPHPP_Setup_: A DataTree of the final clean, Excel-Ready output objects. Each output object has a Worksheet-Name, a Cell Range, and a Value. Connect to the 'Setup_' input on the 'Write 2PHPP' Component to write to Excel.
"""

ghenv.Component.Name = "BT_CreateXLObj_Setup"
ghenv.Component.NickName = "Create Excel Obj - Setup"
ghenv.Component.Message = 'AUG_20_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "BT"
ghenv.Component.SubCategory = "02 | IDF2PHPP"

import rhinoscriptsyntax as rs
import Grasshopper.Kernel as gh
from System import Object
from Grasshopper import DataTree
from Grasshopper.Kernel.Data import GH_Path
import scriptcontext as sc
import Grasshopper.Kernel as ghK

# Classes and Defs
PHPP_XL_Obj = sc.sticky['PHPP_XL_Obj'] 
preview = sc.sticky['Preview']

#-------------------------------------------------------------------------------
# Check Cooling is 'On' and give warnings
mechCooling_verification = False
mechCooling_equip = False
if verification_:
    if verification_.MechCooling == 'x':
        mechCooling_verification = True
if Heating_Cooling_.Branches:
    if Heating_Cooling_.Branch(1)[0].RecircCooling:
        mechCooling_equip = True
if mechCooling_equip==True and mechCooling_verification==False:
    msg1 = "It looks like you hooked up some cooling equipment \n but did not\n"\
    "turn it on in the 'PHPP Setup' component. \n Set 'mechCooling_' to 'x' \'n"\
    "to turn on Cooling in the model."
    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, msg1)
if mechCooling_equip==False and mechCooling_verification==True:
    msg1 = "It looks like you turned 'on' Active Cooling in the 'PHPP Setup'\n"\
    "Component \n but you didn't setup any Cooling Equipment in the\n"\
    "'Heating/Cooling Equip.' Component?"
    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, msg1)

#-------------------------------------------------------------------------------
# DHW
dhwSystem = []
if dhw_:
    dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J146', dhw_.forwardTemp, 'C', 'F' ))
    dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'P145', 0, 'C', 'F' ))
    dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'P29', 0, 'C', 'F' ))
    
    # Recirc Piping
    if len(dhw_.circulation_piping)>0:
        dhwSystem.append( PHPP_XL_Obj('Aux Electricity', 'H29', 1 ) ) # Circulator Pump
        
    for colNum, recirc_line in enumerate(dhw_.circulation_piping):
        col = chr(ord('J') + colNum)
        
        if ord(col) <= ord('N'):
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 149), recirc_line.length, 'M', 'FT' ))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 150), recirc_line.diam, 'MM','IN' ))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 151), recirc_line.insulThck, 'MM', 'IN' ))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 152), 'x' if recirc_line.insulRefl=='Yes' else '' ))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 153), recirc_line.insulCond, 'W/MK', 'HR-FT2-F/BTU-IN'  ))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 155), recirc_line.quality ))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 159), recirc_line.period ))
        else:
            dhwRecircWarning = "Too many recirculation loops. PHPP only allows up to 5 loops to be entered.\n"\
            "Consolidate the loops before moving forward"
            ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, dhwRecircWarning)
    
    # Branch Piping
    for colNum, branch_line in enumerate(dhw_.branch_piping):
        col = chr(ord('J') + colNum)
        
        if ord(col) <= ord('N'):
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 167), branch_line.diameter, 'M', 'IN'))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 168), branch_line.totalLength, 'M', 'FT'))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 169), branch_line.totalTapPoints))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 171), branch_line.tapOpenings))
            dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', '{}{}'.format(col, 172), branch_line.utilisation))
        else:
            dhwRecircWarning = "Too many branch piping sets. PHPP only allows up to 5 sets to be entered.\n"\
            "Consolidate the piping sets before moving forward"
            ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, dhwRecircWarning)
    
    # Tanks
    if dhw_.tank1:
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J186', dhw_.tank1.type) )
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J189', 'x' if dhw_.tank1.solar==True else '') )
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J191', dhw_.tank1.hl_rate, 'W/K', 'BTU/HR-F') )
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J192', dhw_.tank1.vol, 'LITER', 'GALLON') )
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J193', dhw_.tank1.stndbyFrac) )
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J195', dhw_.tank1.loction) )
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'J198', dhw_.tank1.locaton_t, 'C', 'F') )
    if dhw_.tank2:
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'M186', dhw_.tank2.type) )
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'M189', 'x' if dhw_.tank2.solar==True else '') )
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'M191', dhw_.tank2.hl_rate, 'W/K', 'BTU/HR-F') )
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'M192', dhw_.tank2.vol, 'LITER', 'GALLON') )
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'M193', dhw_.tank2.stndbyFrac) )
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'M195', dhw_.tank2.loction) )
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'M198', dhw_.tank2.locaton_t, 'C', 'F') )
    if dhw_.tank_buffer:
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'P186', dhw_.tank_buffer.type) )
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'P191', dhw_.tank_buffer.hl_rate, 'W/K', 'BTU/HR-F') )
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'P192', dhw_.tank_buffer.vol, 'LITER', 'GALLON') )
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'P195', dhw_.tank_buffer.loction) )
        dhwSystem.append( PHPP_XL_Obj('DHW+Distribution', 'P198', dhw_.tank_buffer.locaton_t, 'C', 'F') )

#-------------------------------------------------------------------------------
# Verification
verification = []
if verification_:
    verification.append( PHPP_XL_Obj('Verification', 'F28', verification_.NumResUnits if verification_ else 1  )) # Num Dwelling Units
    verification.append( PHPP_XL_Obj('Verification', 'K29', verification_.SpecCapacity if verification_ else 60, 'WH/KM2', 'BTU/FT2' )) # Spec Capacity
    verification.append( PHPP_XL_Obj('Verification', 'N29', verification_.MechCooling if verification_ else ''  )) # Cooling
    verification.append( PHPP_XL_Obj('Verification', 'K4', verification_.BldgName if verification_ else 'x' )) # Building Name
    verification.append( PHPP_XL_Obj('Verification', 'M7', verification_.BldgCountry if verification_ else 'US-United States of America'  )) # Building Country
    
    if verification_.Certification != None:
        verification.append( PHPP_XL_Obj('Verification', 'R78', verification_.Certification.energy_standard ))
        verification.append( PHPP_XL_Obj('Verification', 'R80', verification_.Certification.cert_class ))
        verification.append( PHPP_XL_Obj('Verification', 'R82', verification_.Certification.pe_type ))
        verification.append( PHPP_XL_Obj('Verification', 'R85', verification_.Certification.enerphit_type ))
        verification.append( PHPP_XL_Obj('Verification', 'R87', verification_.Certification.retrofit ))
    
    # IHG and Occupancy
    verification.append( PHPP_XL_Obj('Verification', 'R20', getattr(verification_, 'BuildingType', "1-Residential building" )))
    verification.append( PHPP_XL_Obj('Verification', 'R24', getattr(verification_, 'IHG_Type', '10-Dwelling' )))
    verification.append( PHPP_XL_Obj('Verification', 'R25', getattr(verification_, 'IHG_Values', '2-Standard' )))
    if getattr(verification_, 'Occupancy', '' ) != '':
        verification.append( PHPP_XL_Obj('Verification', 'Q29', getattr(verification_, 'Occupancy', '' )))
    verification.append( PHPP_XL_Obj('Verification', 'R29', getattr(verification_, 'OccupancyMethod', '1-Standard (only for residential buildings)' )))



#-------------------------------------------------------------------------------
# Climate Data
climate = []
if climate_:
    climate.append( PHPP_XL_Obj('Climate', 'D12', climate_.DataSet if climate_ else 'DE-9999-PHPP-Standard' )) # Climate Data Set Name (Dropdown)
    climate.append( PHPP_XL_Obj('Climate', 'D18', climate_.Altitude if climate_ else '=D17' )) # Altitude

#-------------------------------------------------------------------------------
# Airtightness
airtightness = []
if airtightness_:
    airtightness.append(PHPP_XL_Obj('Ventilation', 'N25', airtightness_.Coef_E if airtightness_ else float(0.07) ))# Wind protection E
    airtightness.append(PHPP_XL_Obj('Ventilation', 'N26', airtightness_.Coef_F if airtightness_ else float(15) ))# Wind protection F
    airtightness.append(PHPP_XL_Obj('Ventilation', 'N27', airtightness_.ACH50 if airtightness_ else float(0.6) ))# ACH50
    airtightness.append(PHPP_XL_Obj('Ventilation', 'P27', airtightness_.VN50 if airtightness_ else '=N9*1.2', 'M3', 'FT3' ))#  Internal Reference Volume

#-------------------------------------------------------------------------------
# Ventilation Single
vent = []
if ventilationSingle_:
    # Create the Vent Unit in the Components Worksheet
    vent.append( PHPP_XL_Obj('Components', 'JH15', ventilationSingle_.Unit_Name if ventilationSingle_ else 'Default_Name' )) #  Create the Vent Unit
    vent.append( PHPP_XL_Obj('Components', 'JI15', ventilationSingle_.Unit_HR if ventilationSingle_ else 0.75 )) #  Vent Heat Recovery
    vent.append( PHPP_XL_Obj('Components', 'JJ15', ventilationSingle_.Unit_MR if ventilationSingle_ else 0 )) #  Vent Moisture Recovery
    vent.append( PHPP_XL_Obj('Components', 'JK15', ventilationSingle_.Unit_ElecEff if ventilationSingle_ else 0.45, 'WH/M3', 'W/CFM'  )) #  Vent Elec Efficiency
    
    # Assign the Vent Unit
    vent.append( PHPP_XL_Obj('Ventilation', 'L12', ventilationSingle_.Unit_Type if ventilationSingle_ else '1-Balanced PH ventilation with HR' )) #  Assign the Vent Unit Type
    vent.append( PHPP_XL_Obj('Ventilation', 'K88', '01ud-{}'.format(ventilationSingle_.Unit_Name) if ventilationSingle_ else '01ud-Default_Name' )) #  Assign the Vent Unit
    vent.append( PHPP_XL_Obj('Ventilation', 'R90', ventilationSingle_.FrostTemp if ventilationSingle_ else '-5', 'C', 'F' )) #  HRV Frost Protection Limit
    
    # Ducts
    vent.append( PHPP_XL_Obj('Ventilation', 'N91', ventilationSingle_.Duct01.DuctLength if ventilationSingle_ else 5, 'M', 'FT'))
    vent.append( PHPP_XL_Obj('Ventilation', 'L106', ventilationSingle_.Duct01.DuctWidth if ventilationSingle_ else 104, 'MM', 'IN'))
    vent.append( PHPP_XL_Obj('Ventilation', 'L107', ventilationSingle_.Duct01.InsulationThickness if ventilationSingle_ else 52, 'MM', 'IN' ))
    vent.append( PHPP_XL_Obj('Ventilation', 'L109', 'x' ))# Reflective
    vent.append( PHPP_XL_Obj('Ventilation', 'L112', ventilationSingle_.Duct01.InsulationLambda if ventilationSingle_ else 0.04, 'W/MK', 'HR-FT2-F/BTU-IN'))
    
    vent.append( PHPP_XL_Obj('Ventilation', 'N93', ventilationSingle_.Duct02.DuctLength if ventilationSingle_ else 5, 'M', 'FT'))
    vent.append( PHPP_XL_Obj('Ventilation', 'Q106', ventilationSingle_.Duct02.DuctWidth if ventilationSingle_ else 104, 'MM', 'IN'))
    vent.append( PHPP_XL_Obj('Ventilation', 'Q107', ventilationSingle_.Duct02.InsulationThickness if ventilationSingle_ else 52, 'MM', 'IN'))
    vent.append( PHPP_XL_Obj('Ventilation', 'Q109', 'x' ))# Reflective
    vent.append( PHPP_XL_Obj('Ventilation', 'Q112', ventilationSingle_.Duct02.InsulationLambda if ventilationSingle_ else 0.04, 'W/MK', 'HR-FT2-F/BTU-IN'))


#-------------------------------------------------------------------------------
# PER
per = []
if Heating_Cooling_.Branches:
    per.append( PHPP_XL_Obj('PER', 'P10', Heating_Cooling_.Branch(0)[0].heatPrimaryGen if Heating_Cooling_.Branches else "5-Direct electricity" )) # Primary Heat Generator
    per.append( PHPP_XL_Obj('PER', 'P12', Heating_Cooling_.Branch(0)[0].heatScondaryGen if Heating_Cooling_.Branches else "-" )) # Secondary Heat Generator
    per.append( PHPP_XL_Obj('PER', 'S10', Heating_Cooling_.Branch(0)[0].heatFracPrimary if Heating_Cooling_.Branches else "1" )) # Heat Fraction Primary
    per.append( PHPP_XL_Obj('PER', 'T10', Heating_Cooling_.Branch(0)[0].dhwFracPrrimary if Heating_Cooling_.Branches else "0" )) # DHW Fraction Primary

#-------------------------------------------------------------------------------
# MECH
mech = []
if Heating_Cooling_.Branches: # If there are any mechanical equipment objects
    #---------------------------------------------------------------------------
    # Boiler
    if Heating_Cooling_.Branch(1)[0].Boiler:
        mech.append( PHPP_XL_Obj('Boiler', 'N21', Heating_Cooling_.Branch(1)[0].Boiler.Type)) 
        mech.append( PHPP_XL_Obj('Boiler', 'N22', Heating_Cooling_.Branch(1)[0].Boiler.Fuel)) 
        mech.append( PHPP_XL_Obj('Boiler', 'M31', Heating_Cooling_.Branch(1)[0].Boiler.UseTypicalValues)) 
    
    #---------------------------------------------------------------------------
    # Cooling Units
    if Heating_Cooling_.Branch(1)[0].SupplyAirCooling:
        onOff, maxPower, seer = Heating_Cooling_.Branch(1)[0].SupplyAirCooling.getValsForPHPP()
        mech.append( PHPP_XL_Obj('Cooling units', 'I15', 'x' ))
        mech.append( PHPP_XL_Obj('Cooling units', 'P17', onOff))
        mech.append( PHPP_XL_Obj('Cooling units', 'P18', maxPower, 'KW', 'BTU/H'))
        mech.append( PHPP_XL_Obj('Cooling units', 'P20', seer, 'W/W', 'BTU/HW'))
    
    if Heating_Cooling_.Branch(1)[0].RecircCooling:
        onOff, maxPower, volumeFlow, variableVol, seer = Heating_Cooling_.Branch(1)[0].RecircCooling.getValsForPHPP()
        mech.append( PHPP_XL_Obj('Cooling units', 'I22', 'x' ))
        mech.append( PHPP_XL_Obj('Cooling units', 'P24', onOff))
        mech.append( PHPP_XL_Obj('Cooling units', 'P25', maxPower, 'KW', 'BTU/H'))
        mech.append( PHPP_XL_Obj('Cooling units', 'P26', volumeFlow, 'M3/H', 'CFM'))
        mech.append( PHPP_XL_Obj('Cooling units', 'P28', variableVol))
        mech.append( PHPP_XL_Obj('Cooling units', 'P29', seer, 'W/W', 'BTU/HW'))
    
    if Heating_Cooling_.Branch(1)[0].AddnlDehumid:
        wasteHeat, SEER = Heating_Cooling_.Branch(1)[0].AddnlDehumid.getValsForPHPP()
        mech.append( PHPP_XL_Obj('Cooling units', 'I32', 'x' ))
        mech.append( PHPP_XL_Obj('Cooling units', 'P34', wasteHeat))
        mech.append( PHPP_XL_Obj('Cooling units', 'P35', SEER, 'W/W', 'BTU/HW'))
    
    if Heating_Cooling_.Branch(1)[0].PanelCooling:
        SEER = Heating_Cooling_.Branch(1)[0].PanelCooling.getValsForPHPP()
        mech.append( PHPP_XL_Obj('Cooling units', 'I37', 'x' ))
        mech.append( PHPP_XL_Obj('Cooling units', 'P39', SEER, 'W/W', 'BTU/HW'))



#-------------------------------------------------------------------------------
# Summer Vent
sumVent = []
if len(summerVent_)>0:
    if summerVent_[0] != False:
        try:
            sumVentACH_day = float(str(summerVent_[0]))
        except:
            sumVentACH_day = '=L20*0.5'
        
        try:
            sumVentACH_night = float(str(summerVent_[1]))
        except:
            sumVentACH_night = '=L31'
        
        sumVent.append( PHPP_XL_Obj('SummVent', 'L31', sumVentACH_day) )        # Daytime window Ventilation Default
        sumVent.append( PHPP_XL_Obj('SummVent', 'P59', sumVentACH_night))       # Nightime window Ventilation Default
        sumVent.append( PHPP_XL_Obj('SummVent', 'R21', ''))                     # HRV Summer Bypass - Clear
        sumVent.append( PHPP_XL_Obj('SummVent', 'R22', 'x'))                    # HRV Summer Bypass Set Temp difference (default)
        sumVent.append( PHPP_XL_Obj('SummVent', 'R23', ''))                     # HRV Summer Bypass - Clear
        sumVent.append( PHPP_XL_Obj('SummVent', 'R24', ''))                     # HRV Summer Bypass - Clear
 
#-------------------------------------------------------------------------------
# Add it all to a master Tree
toPHPP_Setup_ = DataTree[Object]() # Master tree to hold all the results
toPHPP_Setup_.AddRange(verification, GH_Path(0))
toPHPP_Setup_.AddRange(climate, GH_Path(1))
toPHPP_Setup_.AddRange(airtightness, GH_Path(2))
toPHPP_Setup_.AddRange(vent, GH_Path(3))
toPHPP_Setup_.AddRange(per, GH_Path(4))
toPHPP_Setup_.AddRange(mech, GH_Path(5))
toPHPP_Setup_.AddRange(sumVent, GH_Path(6))
toPHPP_Setup_.AddRange(dhwSystem, GH_Path(7))