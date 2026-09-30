from shapely.geometry import Polygon, LineString, MultiPoint, MultiPolygon, GeometryCollection, box
from shapely.affinity import scale as affine_scale
from shapely.ops import voronoi_diagram, unary_union, split
from scipy.spatial import Voronoi
import numpy as np

"""
def slash(data, bound_polylines, struct_polylines):
    voronoi_areas = {}
    for boundary, elements in data.items():
        boundary_polygon = Polygon(bound_polylines[boundary]["points"])
        centroids = {}
        for element, value in elements.items():
            poly = Polygon(struct_polylines[element]["points"])
            centroids[element] = poly.centroid
        points = list(centroids.values())
        multipoint = MultiPoint(points)
        regions = voronoi_diagram(multipoint, envelope=boundary_polygon)
        
        for cell in regions.geoms:
            clipped = cell.intersection(boundary_polygon)
            for h, p in centroids.items():
                if clipped.contains(p):
                    voronoi_areas[h] = {"area":clipped.area, "geometry":list(clipped.exterior.coords)}
                    break
    return voronoi_areas

def multis_slash(total_rooms_polylines, total_rooms_data, struct_polylines):
    voronoi_areas = {}
    for boundary, _ in total_rooms_polylines.items():
        boundary_polygon = Polygon(total_rooms_polylines[boundary]["points"])
        centroids = {}
        for element in total_rooms_data[boundary]["intersecano"]:
            poly = Polygon(struct_polylines[element]["points"])
            centroids[element] = poly.centroid
        points = list(centroids.values())
        multipoint = MultiPoint(points)
        regions = voronoi_diagram(multipoint, envelope=boundary_polygon)
        
    return voronoi_areas


"""

def multi_slash(total_rooms_polylines, total_rooms_data, struct_polylines):
    voronoi_areas = {}

    for boundary in total_rooms_polylines:
        
        boundary_polygon = Polygon(total_rooms_polylines[boundary]["points"])

        centroids = {}
        for element in total_rooms_data[boundary]["intersecano"]:
            poly = Polygon(struct_polylines[element]["points"])
            centroids[element] = poly.centroid

        cell_by_element = {}

        if len(centroids) == 0:
            # nessun elemento strutturale associato a questo ambiente
            voronoi_areas[boundary] = {}
            continue

        if len(centroids) == 1:
            # con un solo punto il diagramma di Voronoi degenera:
            # l'intera area di boundary appartiene a quell'unico elemento
            only_element = next(iter(centroids))
            cell_by_element[only_element] = boundary_polygon
            voronoi_areas[boundary] = cell_by_element
            continue

        points = list(centroids.values())
        multipoint = MultiPoint(points)
        regions = voronoi_diagram(multipoint, envelope=boundary_polygon)

        
        for cell in regions.geoms:
            best_element = None
            best_dist = float("inf")
            for element, centroid in centroids.items():
                d = cell.distance(centroid)
                if d < best_dist:
                    best_dist = d
                    best_element = element
            
            if best_element is None:
                print("here")
                continue

            # Ora clippiamo sulla forma reale del boundary
            clipped_cell = cell.intersection(boundary_polygon)
            
            if clipped_cell.is_empty:
                continue

            # Se più celle risultassero (raro, per boundary non convessi che
            # spezzano una cella in più pezzi), uniamo tutto sotto lo stesso elemento

            """
            if best_element in cell_by_element:
                            print("ok")
                            cell_by_element[best_element] = cell_by_element[best_element].union(clipped_cell)
                        else:
                            print("not ok")
                            cell_by_element[best_element] = clipped_cell
            """
            
            #cell_by_element[best_element] = unary_union([Polygon(struct_polylines[best_element]["points"]),clipped_cell])
            cell_by_element[best_element] = clipped_cell
        

        voronoi_areas[boundary] = cell_by_element
    return voronoi_areas

def flatten_single_level(geom_dict):
    """
    Converte {element: shapely_geometry} in {handle: {"geometry": [(x,y), ...]}}
    per il plotting. Versione ad un solo livello (post-merge).
    """
    flat = {}
    for element, geom in geom_dict.items():
        if geom is None or geom.is_empty:
            continue

        if isinstance(geom, Polygon):
            coords = list(geom.exterior.coords)
            flat[element] = {"geometry": coords}

        elif isinstance(geom, MultiPolygon):
            for i, part in enumerate(geom.geoms):
                if part.is_empty:
                    continue
                coords = list(part.exterior.coords)
                flat[f"{element}_{i}"] = {"geometry": coords}

        elif isinstance(geom, GeometryCollection):
            i = 0
            for part in geom.geoms:
                if isinstance(part, Polygon) and not part.is_empty:
                    coords = list(part.exterior.coords)
                    flat[f"{element}_{i}"] = {"geometry": coords}
                    i += 1
        # altri tipi (LineString, Point residui) vengono scartati

    return flat

def flatten_voronoi(voronoi_areas):

    """
    Converte {boundary: {element: shapely_geometry}} 
    in {handle_univoco: {"geometry": [(x, y), ...]}} per il plotting.
    Gestisce Polygon, MultiPolygon e geometrie degeneri/vuote.
    """
    flat = {}
    for boundary, cell_by_element in voronoi_areas.items():
        for element, geom in cell_by_element.items():
            if geom is None or geom.is_empty:
                continue

            handle = f"{boundary}_{element}"

            if isinstance(geom, Polygon):
                coords = list(geom.exterior.coords)
                flat[handle] = {"geometry": coords}

            elif isinstance(geom, MultiPolygon):
                # una cella spezzata in più pezzi: la plottiamo come sotto-pezzi separati
                for i, part in enumerate(geom.geoms):
                    if part.is_empty:
                        continue
                    coords = list(part.exterior.coords)
                    flat[f"{handle}_{i}"] = {"geometry": coords}

            elif isinstance(geom, GeometryCollection):
                # può contenere frammenti di tipo diverso (linee, punti) oltre ai poligoni:
                # teniamo solo le componenti poligonali
                i = 0
                for part in geom.geoms:
                    if isinstance(part, Polygon) and not part.is_empty:
                        coords = list(part.exterior.coords)
                        flat[f"{handle}_{i}"] = {"geometry": coords}
                        i += 1
            # altri tipi (es. LineString, Point residui da intersezioni al limite) vengono scartati

    return flat

def to_polygon(stuff):
    return Polygon(stuff).buffer(10)

def unionized(stuff):
    return unary_union(stuff)

def fusion(value):
    if type(value) == MultiPolygon:
        value = unary_union(list(value.geoms))
        inflated = value.buffer(1E-6)
        inflated = unary_union(inflated)
        value = inflated.buffer(-1E-6)
    return value

def point_in_polygon(s_value, t_value):
    x, y = t_value[0], t_value[1]
    inside = False
    n = len(s_value)
    for i in range(n):
        x1, y1 = s_value[i]
        x2, y2 = s_value[(i+1) % n]
        if  ((y1 > y) != (y2 > y)):
            x_intersects = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < x_intersects:
                inside = not inside
    x1, y1 = x2, y2
    return inside

def polygon_in_polygon(b_value, s_value):
    inside = True
    for point in s_value:
        if not point_in_polygon(b_value, point):
           inside = False
    return inside

def segments_intersect(p1, p2, p3, p4):
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    d1 = cross(p3, p4, p1)
    d2 = cross(p3, p4, p2)
    d3 = cross(p1, p2, p3)
    d4 = cross(p1, p2, p4)

    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
       ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True

    def on_segment(p, q, r):
        return (min(p[0], r[0]) <= q[0] <= max(p[0], r[0]) and
                min(p[1], r[1]) <= q[1] <= max(p[1], r[1]))

    if d1 == 0 and on_segment(p3, p1, p4): return True
    if d2 == 0 and on_segment(p3, p2, p4): return True
    if d3 == 0 and on_segment(p1, p3, p2): return True
    if d4 == 0 and on_segment(p1, p4, p2): return True
    return False

def polygons_intersect(b_value, s_value):
    for point in s_value:
        if point_in_polygon(b_value, point):
            return True

    for point in b_value:
        if point_in_polygon(s_value, point):
            return True

    nb = len(b_value)
    ns = len(s_value)
    for i in range(nb):
        b1 = b_value[i]
        b2 = b_value[(i + 1) % nb]
        for j in range(ns):
            s1 = s_value[j]
            s2 = s_value[(j + 1) % ns]
            if segments_intersect(b1, b2, s1, s2):
                return True

    return False

def more_xy(points):
    # Valuta se un elemento è prevalente in direzione x o in direzione y
    if len(points) > 2:
        raise ValueError("Numero di punti maggiore di 2")
    n = len(points)
    x1, y1 = points[0]
    x2, y2 = points[1]
    if abs(y2 - y1) > abs(x2 - x1):
        return "Y"
    return "X"

def split_polygon_by_direction(points, direction):
    """
    direction: "X" -> taglio verticale (separa sinistra/destra)
               "Y" -> taglio orizzontale (separa sopra/sotto)
    Ritorna una lista di liste di punti [(x,y), ...], una per ciascuna metà.
    Se una metà risulta spezzata in più pezzi (poligono concavo), 
    ogni pezzo viene incluso separatamente.
    """
    poly = Polygon(points)
    minx, miny, maxx, maxy = poly.bounds

    if direction == "X":
        cut = (minx + maxx) / 2
        box1 = box(minx, miny, cut, maxy)
        box2 = box(cut, miny, maxx, maxy)
    elif direction == "Y":
        cut = (miny + maxy) / 2
        box1 = box(minx, miny, maxx, cut)
        box2 = box(minx, cut, maxx, maxy)
    else:
        raise ValueError(f"Direzione non valida: {direction}")

    parts = []
    for b in (box1, box2):
        clipped = poly.intersection(b)
        if clipped.is_empty:
            continue
        if clipped.geom_type == "Polygon":
            parts.append(list(clipped.exterior.coords))
        elif clipped.geom_type == "MultiPolygon":
            for sub in clipped.geoms:
                if not sub.is_empty:
                    parts.append(list(sub.exterior.coords))

    return parts

def generate_weighted_cluster(centroid, weight, n_points=24):
    """
    Genera n_points disposti in cerchio attorno al centroide,
    con raggio = weight. Più il weight è grande, più il cluster
    'spinge' la cella Voronoi risultante verso l'esterno.
    """
    angles = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
    return [
        (centroid.x + weight * np.cos(a), centroid.y + weight * np.sin(a))
        for a in angles
    ]

def voronoi_finite_polygons_2d(vor, radius=None):
    if vor.points.shape[1] != 2:
        raise ValueError("Richiede punti 2D")

    new_regions = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)
    if radius is None:
        radius = np.ptp(vor.points, axis=0).max() * 10  # <-- corretto

    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    for p1, region_index in enumerate(vor.point_region):
        vertices = vor.regions[region_index]

        if all(v >= 0 for v in vertices):
            new_regions.append(vertices)
            continue

        ridges = all_ridges[p1]
        new_region = [v for v in vertices if v >= 0]

        for p2, v1, v2 in ridges:
            if v2 < 0:
                v1, v2 = v2, v1
            if v1 >= 0:
                continue

            t = vor.points[p2] - vor.points[p1]
            t = t / np.linalg.norm(t)
            n = np.array([-t[1], t[0]])

            midpoint = (vor.points[p1] + vor.points[p2]) / 2
            direction = np.sign(np.dot(midpoint - center, n)) * n
            far_point = vor.vertices[v2] + direction * radius

            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())

        vs = np.asarray([new_vertices[v] for v in new_region])
        c = vs.mean(axis=0)
        angles = np.arctan2(vs[:, 1] - c[1], vs[:, 0] - c[0])
        new_region = np.array(new_region)[np.argsort(angles)].tolist()

        new_regions.append(new_region)

    return new_regions, np.asarray(new_vertices)

def split_rooms_by_orditura(total_rooms_polylines, total_rooms_data, struct_polylines):

    """
    Per ogni stanza, la divide in 2 (o più, se concava) sotto-poligoni
    secondo la direzione di orditura, e ricostruisce da zero
    i dizionari total_rooms_polylines / total_rooms_data con nuove chiavi uniche.
    """
    new_polylines = {}
    new_data = {}

    for room_key, room_info in total_rooms_polylines.items():
        room_meta = total_rooms_data[room_key]
        direction = room_meta.get("orditura")
        points = room_info["points"]

        split_parts = split_polygon_by_direction(points, direction)

        # se lo split fallisce o produce un solo pezzo, teniamo la stanza originale
        if len(split_parts) <= 1:
            new_polylines[room_key] = room_info
            new_data[room_key] = room_meta
            continue

        for i, part_points in enumerate(split_parts):
            new_key = f"{room_key}_{i}"

            new_polylines[new_key] = {
                "points": part_points,
                "closed": True
            }

            # ricalcoliamo 'intersecano' SOLO sulla nuova geometria più piccola,
            # non possiamo riusare quello della stanza originale
            part_contains = []
            for s_key, s_values in struct_polylines.items():
                if polygons_intersect(part_points, s_values["points"]):
                    part_contains.append(s_key)

            new_data[new_key] = {
                "intersecano": part_contains,
                "orditura": direction,
                "tipo": room_meta["tipo"]
            }

    return new_polylines, new_data

def multi_slash_anisotropic(total_rooms_polylines, total_rooms_data, struct_polylines, stretch_factor=3.0):
    voronoi_areas = {}

    for boundary in total_rooms_polylines:
        boundary_polygon = Polygon(total_rooms_polylines[boundary]["points"])
        orditura = total_rooms_data[boundary].get("orditura")

        # Comprimiamo l'asse PERPENDICOLARE alla direzione di orditura
        if orditura == "X":
            sx, sy = 1.0, stretch_factor   # celle corte in Y, lunghe in X
        elif orditura == "Y":
            sx, sy = stretch_factor, 1.0   # celle corte in X, lunghe in Y
        else:
            sx, sy = 1.0, 1.0              # nessuna anisotropia se orditura non nota

        centroids = {}
        for element in total_rooms_data[boundary]["intersecano"]:
            poly = Polygon(struct_polylines[element]["points"])
            centroids[element] = poly.centroid

        cell_by_element = {}

        if len(centroids) == 0:
            voronoi_areas[boundary] = {}
            continue

        if len(centroids) == 1:
            only_element = next(iter(centroids))
            cell_by_element[only_element] = boundary_polygon
            voronoi_areas[boundary] = cell_by_element
            continue

        # --- passiamo allo spazio "stirato" ---
        scaled_boundary = affine_scale(boundary_polygon, xfact=sx, yfact=sy, origin=(0, 0))
        scaled_centroids = {
            element: affine_scale(centroid, xfact=sx, yfact=sy, origin=(0, 0))
            for element, centroid in centroids.items()
        }

        points = list(scaled_centroids.values())
        multipoint = MultiPoint(points)
        regions = voronoi_diagram(multipoint, envelope=scaled_boundary)

        for cell in regions.geoms:
            # matching per distanza minima, fatto nello spazio stirato
            # (coerente: sia cell che centroidi sono nello stesso spazio)
            best_element = None
            best_dist = float("inf")
            for element, centroid in scaled_centroids.items():
                d = cell.distance(centroid)
                if d < best_dist:
                    best_dist = d
                    best_element = element

            if best_element is None:
                continue

            # --- torniamo allo spazio reale PRIMA di clippare sul boundary vero ---
            real_cell = affine_scale(cell, xfact=1/sx, yfact=1/sy, origin=(0, 0))
            clipped_cell = real_cell.intersection(boundary_polygon)

            if clipped_cell.is_empty:
                continue

            cell_by_element[best_element] = clipped_cell

            

        voronoi_areas[boundary] = cell_by_element

    return voronoi_areas

def multi_slash_weighted(total_rooms_polylines, total_rooms_data, struct_polylines,
                         
                          weight_scale=0.5, n_points=24):
    """
    weight_scale: fattore che converte l'area dell'elemento in un raggio
                  di 'spinta' del cluster. Da tarare visivamente.
    """
    voronoi_areas = {}

    for boundary in total_rooms_polylines:
        boundary_polygon = Polygon(total_rooms_polylines[boundary]["points"])
        elements = total_rooms_data[boundary]["intersecano"]

        if len(elements) == 0:
            voronoi_areas[boundary] = {}
            continue

        # calcoliamo centroide + area per ciascun elemento
        info = {}
        for element in elements:
            poly = Polygon(struct_polylines[element]["points"])
            info[element] = {"centroid": poly.centroid, "area": poly.area}

        if len(elements) == 1:
            only_element = elements[0]
            voronoi_areas[boundary] = {only_element: boundary_polygon}
            continue

        # peso = radice quadrata dell'area (l'area cresce col quadrato del raggio,
        # quindi sqrt la riporta a una scala "lineare" più intuitiva da tarare)
        all_points = []
        point_owner = []
        for element, d in info.items():
            weight = weight_scale * np.sqrt(d["area"])
            cluster = generate_weighted_cluster(d["centroid"], weight, n_points=n_points)
            for p in cluster:
                all_points.append(p)
                point_owner.append(element)

        points_arr = np.array(all_points)
        points_arr += np.random.normal(0, 1e-9, points_arr.shape)  # evita duplicati esatti

        vor = Voronoi(points_arr)
        regions, vertices = voronoi_finite_polygons_2d(vor)  # funzione già scritta in precedenza

        cell_by_element = {}
        for i, owner in enumerate(point_owner):
            region = regions[i]
            cell = Polygon(vertices[region])
            clipped = cell.intersection(boundary_polygon)
            if clipped.is_empty:
                continue
            if owner in cell_by_element:
                cell_by_element[owner] = unary_union([cell_by_element[owner], clipped])
            else:
                cell_by_element[owner] = clipped

        voronoi_areas[boundary] = cell_by_element

    return voronoi_areas

