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
This Component is used to apply a new PHPP-Style Fresh-Air Ventilation System to a Honeybee Zone or Zones.
-
EM Mar. 17, 2020
    Args:
        _VentSystem: Input the Ventilation System PHPP Object created by the 'New Vent System' Component
        _HBZones: The Honeybee Zones to apply this Fresh Air Ventilation System to
    Returns:
        HBZones_: The Honeybee Zones with the new Vent System paramaters applied.
"""

ghenv.Component.Name = "BT_SetZoneVentSystem"
ghenv.Component.NickName = "Set Zone Vent"
ghenv.Component.Message = 'MAR_17_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "BT"
ghenv.Component.SubCategory = "01 | Model"

import scriptcontext as sc

hb_hive = sc.sticky["honeybee_Hive"]()

# Add the Vent System Params to the Honeybee Zones
if _VentSystem and len(_HBZones)>0 and _HBZones[0] != None:
    HBZoneObjects = hb_hive.callFromHoneybeeHive(_HBZones)
    for zone in HBZoneObjects:
        # Set the Vent System for the Zone
        setattr(zone, 'PHPP_VentSys', _VentSystem)
        for room in zone.PHPProoms:
            # Assign the Vent Unit for the Zone's rooms
            setattr(room, 'VentUnitName', _VentSystem.Unit_Name)
            setattr(room, 'VentSystemName', _VentSystem.SystemName)
    
    # Add modified zones back to the HB dictionary
    if _VentSystem and len(_HBZones)>0:
        HBZones_  = hb_hive.addToHoneybeeHive(HBZoneObjects, ghenv.Component)
    else:
        HBZones_ = _HBZones
