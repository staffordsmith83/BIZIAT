# Title of Script: BIZIAT ArcMap AddIn
# Description: This is the python code for an ArcMap Addin. The behaviour of each button or combobox or tool on the AddIn
# toolbars is described with a separate class.

# Author: Stafford Smith
#         GIS Programming, Curtin University
# Creation date: 20/10/2019 (SS)
# Last update: 04/11/2019 (SS)

#=== IMPORTS
import arcpy
import pythonaddins
import webbrowser
import csv
from threading import Thread

#=== GLOBALS
tide_height = 0
global selected_lyr # maybe unnecessary to emphasise that this is a global variable
selected_lyr = 'known_tracks'

#=== FUNCTIONS
# define openbrowser function before defining help button class. Appears to help with ArcMap crashing behaviour.
def OpenBrowserURL():
    webbrowser.open(r"C:\Users\s\Documents\Masters of Geospatial\GISP\Assignment2\BIZIAT_AddIn\Install\help.html",new=2)

#=== CLASSES
class CalcExtents(object):
    """Implementation for BIZIAT_CalcExtents.button (Button).
    Takes tide height value from user and DEM. Reclassifies DEM
    based on tide height value. Creates two extent feature classes
    from this reclassified DEM. Overwrites existing extent layers.
    Extent layers called submerged_extent and exposed_extent."""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        arcpy.env.workspace = r"C:\Users\s\Documents\Masters of Geospatial\GISP\Assignment2\GISdata"
        # reclassify NIDEM based on user input tide value
        # replace tide_height float with a parameter from Tide Height combo box

        reclass_values = "-2.601000 {0} 0;{0} 2.772000 1".format(tide_height)
        #   may need to replace output path with reference to workspace...
        if arcpy.Exists("NIDEM_reclass.tif"):
            arcpy.Delete_management("NIDEM_reclass.tif")

        arcpy.env.overwriteOutput = True    # temporarily allow overwriting of exisitng datasets, then disallow.
        arcpy.gp.Reclassify_sa("NIDEM.tif", "VALUE", reclass_values,
                               "C:/Users/s/Documents/Masters of Geospatial/GISP/Assignment2/GISdata/NIDEM_reclass.tif",
                               "DATA")

        # RasterToPolygon(in_raster, out_polygon_features, {simplify}, {raster_field}, {create_multipart_features}, {max_vertices_per_feature})
        arcpy.RasterToPolygon_conversion("NIDEM_reclass.tif", "zones.shp", "NO_SIMPLIFY",
                                         "VALUE")

        # Select(in_features, out_feature_class, {where_clause})
        if arcpy.Exists("submerged_extent"):
            arcpy.Delete_management("submerged_extent")
        arcpy.Select_analysis("zones", "submerged_extent", '"gridcode" = 0')

        if arcpy.Exists("exposed_extent"):
            arcpy.Delete_management("exposed_extent")
        arcpy.Select_analysis("zones", "exposed_extent", '"gridcode" = 1')

        arcpy.env.overwriteOutput = False

class ChooseAnalysis(object):
    """Implementation for BIZIAT_Analysis.combobox (ComboBox).
    Allows the user to select between three intersection analyses.
    Will find intersection of the selected layer with the exposed extent of the
    intertidal zone (or other options).
    This tool is essentially a data filter, and results in a new selection."""

    def __init__(self):
        self.items = ["Intersection with Intertidal Zone Extent", "Intersection with Exposed Extent", "Intersection with Submerged Extent"]
        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWWWWWWWWWWWW'
        self.width = 'WWWWWWWWWWWWWWWWWWWWWWWWW'
    def onSelChange(self, selection):

        search_distance = 0
        if selection == "Intersection with Exposed Extent":
            arcpy.SelectLayerByLocation_management(selected_lyr, "INTERSECT", "exposed_extent", search_distance, "NEW_SELECTION",
                                                   "NOT_INVERT")

        elif selection == "Intersection with Submerged Extent":
            arcpy.SelectLayerByLocation_management(selected_lyr, "INTERSECT", "submerged_extent", search_distance, "NEW_SELECTION",
                                                   "NOT_INVERT")

        elif selection == "Intersection with Intertidal Zone Extent":
            arcpy.SelectLayerByLocation_management(selected_lyr, "INTERSECT", "intertidal_zone", search_distance, "NEW_SELECTION",
                                                   "NOT_INVERT")

    def onEditChange(self, text):
        pass
    def onFocus(self, focused):
        pass
    def onEnter(self):
        pass
    def refresh(self):
        pass

class ChooseLayer(object):
    """Implementation for BIZIAT_choose_layer.combobox (ComboBox).
    Allows user to select from two layers of data points.
    Layer choice is stored in a global variable to be accessible to other features."""

    def __init__(self):
        self.value = 'known_tracks'
        self.items = ['known_tracks', 'user_tracks']
        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWWWWWWWWWWW'
        self.width = 'WWWWWWWWWWWWWWW'
        self.refresh()



    def onSelChange(self, selection):

        global selected_lyr
        selected_lyr = selection
        self.mxd = arcpy.mapping.MapDocument('current')
        # modify lyrList to exclude NIDEM layers:

        global lyrList
        lyrList = [lyr for lyr in arcpy.mapping.ListLayers(self.mxd, "") if not lyr.name.startswith('NIDEM')]

        for lyr in lyrList:
            arcpy.SelectLayerByAttribute_management(lyr, "CLEAR_SELECTION")

        arcpy.SelectLayerByAttribute_management(selection, "NEW_SELECTION", "")
        arcpy.RefreshActiveView()

    def onFocus(self, focused):

        pass

    # Unused parts:
    def onEditChange(self, text):
        pass
    def onEnter(self):
        pass
    def refresh(self):
        pass

class ChooseField(object):
    """Implementation for BIZIAT_ChooseField.combobox (ComboBox).
    Allows user to choose from a list of fields. Fields are dynamically added from the selected layer.
    Chosen field is stored in a global variable to be accessible to other classes."""
    def __init__(self):

        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWW'
        self.width = 'WWWWWW'
        self.value = "type"
        self.refresh()
        global selected_field
        selected_field = self.value

    def onSelChange(self, selection):
        global selected_field
        selected_field = selection

        # use data access module to get unique values for selected field.
        global valueList
        with arcpy.da.SearchCursor(selected_lyr, selected_field) as cursor:
            valueList = sorted({row[0] for row in cursor})

    def onEditChange(self, text):
        pass
    def onFocus(self, focused):
        fieldList = arcpy.ListFields(selected_lyr)
        fieldnameList = []
        for field in fieldList:
            fieldnameList.append(field.name)

        self.items = fieldnameList
    def onEnter(self):
        pass
    def refresh(self):
        pass

class ChooseValue(object):
    """Implementation for BIZIAT_ChooseValue.combobox (ComboBox).
    Allows user to choose from a list of values for the chosen layer and field.
    In this way, the user can narrow the selection of features on the map.
    Field value list is dynamically generated."""
    def __init__(self):

        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWW'
        self.width = 'WWWWWW'
    def onSelChange(self, selection):

        my_expression = "{0} = '{1}'".format(selected_field, selection)
        arcpy.SelectLayerByAttribute_management(in_layer_or_view=selected_lyr, selection_type="NEW_SELECTION",
                                                where_clause=my_expression)



    def onEditChange(self, text):
        pass
    def onFocus(self, focused):
        # clear any selected features in this layer
        # arcpy.SelectLayerByAttribute_management(in_layer_or_view=selected_lyr, selection_type="CLEAR_SELECTION")

        # # use data access module to get unique values for selected field. MOVED TO ChooseField Class
        # with arcpy.da.SearchCursor(selected_lyr, selected_field) as cursor:
        #     valueList = sorted({row[0] for row in cursor})

        self.items = valueList


    def onEnter(self):
        pass
    def refresh(self):
        pass


class ClearSelection(object):
    """Implementation for BIZIAT_AddIn_addin.clrSelect (Button).
    Clears feature selection on the map."""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        self.mxd = arcpy.mapping.MapDocument('current')
        # create a lyrList that excludes NIDEM layers:
        lyrList = [lyr for lyr in arcpy.mapping.ListLayers(self.mxd, "") if not lyr.name.startswith('NIDEM')]
        for lyr in lyrList:
            arcpy.SelectLayerByAttribute_management(lyr, "CLEAR_SELECTION")

class CreateStudyArea(object):
    """Implementation for BIZIAT_AddIn_addin.crStudyArea (Tool).
    Allows user to draw a rectangular study area on the map. Rectanlge is drawn as an extent object.
    This is then converted to a polygon feature class.
    Please note: The existing survey_area layer is overwritten by this tool."""

    def __init__(self):
        self.enabled = True
        self.cursor = 3
        self.shape = 'Rectangle'


    def onRectangle(self, rectangle_geometry):
        """Occurs when the rectangle is drawn and the mouse button is released.
        The rectangle is a extent object."""

        array = arcpy.Array()
        array.add(rectangle_geometry.upperLeft)
        array.add(rectangle_geometry.upperRight)
        array.add(rectangle_geometry.lowerRight)
        array.add(rectangle_geometry.lowerLeft)
        array.add(rectangle_geometry.upperLeft)

        polygon = arcpy.Polygon(array)
        arcpy.env.overwriteOutput = True  # temporarily allow overwriting of existing datasets, then disallow.
        arcpy.FeatureToPolygon_management(polygon, r"C:\Users\s\Documents\Masters of Geospatial\GISP\Assignment2\GISdata\survey_area.shp")
        arcpy.env.overwriteOutput = False

        WORKSPACE = r"C:\Users\s\Documents\Masters of Geospatial\GISP\Assignment2\GISdata"
        arcpy.env.workspace = WORKSPACE

        # arcpy.env.overwriteOutput = True  # temporarily allow overwriting of existing datasets, then disallow.
        # survey_area = arcpy.management.CreateFeatureclass(WORKSPACE, "survey_area.shp", "POLYGON", spatial_reference=28351)
        # with arcpy.da.InsertCursor(survey_area, ['SHAPE@']) as cursor:
        #     cursor.insertRow(rectangle_geometry.Polygon)
        # arcpy.env.overwriteOutput = False


        # this next code block may be uneccessary
        # mxd = arcpy.mapping.MapDocument("CURRENT")
        # df = arcpy.mapping.ListDataFrames(mxd, "")[0]
        # addLayer = arcpy.mapping.Layer("survey_area.shp")
        # arcpy.mapping.AddLayer(df, addLayer, "BOTTOM")
        # del mxd, addLayer
        #
        # arcpy.RefreshActiveView()

    def onMouseDown(self, x, y, button, shift):
        pass
    def onMouseDownMap(self, x, y, button, shift):
        pass
    def onMouseUp(self, x, y, button, shift):
        pass
    def onMouseUpMap(self, x, y, button, shift):
        pass
    def onMouseMove(self, x, y, button, shift):
        pass
    def onMouseMoveMap(self, x, y, button, shift):
        pass
    def onDblClick(self):
        pass
    def onKeyDown(self, keycode, shift):
        pass
    def onKeyUp(self, keycode, shift):
        pass
    def deactivate(self):
        pass
    def onCircle(self, circle_geometry):
        pass
    def onLine(self, line_geometry):
        pass

class HelpButton(object):
    """Implementation for BIZIAT_AddIn_addin.help (Button).
    Opens help.html in a browser. The file is stored locally in the AddIn install directory.
    Please note that it is referenced absolutely, not relatively, at this stage."""
    def __init__(self):
        self.enabled = True
        self.checked = False

    def onClick(self):
        t = Thread(target=OpenBrowserURL)
        t.start()
        t.join()

class ZoomFull(object):
    """Implementation for BIZIAT_AddIn_addin.ZoomFull (Button).
    Allows user to zoom the map to the full extent of the data."""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        mapdoc = arcpy.mapping.MapDocument('CURRENT')
        df = mapdoc.activeDataFrame
        df_extent = df.extent
        for lyr in arcpy.mapping.ListLayers(mapdoc, data_frame=df):
            extent = lyr.getExtent()
            df_extent.XMin = min(df_extent.XMin, extent.XMin)
            df_extent.XMax = max(df_extent.XMax, extent.XMax)
            df_extent.YMin = min(df_extent.YMin, extent.YMin)
            df_extent.YMax = max(df_extent.YMax, extent.YMax)
        df.extent = df_extent

class ZoomToSelectedFeatures(object):
    """Implementation for BIZIAT_AddIn_addin.zoomSelectBtn (Button).
    Allows the user to zoom the map extent to the extent of the selected features.
    Useful at various stages of selection using the BIZIAT tools."""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        mxd = arcpy.mapping.MapDocument('CURRENT')
        df = arcpy.mapping.ListDataFrames(mxd, "")[0]
        df.zoomToSelectedFeatures()
        arcpy.RefreshActiveView()

class TideHeight(object):
    """Implementation for BIZIAT_TideHeight.combobox (ComboBox).
    Allows user to select from pre-determined tide height values.
    Also allows user to enter their own value. Employs error checking in this process.
    Please note: the is an error in this class definition: The combo box
    is not accepting negative values. A modification must be made to move the error checking actions
    into the 'onEnter' function. This may resolve the issue."""
    def __init__(self):

        self.value = "0"
        self.items = ["-2", "-1", "0", "1", "2"]
        self.editable = True
        self.enabled = True
        self.dropdownWidth = 'WWWWWW'
        self.width = 'WWWWWW'
        self.refresh()

    def onSelChange(self, selection):
        tide_height = selection
        global tide_height
    def onEditChange(self, text):
        try:
            temp_tide_height = float(text)

        except:
            pythonaddins.MessageBox("Tide value must be numeric, between -2.601 and 2.772\n Tide value has been set to 0.", "ERROR IN ENTERED VALUE")

        else:
            if -2.601 <= temp_tide_height <= 2.772:
                tide_height = temp_tide_height
                global tide_height
            else:
                pythonaddins.MessageBox("Tide value must be numeric, between -2.601 and 2.772\n Tide value has been set to 0.", "ERROR IN ENTERED VALUE")

                self.value = "0"
                self.refresh()
                temp_tide_height = 0
                tide_height = temp_tide_height
                global tide_height

    def onFocus(self, focused):
        pass
    def onEnter(self):
        pass
    def refresh(self):
        pass


class CalculateStatistics(object):
    """Implementation for BIZIAT_CalculateStatistics.button (Button).
    Calculates basic statistics for the chosen layer and field.
    Displays results in the Python window of ArcMap.
    Also saves initial results to output_table.csv"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):

        # show progress of statistics calculation:

        with pythonaddins.ProgressDialog() as dialog:
            dialog.title = "Progress Dialog"
            dialog.description = "Calculating Statistics..."
            dialog.animation = "Spiral"
            arcpy.env.overwriteOutput = True    # temporarily allow overwriting of exisitng datasets, then disallow.

            output_table = r"C:\Users\s\Documents\Masters of Geospatial\GISP\Assignment2\GISdata\output_table.csv"
            arcpy.Frequency_analysis(selected_lyr, output_table, [[selected_field]])
            arcpy.env.overwriteOutput = False

            with open (r"C:\Users\s\Documents\Masters of Geospatial\GISP\Assignment2\GISdata\output_table.csv") as csvfile:
                reader = csv.reader(csvfile, delimiter=",")
                next(reader)
                total = 0
                print "Occurrences of each value for the field ({}) are as follows:".format(selected_field)
                for row in reader:
                    total = total + int(row[1])
                    print "The value {0} occurs {1} times".format(row[2], row[1])

                print "Total features are: {}".format(total)

                csvfile.seek(0)
                next(reader)
                for row in reader:
                    value = float(row[1])
                    total = float(total)
                    percentage = value / total * 100
                    print "The value {} is a {:.2f} percentage of the total occurrences".format(row[2], percentage)
