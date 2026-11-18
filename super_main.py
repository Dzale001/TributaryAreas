
import ezdxf
import math
import pandas as pd
#from plotting import *
from shapely.geometry import Point, Polygon, LineString, MultiPoint, MultiPolygon, GeometryCollection, box
from shapely.affinity import scale as affine_scale
from shapely.ops import voronoi_diagram, unary_union, split

import numpy as np
from collections import defaultdict

def prune_disconnected_regions(StructDataframe, tol=1e-6, min_shared=1e-3):
    """
    Per ogni elemento strutturale tiene solo i pezzi di regione collegati,
    direttamente o tramite altri pezzi, all'elemento stesso.
    Tutto ciò che resta isolato viene eliminato.
    """
    orphans = []
    for i in StructDataframe.index:
        regions = StructDataframe.at[i, "True Regions"]
        if not regions:
            continue
        struct_polygon = StructDataframe.at[i, "Struct Polygon"]
        bound_id = StructDataframe.at[i, "Associated Bound"]

        parts = []
        for room_id, geom in regions.items():
            geom = _polygonal_part(geom)
            if geom.is_empty:
                continue
            subs = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
            parts.extend((room_id, p) for p in subs if not p.is_empty)

        kept = {k for k, (_, p) in enumerate(parts) if p.distance(struct_polygon) <= tol}
        frontier = list(kept)
        while frontier:
            cur = frontier.pop()
            for k, (_, p) in enumerate(parts):
                if k not in kept and p.distance(parts[cur][1]) <= tol:
                    kept.add(k)
                    frontier.append(k)

        new_regions = defaultdict(list)
        for k, (room_id, p) in enumerate(parts):
            if k in kept:
                new_regions[room_id].append(p)
            else:
                orphans.append((room_id, p, bound_id, i))

        StructDataframe.at[i, "True Regions"] = {rid: unary_union(ps) for rid, ps in new_regions.items()}
        StructDataframe.at[i, "Associated Rooms"] = [k for k in new_regions if k != "Extra"]

        def shared_length(a, b):
            return b.boundary.intersection(a.buffer(tol)).length

        pending = list(orphans)
        while pending:
            assigned_now = []
            for item in pending:
                room_id, poly, bound_id, origin = item
                best_i, best_len, best_same_room = None, min_shared, False

                for j in StructDataframe.index:
                    if j == origin or StructDataframe.at[j, "Associated Bound"] != bound_id:
                        continue
                    for rid, geom in StructDataframe.at[j, "True Regions"].items():
                        L = shared_length(poly, geom)
                        if L <= min_shared:
                            continue
                        same_room = (rid == room_id)
                        # preferisco regioni della stessa stanza, poi il bordo più lungo
                        if (same_room, L) > (best_same_room, best_len) or best_i is None:
                            best_i, best_len, best_same_room = j, L, same_room

                if best_i is not None:
                    regions = StructDataframe.at[best_i, "True Regions"]
                    regions[room_id] = unary_union([regions[room_id], poly]) if room_id in regions else poly
                    StructDataframe.at[best_i, "Associated Rooms"] = [k for k in regions if k != "Extra"]
                    assigned_now.append(item)

            if not assigned_now:
                break
            pending = [o for o in pending if o not in assigned_now]

        # ultimo fallback: pezzi che non toccano nessuno -> struttura più vicina nello stesso piano
        for room_id, poly, bound_id, origin in pending:
            cands = [j for j in StructDataframe.index
                    if j != origin and StructDataframe.at[j, "Associated Bound"] == bound_id]
            if not cands:
                continue
            j = min(cands, key=lambda j: poly.distance(StructDataframe.at[j, "Struct Polygon"]))
            regions = StructDataframe.at[j, "True Regions"]
            regions["Extra"] = unary_union([regions["Extra"], poly]) if "Extra" in regions else poly
            print(f"Pezzo isolato (area {poly.area:.1f}) assegnato per vicinanza alla struttura {StructDataframe.at[j, 'Struct ID']}")


    return StructDataframe

def clean_polygon(StructDataframe, toll):
    for i in range(len(StructDataframe)):
        polygon_to_clean = StructDataframe.loc[i, "True Regions"]
        coords = list(polygon_to_clean.exterior.coords)
        for item in coords:
            pass
    return StructDataframe

def truebuffer(StructDataframe):
    StructDataframe["True Struct Buffer Polygon"] = StructDataframe["True Struct Buffer Polygon"].astype(object)
    StructDataframe["Difference Buffer"] = StructDataframe["Difference Buffer"].astype(object)
    
    n = len(StructDataframe)
    
    # 1. Sottrai gli altri elementi strutturali dal buffer di ciascuna struttura
    for i in range(n):
        current_id = StructDataframe.loc[i, "Struct ID"]
        base_buffer = StructDataframe.loc[i, "Struct Buffer Polygon"]
        if base_buffer is None or base_buffer.is_empty:
            continue
            
        other_polys = [
            StructDataframe.loc[j, "Struct Polygon"]
            for j in range(n)
            if StructDataframe.loc[j, "Struct ID"] != current_id and not StructDataframe.loc[j, "Struct Polygon"].is_empty
        ]
        
        if other_polys:
            other_union = unary_union(other_polys)
            res = base_buffer.difference(other_union)
        else:
            res = base_buffer
            
        # Pulisci la geometria risultante
        if not res.is_empty:
            res = res.buffer(0) 
        StructDataframe.loc[i, "True Struct Buffer Polygon"] = res

    # 2. Calcola le intersezioni tra i buffer veri risultanti
    for i in range(n):
        current_id = StructDataframe.loc[i, "Struct ID"]
        curr_buffer = StructDataframe.loc[i, "True Struct Buffer Polygon"]
        
        if curr_buffer is None or curr_buffer.is_empty:
            StructDataframe.loc[i, "Difference Buffer"] = Polygon()
            continue
            
        intersection_list = []
        for j in range(n):
            if StructDataframe.loc[j, "Struct ID"] != current_id:
                other_buffer = StructDataframe.loc[j, "True Struct Buffer Polygon"]
                if other_buffer is not None and not other_buffer.is_empty:
                    inter = curr_buffer.intersection(other_buffer)
                    if not inter.is_empty:
                        intersection_list.append(inter)
                        
        if intersection_list:
            diff_union = unary_union(intersection_list).buffer(0)
            StructDataframe.loc[i, "Difference Buffer"] = diff_union
        else:
            StructDataframe.loc[i, "Difference Buffer"] = Polygon()

    # 3. Sottrai le sovrapposizioni dai buffer
    for i in range(n):
        try:
            buf = StructDataframe.loc[i, "True Struct Buffer Polygon"]
            diff = StructDataframe.loc[i, "Difference Buffer"]
            if buf is not None and not buf.is_empty and diff is not None and not diff.is_empty:
                cleaned = buf.difference(diff).buffer(0)
                StructDataframe.loc[i, "True Struct Buffer Polygon"] = cleaned
        except KeyError:
            continue
            
    return StructDataframe

def compute_lengths(StructDataframe):
    """Lunghezza = lato maggiore del rettangolo minimo ruotato che racchiude l'elemento
    (coincide con la dimensione maggiore del bounding box se l'elemento è ortogonale agli assi)."""
    lengths = []
    for poly in StructDataframe["Struct Polygon"]:
        rect = poly.minimum_rotated_rectangle
        if rect.geom_type == "Polygon":
            c = list(rect.exterior.coords)
            lengths.append(max(math.dist(c[k], c[k + 1]) for k in range(4)))
        else:  # geometria degenere
            minx, miny, maxx, maxy = poly.bounds
            lengths.append(max(maxx - minx, maxy - miny))
    StructDataframe["Length"] = lengths
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
                        j += 1          # <-- dentro il for
    return newRoomsDataframe

def _polygonal_part(geom):
    """Tiene solo la parte poligonale: scarta LineString/Point residui."""
    if geom is None or geom.is_empty:
        return Polygon()
    if geom.geom_type in ("Polygon", "MultiPolygon"):
        return geom
    if geom.geom_type == "GeometryCollection":
        polys = [g for g in geom.geoms if g.geom_type in ("Polygon", "MultiPolygon")]
        return unary_union(polys) if polys else Polygon()
    return Polygon()


def _finalize_region(geom, bound_polygon):
    geom = _polygonal_part(geom)
    if geom.geom_type == "MultiPolygon":
        geom = unary_union(geom.buffer(1E-6)).buffer(-1E-6)
    return _polygonal_part(geom.intersection(bound_polygon))


def anisotropic_cleave(StructDataframe, RoomsDataframe, BoundDataframe, stretch):
    StructDataframe["Scaled Centroid"] = StructDataframe["Scaled Centroid"].astype(object)
    StructDataframe["Centroid"] = StructDataframe["Centroid"].astype(object)
    StructDataframe["Associated Regions"] = StructDataframe["Associated Regions"].astype(object)
    StructDataframe["Associated Regions"] = StructDataframe["Associated Regions"].apply(lambda _: {})   # {Room ID: [celle]}
    StructDataframe["True Regions"] = StructDataframe["True Regions"].astype(object)
    StructDataframe["Associated Rooms"] = StructDataframe["Associated Rooms"].astype(object)

    for i in range(len(RoomsDataframe)):
        room_id = RoomsDataframe.loc[i, "Room ID"]
        if RoomsDataframe.loc[i, "Direction"] == "X":
            sX, sY = 1.0, stretch
        else:
            sX, sY = stretch, 1.0
        scaled_boundary = affine_scale(RoomsDataframe.loc[i, "Room Polygon"], xfact=sX, yfact=sY, origin=(0, 0))
        points = []
        for element in RoomsDataframe.loc[i, "Associated Structs"]:
            scaled_centroid = affine_scale(StructDataframe.loc[StructDataframe["Struct ID"] == element, "Centroid"].values[0], xfact=sX, yfact=sY, origin=(0, 0))
            StructDataframe.loc[StructDataframe["Struct ID"] == element, "Scaled Centroid"] = scaled_centroid
            points.append(scaled_centroid)
        multipoint = MultiPoint(points)
        regions = voronoi_diagram(multipoint, envelope=scaled_boundary)

        for cell in regions.geoms:
            best_element = None
            best_dist = float("inf")
            for element in RoomsDataframe.loc[i, "Associated Structs"]:
                d = cell.distance(StructDataframe.loc[StructDataframe["Struct ID"] == element, "Scaled Centroid"].values[0])
                if d < best_dist:
                    best_dist = d
                    best_element = element

            if best_element is None:
                continue
            real_cell = affine_scale(cell, xfact=1/sX, yfact=1/sY, origin=(0, 0))
            real_clipped_cell = _polygonal_part(real_cell.intersection(RoomsDataframe.loc[i, "Room Polygon"]))
            if real_clipped_cell.is_empty:
                continue

            if real_clipped_cell.is_empty:
                continue

            # le celle restano raggruppate per stanza/scala/aggetto di provenienza
            regions_dict = StructDataframe.loc[StructDataframe["Struct ID"] == best_element, "Associated Regions"].values[0]
            regions_dict.setdefault(room_id, []).append(real_clipped_cell)

    all_buffer = unary_union(list(StructDataframe["True Struct Buffer Polygon"]))

    for i in range(len(StructDataframe)):
        struct_polygon = StructDataframe.loc[i, "Struct Polygon"]
        true_buffer = StructDataframe.loc[i, "True Struct Buffer Polygon"]
        other_buffer = all_buffer.difference(true_buffer)
        base = unary_union([struct_polygon, true_buffer])      # elemento + suo buffer

        associated_bound_polygon = BoundDataframe.loc[
            BoundDataframe["Bound ID"] == StructDataframe.loc[i, "Associated Bound"], "Bound Polygon"].values[0]

        true_regions = {}
        covered_rooms = []
        for room_id, cells in StructDataframe.loc[i, "Associated Regions"].items():
            room_polygon = RoomsDataframe.loc[RoomsDataframe["Room ID"] == room_id, "Room Polygon"].values[0]
            # celle Voronoi + la parte di elemento/buffer che cade in questa stanza
            piece = unary_union(cells + [base.intersection(room_polygon)])
            piece = _finalize_region(piece.difference(other_buffer), associated_bound_polygon)
            if piece.is_empty:
                continue
            true_regions[room_id] = piece
            covered_rooms.append(room_polygon)

        # parte di elemento/buffer che non cade in nessuna delle stanze associate
        leftover = base.difference(unary_union(covered_rooms)).difference(other_buffer)
        leftover = _finalize_region(leftover, associated_bound_polygon)
        if not leftover.is_empty:
            true_regions["Extra"] = leftover

        StructDataframe.at[i, "True Regions"] = true_regions                       # {ID regione: Polygon}
        StructDataframe.at[i, "Associated Rooms"] = [k for k in true_regions if k != "Extra"]

    return StructDataframe


def create_areas(file_path, buffer, stretch):
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()
    struct_columns = ["Struct ID", "Text", "Struct Points", "Struct Polygon", "Struct Buffer Polygon", "True Struct Buffer Polygon","Difference Buffer","Centroid","Scaled Centroid", "Associated Rooms", "Associated Regions","True Regions", "Associated Bound"]
    rooms_columns = ["Room ID", "Room Points", "Room Polygon", "Associated Structs","Type", "Direction"]
    bound_columns = ["Bound ID", "Bound Points", "Bound Polygon", "Associated Structs", "Associated Regions", "Number"]
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
            elif entity.dxf.layer == "BOUND":
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

    # Elementi strutturali per piano
    StructDataframe["Associated Bound"] = StructDataframe["Associated Bound"].astype(object)
    BoundDataframe["Associated Structs"] = BoundDataframe["Associated Structs"].apply(lambda _: [])
    BoundDataframe["Associated Structs"] = BoundDataframe["Associated Structs"].astype(object)
    for i in range(len(StructDataframe)):
        for j in range(len(BoundDataframe)):
            if BoundDataframe.loc[j, "Bound Polygon"].contains(StructDataframe.loc[i, "Struct Polygon"]):
                StructDataframe.loc[i, "Associated Bound"] = BoundDataframe.loc[j, "Bound ID"]
                BoundDataframe.loc[j, "Associated Structs"].append(StructDataframe.loc[i, "Struct ID"])
    
    StructDataframe = anisotropic_cleave(StructDataframe, RoomsDataframe, BoundDataframe, stretch)
    StructDataframe = prune_disconnected_regions(StructDataframe, tol=0.0001)
    StructDataframe = compute_lengths(StructDataframe)
    # serve al viewer per sapere se ogni regione è stanza, scala o aggetto
    StructDataframe.attrs["room_types"] = dict(zip(RoomsDataframe["Room ID"], RoomsDataframe["Type"]))
    return StructDataframe
    
if __name__ == "__main__":
    buffer = 30
    stretch = 25
    df = create_areas("Disegno1.dxf", buffer, stretch)
