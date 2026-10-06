"""
Versione corretta di buffer_overlapping.

Bug del codice originale:
1) `result` non veniva resettato ad ogni elemento -> in certi casi
   (0 iterazioni valide nel ciclo interno) restava il valore lasciato
   dall'elemento precedente, o dava NameError.
2) Il dizionario `true_buffer_polygons` veniva letto E modificato nello
   stesso doppio ciclo -> il risultato dipendeva dall'ordine di iterazione
   del dict (chi viene processato per primo "vince" la zona di overlap).

Fix: si congelano i buffer "puliti" (step 1) e le sovrapposizioni si
risolvono in un secondo passaggio SOLO su quella copia congelata, poi si
applicano tutte le modifiche in blocco alla fine. La zona di overlap fra
due buffer viene divisa esattamente a metà con la bisettrice perpendicolare
fra i due centroidi (un solo taglio per coppia, niente campionamento denso).
"""

import math
from collections import defaultdict
from shapely.geometry import LineString, Polygon, MultiPolygon, GeometryCollection
from shapely.ops import split, unary_union


def to_polygon(points):
    return Polygon(points)


def _polygonal_only(geom):
    """
    Estrae solo la parte con area (Polygon/MultiPolygon) da una geometria
    qualsiasi, scartando frammenti di dimensione inferiore (LineString,
    Point) che shapely produce quando due poligoni si intersecano non solo
    su un'area ma anche lungo un bordo o in un punto isolato. split()
    accetta solo Polygon/MultiPolygon: una GeometryCollection lo fa fallire
    anche se contiene un solo poligono "vero" in mezzo a scarti puntiformi.
    """
    if geom is None or geom.is_empty:
        return None
    if isinstance(geom, (Polygon, MultiPolygon)):
        return geom
    if isinstance(geom, GeometryCollection):
        polys = [g for g in geom.geoms if isinstance(g, (Polygon, MultiPolygon)) and not g.is_empty]
        if not polys:
            return None
        return unary_union(polys)
    return None


def _bisector_line(centroid_a, centroid_b, length=1e6):
    """Retta perpendicolare al segmento a-b, passante per il punto medio."""
    mx, my = (centroid_a.x + centroid_b.x) / 2, (centroid_a.y + centroid_b.y) / 2
    dx, dy = centroid_b.x - centroid_a.x, centroid_b.y - centroid_a.y
    norm = math.hypot(dx, dy)
    if norm == 0:
        return None  # centroidi coincidenti: caso degenere
    ux, uy = -dy / norm, dx / norm  # direzione perpendicolare, normalizzata
    p1 = (mx - ux * length, my - uy * length)
    p2 = (mx + ux * length, my + uy * length)
    return LineString([p1, p2])


def _split_overlap(overlap_poly, centroid_a, centroid_b):
    """
    Divide overlap_poly in due parti lungo la bisettrice fra i due centroidi.
    Ritorna (parte_di_a, parte_di_b); una delle due può essere None.
    """
    line = _bisector_line(centroid_a, centroid_b)
    if line is None:
        return overlap_poly, None

    pieces = split(overlap_poly, line)
    near_a, near_b = [], []
    for piece in pieces.geoms:
        rp = piece.representative_point()
        if rp.distance(centroid_a) <= rp.distance(centroid_b):
            near_a.append(piece)
        else:
            near_b.append(piece)

    part_a = unary_union(near_a) if near_a else None
    part_b = unary_union(near_b) if near_b else None
    return part_a, part_b


def buffer_overlapping(struct_polylines, struct_buffer_polygons):
    struct_poly = {el: to_polygon(v["points"]) for el, v in struct_polylines.items()}
    centroids = {el: p.centroid for el, p in struct_poly.items()}

    # --- STEP 1: da ogni buffer togliamo il footprint di TUTTI gli altri
    #     elementi strutturali (mai il proprio). Nessuna dipendenza
    #     dall'ordine: ogni elemento è indipendente dagli altri qui.
    step1 = {}
    for element, buffer_poly in struct_buffer_polygons.items():
        others = [p for e, p in struct_poly.items() if e != element]
        others_union = unary_union(others) if others else None
        if others_union is not None and not others_union.is_empty:
            cleaned = _polygonal_only(buffer_poly.difference(others_union))
            step1[element] = cleaned if cleaned is not None else buffer_poly
        else:
            step1[element] = buffer_poly

    # --- STEP 2: risolviamo le sovrapposizioni FRA buffer, lavorando solo
    #     sulla copia congelata step1 (mai mutata durante il calcolo).
    #     Ogni coppia viene considerata una sola volta.
    to_remove = defaultdict(list)
    to_add = defaultdict(list)

    elements = list(step1.keys())
    for i, a in enumerate(elements):
        for b in elements[i + 1:]:
            overlap = _polygonal_only(step1[a].intersection(step1[b]))
            if overlap is None or overlap.is_empty:
                continue

            part_a, part_b = _split_overlap(overlap, centroids[a], centroids[b])

            # a entrambi togliamo l'intera zona di sovrapposizione...
            to_remove[a].append(overlap)
            to_remove[b].append(overlap)
            # ...e poi restituiamo a ciascuno solo la propria metà
            if part_a is not None:
                to_add[a].append(part_a)
            if part_b is not None:
                to_add[b].append(part_b)

    # --- applichiamo tutte le modifiche in blocco, alla fine
    final = {}
    for element, buffer_poly in step1.items():
        if to_remove.get(element):
            buffer_poly = buffer_poly.difference(unary_union(to_remove[element]))
        if to_add.get(element):
            buffer_poly = unary_union([buffer_poly] + to_add[element])
        final[element] = buffer_poly

    return final