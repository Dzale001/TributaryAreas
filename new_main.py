import ezdxf
import math
import json
import pandas as pd
from plotting import plotting, init_plot, update_plot, show
from cutting import multi_slash, flatten_voronoi, flatten_single_level, to_polygon, unionized, fusion, point_in_polygon, polygon_in_polygon, segments_intersect, polygons_intersect, more_xy, split_rooms_by_orditura, multi_slash_anisotropic, multi_slash_weighted, buffer_overlapping, clip_region_to_boundaries

from collections import defaultdict


doc = ezdxf.readfile("Disegno1.dxf")
msp = doc.modelspace()

data =              {}
bound_polylines =   {}
struct_polylines =  {}
room_polylines =    {}
stairs_polylines =  {}
dir_polylines =     {}
other_polylines =   {}
mtexts =            {}

for entity in msp:
    if entity.dxftype() == "LWPOLYLINE" and entity.dxf.layer == "AREE":
        struct_polylines[entity.dxf.handle] = {
            "points": [(float(p[0]), float(p[1])) for p in entity.get_points()],
            "closed": entity.closed}
    elif entity.dxftype() == "LWPOLYLINE" and entity.dxf.layer == "0":
        bound_polylines[entity.dxf.handle] = {
            "points": [(float(p[0]), float(p[1])) for p in entity.get_points()],
            "closed": entity.closed}
    elif entity.dxftype() == "LWPOLYLINE" and entity.dxf.layer == "SCALE":
        stairs_polylines[entity.dxf.handle] = {
            "points": [(float(p[0]), float(p[1])) for p in entity.get_points()],
            "closed": entity.closed}
    elif entity.dxftype() == "LWPOLYLINE" and entity.dxf.layer == "STANZE":
        room_polylines[entity.dxf.handle] = {
            "points": [(float(p[0]), float(p[1])) for p in entity.get_points()],
            "closed": entity.closed}
    elif entity.dxftype() == "LWPOLYLINE" and entity.dxf.layer == "AGGETTI":
        other_polylines[entity.dxf.handle] = {
            "points": [(float(p[0]), float(p[1])) for p in entity.get_points()],
            "closed": entity.closed}
    elif entity.dxftype() == "LWPOLYLINE" and entity.dxf.layer == "ORDITURA":
        dir_polylines[entity.dxf.handle] = {
            "points": [(float(p[0]), float(p[1])) for p in entity.get_points()],
            "closed": entity.closed}
    elif entity.dxftype() == "MTEXT" and entity.dxf.layer == "AREE":
        mtexts[entity.dxf.handle] = {
            "text": entity.plain_text(),
            "insert": (float(entity.dxf.insert[0]), float(entity.dxf.insert[1]))
        }

sub_data = {}
for s_key, s_value in struct_polylines.items():
    for t_key, t_value in mtexts.items():
        if point_in_polygon(s_value["points"], t_value["insert"]): # SE IL TESTO STA DENTRO L'ELEMENTO STRUTTURALE
            sub_data[s_key] = [t_key, mtexts[t_key]["text"]]

for b_key, b_value in bound_polylines.items():
    i = 0
    temp = {}
    for s_key, s_value in struct_polylines.items():
        if polygon_in_polygon(b_value["points"], s_value["points"]): # SE L'ELEMENTO STRUTTURALE STA DENTRO LE LINEE PERIMETRALI
            temp[s_key] = (sub_data[s_key])
    data[b_key] = temp
    i += 1

# il dizionario è strutturato così: 
# {1: {"elementi affini a 1 ": [elem1, elem2 ...], orditura: orditura, tipo: tipo},
#  2: {"elementi affini a 2 ": [elem1, elem2 ...], orditura: orditura, tipo: tipo},
#  3: {"elementi affini a 3 ": [elem1, elem2 ...], orditura: orditura, tipo: tipo}}
rooms_data = {}
for r_key, r_value in room_polylines.items():
    sub_room_data = {}
    room_contains = []
    for s_key, s_values in struct_polylines.items():
        if polygons_intersect(r_value["points"], s_values["points"]): # Controlliamo quali poligoni intersecano la nostra stanza
            room_contains.append(s_key)
    sub_room_data["intersecano"] = room_contains
    for dir_key, dir_value in dir_polylines.items():
        if polygon_in_polygon(r_value["points"], dir_value["points"]): # Controlliamo le orditure
            orditura = more_xy(dir_value["points"])
    sub_room_data["orditura"] = orditura
    sub_room_data["tipo"] = "stanza"
    
    rooms_data[r_key] = sub_room_data

stairs_data = {}
for r_key, r_value in stairs_polylines.items():
    sub_stairs_data = {}
    stair_contains = []
    for s_key, s_values in struct_polylines.items():
        if polygons_intersect(r_value["points"], s_values["points"]):
            stair_contains.append(s_key)
    sub_stairs_data["intersecano"] = stair_contains
    for dir_key, dir_value in dir_polylines.items():
        if polygon_in_polygon(r_value["points"], dir_value["points"]):
            orditura = more_xy(dir_value["points"])
    sub_stairs_data["orditura"] = orditura
    sub_stairs_data["tipo"] = "scale"
    stairs_data[r_key] = sub_stairs_data

other_data = {}
for r_key, r_value in other_polylines.items():
    sub_other_data = {}
    other_contains = []
    for s_key, s_values in struct_polylines.items():
        if polygons_intersect(r_value["points"], s_values["points"]):
            other_contains.append(s_key)
    sub_stairs_data["intersecano"] = other_contains
    for dir_key, dir_value in dir_polylines.items():
        if polygon_in_polygon(r_value["points"], dir_value["points"]):
            orditura = more_xy(dir_value["points"])
    sub_other_data["orditura"] = orditura
    sub_other_data["tipo"] = "scale"
    other_data[r_key] = sub_other_data

total_rooms_polylines = room_polylines# | stairs_polylines | other_polylines
total_rooms_data = rooms_data# | stairs_data | other_data


#with open("temp.JSON", "w") as f:
    #json.dump(total_rooms_data, f, indent=2)
        
#DA CONTROLLARE SE CI SONO ELEMENTI O TESTI CHE NON SONO DENTRO LE POLILINEE PERIMETRALI

#with open("data.JSON", "w") as f:
    #json.dump(data, f, indent=2)


############# M A I N - L O O P #############
anisotropic = True

total_rooms_polylines, total_rooms_data = split_rooms_by_orditura(total_rooms_polylines, total_rooms_data, struct_polylines)
if anisotropic:
    voronoi_areas = multi_slash_anisotropic(total_rooms_polylines, total_rooms_data, struct_polylines, stretch_factor=2.25)
    #voronoi_areas = multi_slash_weighted(total_rooms_polylines, total_rooms_data, struct_polylines, weight_scale=2)
else:
    voronoi_areas = multi_slash(total_rooms_polylines, total_rooms_data, struct_polylines)

struct_buffer_polygons = {}
BUFFER = 30
for key, value in struct_polylines.items():
    struct_buffer_polygons[key] = to_polygon(struct_polylines[key]["points"]).buffer(BUFFER,join_style="mitre",  mitre_limit=100)


#fig1, ax1 = init_plot()
#update_plot(ax, struct_buffer_polygons.values())
truebuffer = buffer_overlapping(struct_polylines, struct_buffer_polygons)
#update_plot(ax1, truebuffer.values(), pause=1)

all_buffers = unionized(list(truebuffer.values()))

struct_regions = {}
for element in struct_polylines:
    stuff = []
    struct_poly = to_polygon(struct_polylines[element]["points"]) # -> qui potrei aggiungere l'area con offset
    stuff.append(struct_poly)
    stuff.append(truebuffer[element])
    other_buffers = all_buffers.difference(truebuffer[element])
    for room, cell_by_element in voronoi_areas.items():
        for struct, cell in cell_by_element.items():
            if struct == element:
                cell = cell.difference(other_buffers)
                stuff.append(cell)
    struct_regions[element] = stuff

#struct regions contiene l'elemento strutturale e tutte le celle voronoi ad esso associate
region_polygons = {}
# in pratica, arrivano gli elementi strutturali e le celle separate e unionized le unisce, poi fusion trasforma in multipoligoni in poligoni con meno intersezioni possibile
# Quindi se voglio aggiungere o togliere qualcosa devo farlo qui?
for struct, cells in struct_regions.items():
    region_polygons[struct] = unionized(cells) ###################################################

#update_plot(ax1, region_polygons.values(), pause=1)

for key, value in region_polygons.items():    
    region_polygons[key] = fusion(value)


region_polygons = clip_region_to_boundaries(region_polygons, bound_polylines, struct_polylines)

#update_plot(ax1, region_polygons.values())
#show()

#voronoi_flat = flatten_voronoi(voronoi_areas)


for boundary, polygon in bound_polylines.items():
    polygon = to_polygon(polygon["points"])

voronoi_flat = flatten_single_level(region_polygons)


print(region_polygons)

plotting(bound_polylines=bound_polylines, struct_polylines=struct_polylines, mtexts=mtexts, voronoi=voronoi_flat)


## L' IDEA è QUELLA DI AGGIUNGERE UN OFFSET A OGNI AREA PRIMA DI FARE QUALNUNQUE CALCOLO E POI FARE QUALUNQUE CALCOLO, MA C
# O FORSE è MEGLIO, QUANDO AGGIUNGIAMO L'AREA A TUTTE LE REGIONI, AGGIUNGERE QUELLA FINTA CON L'OFFSET? BOH

### Aggiungiamo alla lista di aree da unire un area definita così:
# Ci calcoliamo inizialmente un vettore che contiene tutte gli elementi strutturali con buffer + 50 ✓
# Nel loop cerchiamo questo elemento e lo modifichiamo come segue:
# A questo buffer togliamo ogni intersezione con altri elementi strutturali
# Prendiamo l'intersezione di questo buffer con tutti li altri buffer
# Da questa infersezione togliamo l'elemento strutturale di appartenenza e rimaniamo con l'intersezione pura buffer - buffer
# Togliamo questa intersezione pura dal nostro buffer, che andiamo a inserire nelle aree da unire