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
Writes a series of objects to an excel sheet, then recalculates the sheet.
These objects should be in a Treemap, and need a Worksheet, Range, and Value variable.
Optionally only writes the differances from the last execution of this function, to reduce writing time.
-
Component by Jack Hymowitz, August 20, 2020

    Args:
        _excel: A running ExcelInterface from OpenExcel Workbook
        useDiff_: Set to True to only write the differance out to excel, enabled by default.
        color_: set to True to highlight outputted fields, enabled by default.
        _XL_Objects: TreeMap of objects to write with Worksheet, Range, and Value
    Returns:
        excel: The running ExcelInterface is outputted after this function runs.
        numWrites: The number of writes that occured, for debugging purposes.
"""
ghenv.Component.Name = "BT_WriteXLWorkbook"
ghenv.Component.NickName = "Write XL Workbook"
ghenv.Component.Message = 'AUG_20_2020'
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
ghenv.Component.Category = "BT"
ghenv.Component.SubCategory = "02 | IDF2PHPP"

from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs
import Grasshopper.Kernel as ghK
import scriptcontext as sc
from System import Object
from Grasshopper.Kernel.Data import GH_Path
import clr
from contextlib import contextmanager
clr.AddReferenceByName('Microsoft.Office.Interop.Excel')#, Culture=neutral, PublicKeyToken=71e9bce111e9429c')
from Microsoft.Office.Interop import Excel


class MyComponent(component):
    
    @staticmethod
    @contextmanager
    def writingToExcel(_excel):
        """ Changes the Excel Doc settings to help speed up """
        
        # Note: xlCalculationManual / Automatic set only works AFTER the workbook is opened
        
        try:
            _excel.ex.Calculation = -4135 
            _excel.ex.ScreenUpdating = False
            yield
        finally:
            _excel.ex.Calculation = -4105 
            _excel.ex.ScreenUpdating = True
    
    def checkPHPPVersion(self, _excel):
        """ Looks at !Data:D3 to find version number. Returns 'SI' or 'IP' unit type"""
        version = _excel.sheetsDict['Data'].Range['B3'].Value2
        
        if not version:
            print('Using "SI" Units')
            return 'SI'
        elif 'IP' in version:
            print('Using "IP" Units')
            return 'IP'
        else:
            print('Using "SI" Units')
            return 'SI'
    
    def doReadObjs(self, objects, _unitType):
        #If useDiff is false, this is used. Simply reads all objects in
        
        diff=[]
        for eachBranch in objects.Branches:
            for obj in eachBranch:
                diff.append((obj.getWorksheet(_unitType),obj.Range,obj.getValue(_unitType)))
        return diff
    
    def doDiff(self, objects, _unitType):
        #If useDiff is true (or not set), this is used. Only objects that have changed are written
        
        newObj={}
        for eachBranch in objects.Branches:
            for obj in eachBranch:
                newObj[(obj.getWorksheet(_unitType),obj.Range)]=obj.getValue(_unitType);
        
        diff=[]
        if "XLSdata" in sc.sticky:    #We are checking diffs
            oldObj=sc.sticky["XLSdata"]
            for x in newObj.keys():
                if not x in oldObj.keys() or oldObj[x]!=newObj[x]: #If the value didn't exist before or was changed, it's a change
                    diff.append((x[0],x[1],newObj[x]))
            for x in oldObj.keys():
                if not x in newObj.keys():                         #If the value existed before and is now gone, it is a change
                    diff.append((x[0],x[1],""))
            
        else:                                       #Not checking diffs
            for x in newObj.keys():
                diff.append((x[0],x[1],newObj[x]))
        sc.sticky["newXLSdata"]=newObj
        return diff
    
    def doWrite(self, excel, border, data):
        #Write out the data we have found
        
        with self.writingToExcel(excel):
            for eachItem in data:
                try:
                    excel.sheetsDict[eachItem[0]].Range[eachItem[1]].Value2 = eachItem[2]
                    if(border == None or border):
                        excel.sheetsDict[eachItem[0]].Range[eachItem[1]].Interior.ColorIndex=8
                except:
                    msg1 = "Sheet not found: " + eachItem[0]
                    ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg1)
            if "newXLSdata" in sc.sticky:
                sc.sticky["XLSdata"]=sc.sticky["newXLSdata"]
    
    def RunScript(self, excel, useDiff, border, XL_Objects):
        
        if not excel or not excel.activeWorkbook or not XL_Objects:
            msg1 = "No Excel Instance!"
            ghenv.Component.AddRuntimeMessage(ghK.GH_RuntimeMessageLevel.Warning, msg1)
            return (None,0)
        
        unitType = self.checkPHPPVersion(excel)
        
        if useDiff is None or useDiff:
            diff=self.doDiff(XL_Objects, unitType)
        else:
            diff=self.doReadObjs(XL_Objects, unitType)
        
        self.doWrite(excel, border,diff)
        excel.ex.Calculate()
        
        return (excel,len(diff))
