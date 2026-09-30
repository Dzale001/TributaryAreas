import ezdxf
import math
import json
import pandas as pd
import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

doc = ezdxf.readfile("Disegno1.dxf")
msp = doc.modelspace()

data = {}
polylines = {}
mtexts = {}

# ============================================================================
# FUNZIONI PER LA GESTIONE DEI POLIGONI
# ============================================================================

def polygon_sides(points):
    n = len(points)
    sides = []
    for i in range(n):
        p1 = points[i]
        p2 = points[(i + 1) % n]
        length = math.dist(p1, p2)
        sides.append({"start": p1, "end": p2, "length": length})
    return sides

def polygon_area(points):
    n = len(points)
    area = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0

def point_in_polygon(point, polygon):
    x, y = point
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

# ============================================================================
# FUNZIONI PER IL VORONOI
# ============================================================================

def compute_centroid(points):
    """Baricentro corretto di un poligono (pesato per area)"""
    n = len(points)
    A = 0.0
    Cx = 0.0
    Cy = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        cross = x1 * y2 - x2 * y1
        A += cross
        Cx += (x1 + x2) * cross
        Cy += (y1 + y2) * cross
    A *= 0.5
    Cx /= (6 * A)
    Cy /= (6 * A)
    return (Cx, Cy)

def classify_and_sample(points, sides, aspect_ratio_threshold=2.0, sample_spacing=300.0):
    """
    Classifica elemento: pilastro (compatto) vs muro (allungato)
    e campiona punti lungo l'asse principale se è un muro
    """
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    width_x = max(xs) - min(xs)
    width_y = max(ys) - min(ys)

    long_dim = max(width_x, width_y)
    short_dim = min(width_x, width_y)
    aspect_ratio = long_dim / short_dim if short_dim > 0 else float("inf")

    centroid = compute_centroid(points)

    if aspect_ratio < aspect_ratio_threshold:
        return [centroid]

    n_samples = max(2, int(long_dim // sample_spacing))
    sampled_points = []

    if width_x >= width_y:
        x_min, x_max = min(xs), max(xs)
        for i in range(n_samples + 1):
            t = i / n_samples
            x = x_min + t * (x_max - x_min)
            sampled_points.append((x, centroid[1]))
    else:
        y_min, y_max = min(ys), max(ys)
        for i in range(n_samples + 1):
            t = i / n_samples
            y = y_min + t * (y_max - y_min)
            sampled_points.append((centroid[0], y))

    return sampled_points

def voronoi_finite_polygons_2d(vor, radius=None):
    """Ricostruzione celle finite del Voronoi"""
    if vor.points.shape[1] != 2:
        raise ValueError("Richiede punti 2D")

    new_regions = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)
    if radius is None:
        # FIX: ndarray.ptp() è stato rimosso in NumPy >= 2.0.
        # Si usa la funzione np.ptp() al suo posto.
        radius = np.ptp(vor.points, axis=0).max() * 2

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
            t /= np.linalg.norm(t)
            n = np.array([-t[1], t[0]])

            midpoint = vor.points[[p1, p2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            far_point = vor.vertices[v2] + direction * radius

            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())

        vs = np.asarray([new_vertices[v] for v in new_region])
        c = vs.mean(axis=0)
        angles = np.arctan2(vs[:, 1] - c[1], vs[:, 0] - c[0])
        new_region = np.array(new_region)[np.argsort(angles)]

        new_regions.append(new_region.tolist())

    return new_regions, np.asarray(new_vertices)

def find_perimeters_auto(perimeters, min_gap_ratio=2.5):
    """Ricerca automatica dei perimetri di piano"""
    if len(perimeters) < 2:
        return perimeters

    handles = list(perimeters.keys())
    areas = np.array([abs(perimeters[h]["area"]) for h in handles])

    if np.any(areas <= 0):
        raise ValueError("Trovate aree nulle o negative tra i perimetri")

    log_areas = np.log(areas)
    order = np.argsort(log_areas)
    sorted_log_areas = log_areas[order]
    sorted_handles = [handles[i] for i in order]

    gaps = np.diff(sorted_log_areas)
    if len(gaps) == 0:
        return perimeters

    max_gap_idx = np.argmax(gaps)
    max_gap = gaps[max_gap_idx]

    other_gaps = np.delete(gaps, max_gap_idx)
    if len(other_gaps) > 0:
        reference = np.median(other_gaps) if np.median(other_gaps) > 0 else np.mean(other_gaps)
        if reference > 0 and max_gap < reference * min_gap_ratio:
            return perimeters

    split_index = max_gap_idx + 1
    floor_handles = sorted_handles[split_index:]
    floor_perimeters = {h: perimeters[h] for h in floor_handles}

    if not floor_perimeters:
        return perimeters

    return floor_perimeters

def assign_elements_to_floors(data, polylines, floor_perimeters):
    """Assegna elementi strutturali al perimetro di piano corretto"""
    floor_polygons = {h: Polygon(v["points"]) for h, v in floor_perimeters.items()}
    grouped = {h: {} for h in floor_perimeters}
    unassigned = []
    ambiguous = []

    for name, value in data.items():
        poly_points = polylines[value["polyline_handle"]]["points"]
        centroid = Point(compute_centroid(poly_points))

        matches = [h for h, fp in floor_polygons.items() if fp.contains(centroid)]

        if len(matches) == 1:
            grouped[matches[0]][name] = value
        elif len(matches) == 0:
            unassigned.append(name)
        else:
            ambiguous.append((name, matches))

    if unassigned:
        print(f"[ATTENZIONE] {len(unassigned)} elementi con baricentro fuori da ogni perimetro: {unassigned}")
    if ambiguous:
        print(f"[ATTENZIONE] {len(ambiguous)} elementi ricadono in più perimetri: {ambiguous}")

    return grouped

def compute_influence_areas(data, polylines, boundary_points):
    """Pipeline Voronoi per un singolo piano"""
    boundary_polygon = Polygon(boundary_points)

    element_names = []
    all_sample_points = []

    for name, value in data.items():
        poly_points = polylines[value["polyline_handle"]]["points"]
        sites = classify_and_sample(poly_points, value["sides"])
        for s in sites:
            element_names.append(name)
            all_sample_points.append(s)

    points_array = np.array(all_sample_points)
    vor = Voronoi(points_array)
    regions, vertices = voronoi_finite_polygons_2d(vor)

    site_polygons = []
    for region in regions:
        poly_pts = vertices[region]
        poly = Polygon(poly_pts)
        clipped = poly.intersection(boundary_polygon)
        site_polygons.append(clipped)

    influence_areas = {}
    for name in set(element_names):
        indices = [i for i, n in enumerate(element_names) if n == name]
        cells = [site_polygons[i] for i in indices]
        merged = unary_union(cells)
        influence_areas[name] = {
            "geometry": merged,
            "area": merged.area
        }

    return influence_areas

def compute_influence_areas_all_floors(data, polylines, perimeters):
    """Pipeline completa multi-piano"""
    floor_perimeters = find_perimeters_auto(perimeters)
    grouped_elements = assign_elements_to_floors(data, polylines, floor_perimeters)

    results = {}
    for floor_handle, floor_data in grouped_elements.items():
        if not floor_data:
            print(f"[INFO] Piano {floor_handle}: nessun elemento assegnato")
            continue
        boundary_points = floor_perimeters[floor_handle]["points"]
        try:
            results[floor_handle] = compute_influence_areas(floor_data, polylines, boundary_points)
        except Exception as e:
            # FIX: non far crashare l'intera pipeline se un piano fallisce;
            # si registra l'errore e si prosegue con gli altri piani.
            print(f"[ERRORE] Calcolo aree di influenza fallito per il piano {floor_handle}: {e}")

    return results

# ============================================================================
# LETTURA DEL FILE DXF
# ============================================================================

for entity in msp:
    if entity.dxftype() == "LWPOLYLINE":
        polylines[entity.dxf.handle] = {
            "points": [(float(p[0]), float(p[1])) for p in entity.get_points()],
            "closed": entity.closed,
            "layer": entity.dxf.layer   # <-- aggiunto
        }
    elif entity.dxftype() == "MTEXT":
        mtexts[entity.dxf.handle] = {
            "text": entity.plain_text().strip(),
            "insert": (float(entity.dxf.insert[0]), float(entity.dxf.insert[1]))
        }

# ============================================================================
# CREAZIONE DATI STRUTTURALI
# ============================================================================

for text_handle, tdata in mtexts.items():
    point = tdata["insert"]
    containing = []
    for poly_handle, pdata in polylines.items():
        if not pdata["closed"] or len(pdata["points"]) < 3:
            continue
        if point_in_polygon(point, pdata["points"]):
            containing.append(poly_handle)

    if not containing:
        continue

    # FIX: invece di prendere containing[0] (ordine arbitrario dipendente
    # dall'ordine delle entità nel DXF), si sceglie il poligono con area
    # minima, ovvero quello più "annidato" attorno al testo: è quello che
    # realmente rappresenta l'elemento strutturale, non il perimetro di piano.
    containing.sort(key=lambda h: polygon_area(polylines[h]["points"]))
    own_handle = containing[0]

    name = tdata["text"]
    if name in data:
        # FIX: etichette duplicate sovrascrivevano silenziosamente
        # l'elemento precedente. Ora viene segnalato.
        print(f"[ATTENZIONE] Etichetta duplicata '{name}': l'elemento precedente con questo nome verrà sovrascritto.")

    poly_points = polylines[own_handle]["points"]

    data[name] = {
        "polyline_handle": own_handle,
        "all_containing": containing,
        "sides": polygon_sides(poly_points),
        "area": polygon_area(poly_points)
    }

# ============================================================================
# IDENTIFICAZIONE PERIMETRI DI PIANO (per layer)
# ============================================================================

PERIMETER_LAYER = "0"  # <-- sostituisci con il nome vero

perimeters = {}
for handle, pdata in polylines.items():
    if pdata["layer"] != PERIMETER_LAYER:
        continue
    if pdata["closed"] and len(pdata["points"]) >= 3:
        perimeters[handle] = {
            "points": pdata["points"],
            "area": polygon_area(pdata["points"])
        }
print(perimeters)
# opzionale ma consigliato: verifica che gli elementi strutturali non siano
# per errore sullo stesso layer del perimetro
elements_on_perimeter_layer = [
    name for name, value in data.items()
    if polylines[value["polyline_handle"]]["layer"] == PERIMETER_LAYER
]
if elements_on_perimeter_layer:
    print(f"[ATTENZIONE] {len(elements_on_perimeter_layer)} elementi strutturali "
          f"si trovano sul layer perimetro '{PERIMETER_LAYER}': {elements_on_perimeter_layer}")
# ============================================================================
# CALCOLO AREE DI INFLUENZA
# ============================================================================

# FIX: 'results' viene sempre inizializzato, così il resto dello script
# (compreso l'export Excel) non va in NameError se data/perimeters sono vuoti
# o se il calcolo fallisce.
results = {}

if data and perimeters:
    try:
        results = compute_influence_areas_all_floors(data, polylines, perimeters)
    except Exception as e:
        print(f"[ERRORE] Calcolo aree di influenza fallito: {e}")

    print("\n" + "="*60)
    print("AREE DI INFLUENZA PER PIANO")
    print("="*60)

    for floor_handle, floor_results in results.items():
        print(f"\nPiano {floor_handle}:")
        for name, info in floor_results.items():
            print(f"  {name}: area = {info['area']:.2f} m²")
else:
    print("Nessun dato sufficiente per calcolare le aree di influenza")

# ============================================================================
# DISEGNO DELLE AREE DI INFLUENZA NEL DXF
# ============================================================================

def draw_influence_areas(doc, msp, results, layer_name="AREE_INFLUENZA"):
    if layer_name not in doc.layers:
        doc.layers.add(layer_name, color=3)  # verde, cambia se vuoi

    for floor_handle, floor_results in results.items():
        for name, info in floor_results.items():
            geometry = info["geometry"]

            # unary_union può restituire Polygon o MultiPolygon
            polygons = geometry.geoms if geometry.geom_type == "MultiPolygon" else [geometry]

            for poly in polygons:
                if poly.is_empty:
                    continue

                coords = list(poly.exterior.coords)
                msp.add_lwpolyline(
                    coords,
                    close=True,
                    dxfattribs={"layer": layer_name}
                )

                # etichetta con nome elemento e area al centroide della cella
                cx, cy = poly.centroid.x, poly.centroid.y
                msp.add_mtext(
                    f"{name}\n{info['area']:.2f} m2",
                    dxfattribs={"layer": layer_name, "char_height": 150}
                ).set_location(insert=(cx, cy))

if results:
    draw_influence_areas(doc, msp, results)

output_dxf_path = r"C:\Users\Amministratore\Desktop\VSCode\Disegno1_aree_influenza.dxf"
doc.saveas(output_dxf_path)






# ============================================================================
# ESPORTAZIONE JSON
# ============================================================================

filepath = r"C:\Users\Amministratore\Desktop\VSCode\data.JSON"
with open(filepath, "w") as f:
    json.dump(data, f, indent=2)

# ============================================================================
# CREAZIONE DATAFRAME ED ESPORTAZIONE EXCEL
# ============================================================================

def get_x_y_dimensions(sides):
    dim_x = 0.0
    dim_y = 0.0
    for side in sides:
        x1, y1 = side["start"]
        x2, y2 = side["end"]
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        if dx > dy:
            dim_x = max(dim_x, side["length"])
        else:
            dim_y = max(dim_y, side["length"])
    return dim_x, dim_y

rows = []
for name, value in data.items():
    dim_x, dim_y = get_x_y_dimensions(value["sides"])
    rows.append({
        "name": name,
        "x": dim_x,
        "y": dim_y,
        "Area": value["area"]
    })

dataframe = pd.DataFrame(rows, columns=["name", "x", "y", "Area"])

# FIX: la colonna Influence_Area viene sempre creata (anche se vuota/NaN),
# così la struttura del file di output è sempre coerente e prevedibile.
influence_areas_flat = {}
for floor_results in results.values():
    for name, info in floor_results.items():
        print(info["area"])
        influence_areas_flat[name] = info["area"]

dataframe["Influence_Area"] = dataframe["name"].map(influence_areas_flat)

missing = dataframe[dataframe["Influence_Area"].isna()]["name"].tolist()
if missing:
    print(f"[ATTENZIONE] {len(missing)} elementi senza area di influenza calcolata: {missing}")

excel_path = r"C:\Users\Amministratore\Desktop\VSCode\data.xlsx"
dataframe.to_excel(excel_path, index=False)

print("\n" + "="*60)
print("DATAFRAME FINALE:")
print("="*60)
print(dataframe)