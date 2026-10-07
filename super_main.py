import ezdxf
import math
import pandas as pd
from plotting import *
from shapely.geometry import Point, Polygon, LineString, MultiPoint, MultiPolygon, GeometryCollection, box
from shapely.affinity import scale as affine_scale
from shapely.ops import voronoi_diagram, unary_union, split
from scipy.spatial import Voronoi
import numpy as np
from collections import defaultdict


def truebuffer(StructDataframe):
    StructDataframe["True Struct Buffer Polygon"] = StructDataframe["True Struct Buffer Polygon"].astype(object)
    StructDataframe["Difference Buffer"] = StructDataframe["Difference Buffer"].astype(object)
    for i in range(len(StructDataframe)):
        for j in range(len(StructDataframe)):
            difference = StructDataframe.loc[i, "Struct Buffer Polygon"].difference(StructDataframe.loc[j, "Struct Polygon"])
            if StructDataframe.loc[i, "Struct ID"] != StructDataframe.loc[j, "Struct ID"] and not difference.is_empty:
                StructDataframe.loc[i, "True Struct Buffer Polygon"] = difference
    for i in range(len(StructDataframe)):
            intersection_list = []
            for j in range(len(StructDataframe)):
                intersection = StructDataframe.loc[i, "True Struct Buffer Polygon"].intersection(StructDataframe.loc[j, "True Struct Buffer Polygon"])
                if StructDataframe.loc[i, "Struct ID"] != StructDataframe.loc[j, "Struct ID"] and not intersection.is_empty:
                    intersection_list.append(intersection)
            StructDataframe.loc[i, "Difference Buffer"] = unary_union(intersection_list)
    for i in range(len(StructDataframe)):
        try: StructDataframe.loc[i, "True Struct Buffer Polygon"] = StructDataframe.loc[i, "True Struct Buffer Polygon"].difference(StructDataframe.loc[i, "Difference Buffer"])
        except KeyError: continue
    return StructDataframe


def split_rooms_by_direction(RoomsDataframe):
    newRoomsDataframe = pd.DataFrame(columns = RoomsDataframe.columns)
    for i in range(len(RoomsDataframe)):
        min_x, min_y, max_x, max_y = RoomsDataframe.loc[i, "Room Polygon"].bounds
        if RoomsDataframe.loc[i, "Direction"] == "X":
            cut = (min_x+max_x)/2
            box_0 = box(min_x, min_y, cut, max_y); box_1 = box(cut, min_y, max_x, max_y)
        else:
            cut = (min_y+max_y)/2
            box_0 = box(min_x, min_y, max_x, cut); box_1 = box(min_x, cut, max_x, max_y)
        j = 0
        for b in [box_0, box_1]:
            clipped = RoomsDataframe.loc[i, "Room Polygon"].intersection(b)
            if clipped.is_empty:
                continue
            if clipped.geom_type == "Polygon":
                newRoomsDataframe.loc[len(newRoomsDataframe)] = {"Room ID": str(RoomsDataframe.loc[i, "Room ID"])+str(j),
                                                                "Room Points": clipped.exterior.coords,
                                                                "Room Polygon": Polygon(clipped.exterior.coords),
                                                                "Type": RoomsDataframe.loc[i, "Type"],
                                                                "Direction": RoomsDataframe.loc[i, "Direction"]}
                j += 1
            elif clipped.geom_type == "MultiPolygon":
                for sub in clipped.geoms:
                    if not sub.is_empty:
                        newRoomsDataframe.loc[len(newRoomsDataframe)] = {"Room ID": str(RoomsDataframe.loc[i, "Room ID"])+str(j),
                                                                        "Room Points": sub.exterior.coords,
                                                                        "Room Polygon": Polygon(sub.exterior.coords),
                                                                        "Type": RoomsDataframe.loc[i, "Type"],
                                                                        "Direction": RoomsDataframe.loc[i, "Direction"]}
                j += 1
    return newRoomsDataframe

def anisotropic_cleave(StructDataframe, RoomsDataframe, stretch):
    StructDataframe["Scaled Centroid"] = StructDataframe["Scaled Centroid"].astype(object)
    StructDataframe["Centroid"] = StructDataframe["Centroid"].astype(object)
    for i in range(len(RoomsDataframe)):
        if RoomsDataframe.loc[i, "Direction"] == "X":
            sX, sY = 1.0, stretch  
        else:
            sX, sY = stretch, 1.0
        scaled_boundary = affine_scale(RoomsDataframe.loc[i, "Room Polygon"], xfact=sX, yfact=sY, origin=(0,0))
        points = []
        for element in RoomsDataframe.loc[i, "Associated Structs"]:
            scaled_centroid =  affine_scale(StructDataframe.loc[StructDataframe["Struct ID"] == element, "Centroid"].values[0], xfact=sX, yfact=sY, origin=(0,0))
            StructDataframe.loc[StructDataframe["Struct ID"] == element, "Scaled Centroid"] = scaled_centroid
            points.append(scaled_centroid)
        multipoint = MultiPoint(points)
        regions = voronoi_diagram(multipoint, envelope=scaled_boundary)
        for element in regions.geoms:
            best_element = None
        
        
    return StructDataframe


def create_areas(file_path, buffer, stretch):
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()
    struct_columns = ["Struct ID", "Text", "Struct Points", "Struct Polygon", "Struct Buffer Polygon", "True Struct Buffer Polygon","Difference Buffer","Centroid","Scaled Centroid", "Associated Rooms", "Associated Regions", "Associated Bound"]
    rooms_columns = ["Room ID", "Room Points", "Room Polygon", "Associated Structs","Type", "Direction"]
    bound_columns = ["Bound ID", "Bound Points", "Bound Polygon", "Associated Regions", "Number"]
    StructDataframe = pd.DataFrame(columns = struct_columns)
    RoomsDataframe = pd.DataFrame(columns = rooms_columns)
    BoundDataframe = pd.DataFrame(columns = bound_columns)

    dir_polylines = {}
    mtexts =        {}

    for entity in msp:
        if entity.dxftype() == "LWPOLYLINE":
            points = [(float(p[0]), float(p[1])) for p in entity.get_points()]
            if entity.dxf.layer == "AREE":
                StructDataframe.loc[len(StructDataframe)] = {"Struct ID": entity.dxf.handle,
                                                            "Struct Points": points,
                                                            "Struct Polygon": Polygon(points),
                                                            "Struct Buffer Polygon": Polygon(points).buffer(buffer, join_style="mitre", mitre_limit=100 ),
                                                            "Centroid": Polygon(points).centroid}
            elif entity.dxf.layer == "0":
                BoundDataframe.loc[len(BoundDataframe)] = { "Bound ID": entity.dxf.handle,
                                                            "Bound Points": points,
                                                            "Bound Polygon": Polygon(points)}
            elif entity.dxf.layer == "SCALE":
                RoomsDataframe.loc[len(RoomsDataframe)] = { "Room ID": entity.dxf.handle,
                                                            "Room Points": points,
                                                            "Room Polygon": Polygon(points),
                                                            "Type": "Stairs"}
            elif entity.dxf.layer == "STANZE":
                RoomsDataframe.loc[len(RoomsDataframe)] = { "Room ID": entity.dxf.handle,
                                                            "Room Points": points,
                                                            "Room Polygon": Polygon(points),
                                                            "Type": "Room"}
            elif entity.dxf.layer == "AGGETTI":
                RoomsDataframe.loc[len(RoomsDataframe)] = { "Room ID": entity.dxf.handle,
                                                            "Room Points": points,
                                                            "Room Polygon": Polygon(points),
                                                            "Type": "Other"}
            elif entity.dxf.layer == "ORDITURA":
                dir_polylines[entity.dxf.handle] = {"points": points,
                                                    "polygon": LineString(points),
                                                    "closed": entity.closed}
        
        elif entity.dxftype() == "MTEXT" and entity.dxf.layer == "AREE":
            point = (float(entity.dxf.insert[0]), float(entity.dxf.insert[1]))
            mtexts[entity.dxf.handle] = {"text": entity.plain_text(),
                                        "point": Point(point),
                                        "insert": point}

    # Orditura dentro la stanza
    RoomsDataframe["Direction"] = RoomsDataframe["Direction"].astype(object)
    for i in range(len(RoomsDataframe)):
        for key, value in dir_polylines.items():
            if len(value["points"]) > 2: raise ValueError("Numero di punti maggiore di due")
            x0, y0 = value["points"][0]; x1, y1 = value["points"][1]
            direction = "Y" if abs(y1-y0) > abs(x1-x0) else "X"
            if RoomsDataframe["Room Polygon"].iloc[i].contains(value["polygon"]):
               RoomsDataframe.loc[i, "Direction"] = direction 

    # Testo dentro gli elementi strutturali
    StructDataframe["Text"] = StructDataframe["Text"].astype(object) 
    for i in range(len(StructDataframe)):
        for key, value in mtexts.items():
            if StructDataframe.loc[i, "Struct Polygon"].contains(value["point"]):
                StructDataframe.loc[i, "Text"] = value["text"]
    
    StructDataframe = truebuffer(StructDataframe)
    RoomsDataframe = split_rooms_by_direction(RoomsDataframe)

    # Elementi strutturali che intersecano le stanze
    RoomsDataframe["Associated Structs"] = RoomsDataframe["Associated Structs"].apply(lambda _: [])
    StructDataframe["Associated Rooms"] = StructDataframe["Associated Rooms"].apply(lambda _: [])
    for i in range(len(RoomsDataframe)):
        for j in range(len(StructDataframe)):
            if RoomsDataframe.loc[i, "Room Polygon"].intersects(StructDataframe.loc[j, "Struct Polygon"]):
                RoomsDataframe.loc[i, "Associated Structs"].append(StructDataframe.loc[j, "Struct ID"])
                StructDataframe.loc[j, "Associated Rooms"].append(RoomsDataframe.loc[i, "Room ID"])

    
    Stuff = anisotropic_cleave(StructDataframe, RoomsDataframe, stretch)






    
    return StructDataframe
    
if __name__ == "__main__":
    buffer = 30
    stretch = 2.5
    df = create_areas("Disegno1.dxf", buffer, stretch)
    